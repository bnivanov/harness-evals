#!/usr/bin/env python3
"""
Oracle Verifier for Aider-Python Benchmark Tasks.
Runs in an isolated temporary directory against quarantined oracle tests.
Enforces anti-tamper constraints (no test modifications, no extra files).
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import re

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../benchmarks/aider-python"))

ALLOWED_HANDOFFS = frozenset({"01_PLAN.md", "02_REVIEW.md"})
PROTECTED_FILES = frozenset({"README.md", "public_test.py"})


def _normalize_repo_path(path: str) -> str:
    norm = path.replace("\\", "/").strip()
    while norm.startswith("./"):
        norm = norm[2:]
    return norm


def _unquote_git_path(path: str) -> str:
    path = path.strip()
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        return bytes(path[1:-1], "utf-8").decode("unicode_escape")
    return path


def _run_git(args, cwd: str):
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"git {' '.join(args)} failed: {exc}"
    if res.returncode != 0:
        detail = (res.stderr or res.stdout or "unknown git error").strip()
        return None, f"git {' '.join(args)} failed: {detail}"
    return res.stdout, None


def _nul_split_paths(blob: str):
    return [_normalize_repo_path(p) for p in blob.split("\0") if p.strip()]


def _collect_porcelain_paths(stdout: str):
    paths = []
    for raw in stdout.splitlines():
        if not raw:
            continue
        if len(raw) < 4 or raw[2] != " ":
            return None, f"malformed git status line: {raw!r}"
        xy = raw[:2]
        rest = raw[3:]
        rename_or_copy = (xy[0] in "RC") or (xy[1] in "RC")
        if rename_or_copy and " -> " in rest:
            orig, dest = rest.split(" -> ", 1)
            paths.append(_normalize_repo_path(_unquote_git_path(orig)))
            paths.append(_normalize_repo_path(_unquote_git_path(dest)))
        else:
            paths.append(_normalize_repo_path(_unquote_git_path(rest)))
    return paths, None


def _is_permitted_change(path: str, impl_file: str) -> bool:
    norm = _normalize_repo_path(path)
    if not norm:
        return False
    if norm == _normalize_repo_path(impl_file):
        return True
    if norm in ALLOWED_HANDOFFS:
        return True
    parts = [part for part in norm.split("/") if part]
    return "__pycache__" in parts


def _tamper_reason_for(path: str) -> str:
    norm = _normalize_repo_path(path)
    base = norm.split("/")[-1] if norm else path
    if norm in PROTECTED_FILES or base in PROTECTED_FILES:
        return f"Illegal modification of non-implementation file: {path}"
    return f"Illegal extra source/config/test file: {path}"


def inspect_workspace_changes(candidate_dir: str):
    """
    Inspect staged/unstaged tracked changes and untracked files versus HEAD.

    Returns (paths, error). error is set when inspection must fail closed.
    """
    _, err = _run_git(["rev-parse", "--verify", "HEAD"], candidate_dir)
    if err:
        return None, err

    status_out, err = _run_git(["status", "--porcelain=v1", "-uall"], candidate_dir)
    if err:
        return None, err
    porcelain_paths, parse_err = _collect_porcelain_paths(status_out)
    if parse_err:
        return None, parse_err

    tracked_out, err = _run_git(["diff", "--name-only", "-z", "HEAD"], candidate_dir)
    if err:
        return None, err
    staged_out, err = _run_git(["diff", "--name-only", "--cached", "-z", "HEAD"], candidate_dir)
    if err:
        return None, err
    untracked_out, err = _run_git(["ls-files", "--others", "-z"], candidate_dir)
    if err:
        return None, err

    changed = set(porcelain_paths)
    changed.update(_nul_split_paths(tracked_out))
    changed.update(_nul_split_paths(staged_out))
    changed.update(_nul_split_paths(untracked_out))
    return sorted(changed), None


def _anti_tamper_failure(task_id: str, reason: str) -> dict:
    return {
        "task_id": task_id,
        "passed": False,
        "tampered": True,
        "tamper_reason": reason,
        "ratio": 0.0,
        "passed_tests": 0,
        "total_tests": 0,
    }


def verify_task(task_id: str, candidate_dir: str, *, testing_allow_missing_git: bool = False) -> dict:
    manifest_path = os.path.join(BENCHMARK_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        return {"error": f"Manifest not found at {manifest_path}", "passed": False}

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    task_meta = next((item for item in manifest if item["task_id"] == task_id), None)
    if not task_meta:
        return {"error": f"Task {task_id} not found in manifest", "passed": False}

    impl_file = task_meta["impl_file"]
    test_file = task_meta["test_file"]

    candidate_impl = os.path.join(candidate_dir, impl_file)
    if not os.path.exists(candidate_impl):
        return {
            "task_id": task_id,
            "error": f"Candidate implementation file {impl_file} does not exist",
            "passed": False,
            "ratio": 0.0,
            "passed_tests": 0,
            "total_tests": 0
        }

    # Anti-tamper: one-commit workspace, uncommitted changes versus HEAD.
    changed_files, inspect_err = inspect_workspace_changes(candidate_dir)
    if inspect_err:
        if testing_allow_missing_git:
            changed_files = []
        else:
            return _anti_tamper_failure(
                task_id,
                f"Anti-tamper git inspection failed closed: {inspect_err}",
            )

    for cf in changed_files:
        if not _is_permitted_change(cf, impl_file):
            return _anti_tamper_failure(task_id, _tamper_reason_for(cf))

    oracle_test = os.path.join(BENCHMARK_DIR, "oracle", "tests", test_file)
    if not os.path.exists(oracle_test):
        return {"error": f"Oracle test file {test_file} not found", "passed": False}

    # Run verification in an isolated temporary sandbox
    with tempfile.TemporaryDirectory() as td:
        shutil.copy2(candidate_impl, os.path.join(td, impl_file))
        shutil.copy2(oracle_test, os.path.join(td, test_file))

        proc = subprocess.run(
            ["python3", "-m", "unittest", "-v", test_file],
            cwd=td,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = proc.stderr + "\n" + proc.stdout

        # Parse test results: "Ran X tests in Ys"
        ran_match = re.search(r"Ran (\d+) tests?", output)
        total_tests = int(ran_match.group(1)) if ran_match else 0

        if proc.returncode == 0 and "OK" in output:
            passed_tests = total_tests
            failed_tests = 0
            errors = 0
            ratio = 1.0
            binary_passed = True
        else:
            # Count failures and errors
            fails_match = re.search(r"FAILED \((?:failures=(\d+))?,?\s*(?:errors=(\d+))?\)", output)
            failures = int(fails_match.group(1)) if (fails_match and fails_match.group(1)) else 0
            errors = int(fails_match.group(2)) if (fails_match and fails_match.group(2)) else 0

            failed_tests = failures + errors
            passed_tests = max(0, total_tests - failed_tests)
            ratio = round(passed_tests / total_tests, 4) if total_tests > 0 else 0.0
            binary_passed = (ratio == 1.0 and total_tests > 0)

        return {
            "task_id": task_id,
            "passed": binary_passed,
            "ratio": ratio,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": total_tests,
            "returncode": proc.returncode,
            "raw_output": output[-500:]  # tail
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: oracle_verifier.py <task_id> <candidate_dir>")
        sys.exit(1)

    res = verify_task(sys.argv[1], sys.argv[2])
    print(json.dumps(res, indent=2))
