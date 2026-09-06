#!/usr/bin/env python3
"""Fail-closed, non-model preflight and immutable run-manifest generator."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from experiment_config import (  # noqa: E402
    AGY_BIN,
    BENCHMARK_DIR,
    BINARY_PINS,
    CODEX_BIN,
    EXPECTED_ORACLE_TEST_CASES,
    EXPECTED_TASK_COUNT,
    GROK_BIN,
    LEGACY_PILOT_RESULTS_DIR,
    MODEL_PINS,
    PROJECT_ROOT,
    RUNS_DIR,
)
from runner_common import (  # noqa: E402
    prepare_isolated_agy_home,
    prepare_isolated_codex_home,
    prepare_isolated_grok_home,
    prepare_isolated_omp_agent_dir,
    sandbox_command,
    sha256_file,
)

FROZEN_SOURCE_FILES = (
    "PROTOCOL.md",
    "ANTI_CHEATING.md",
    "config_overlay.yml",
    "experiment_config.py",
    "runner_common.py",
    "run_task.py",
    "run_matrix.py",
    "preflight.py",
    "smoke_test_parity.py",
    "runners/arm_a_omp.py",
    "runners/arm_b_multicli.py",
    "verifier/oracle_verifier.py",
    "analysis/calculate_stats.py",
    "security/benchmark_guard.ts",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_checked(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=120, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout={result.stdout[-2000:]}\nstderr={result.stderr[-2000:]}"
        )
    return result


def hash_tree(root: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    for current, directories, files in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in {"__pycache__", ".git"})
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(current, name)
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            digest.update(relative.encode())
            digest.update(b"\0")
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
    return digest.hexdigest()


def verify_binary_pins() -> dict:
    evidence = {}
    for name, pin in BINARY_PINS.items():
        path = pin["path"]
        if not os.path.isfile(path) or not os.access(path, os.X_OK):
            raise RuntimeError(f"Pinned binary missing/not executable: {name} {path}")
        output = run_checked([path, *pin["version_args"]]).stdout.strip()
        if not output:
            output = run_checked([path, *pin["version_args"]]).stderr.strip()
        first_line = output.splitlines()[0] if output else ""
        if first_line != pin["version"]:
            raise RuntimeError(f"{name} version drift: expected {pin['version']!r}, got {first_line!r}")
        evidence[name] = {
            "path": path,
            "version": first_line,
            "sha256": sha256_file(os.path.realpath(path)),
        }
    return evidence


def verify_model_catalogs(runtime_dir: str) -> dict:
    grok_home = prepare_isolated_grok_home(runtime_dir)
    agy_home = prepare_isolated_agy_home(runtime_dir)
    codex_home = prepare_isolated_codex_home(runtime_dir)
    grok_env = os.environ.copy()
    grok_env["HOME"] = grok_home
    grok_output = run_checked([GROK_BIN, "models"], env=grok_env).stdout
    expected_grok = MODEL_PINS["planner"]["arm_b"]
    if expected_grok not in grok_output:
        raise RuntimeError(f"Pinned Grok model unavailable: {expected_grok}")

    # AGY auth is machine-bound (proven: full-profile HOME copy still fails
    # sign-in); catalog check runs with the real HOME like the pilot did.
    agy_output = run_checked([AGY_BIN, "models"]).stdout
    expected_agy = MODEL_PINS["reviewer"]["arm_b"]
    if expected_agy not in agy_output:
        raise RuntimeError(f"Pinned AGY model unavailable: {expected_agy}")


    codex_env = os.environ.copy()
    codex_env["CODEX_HOME"] = codex_home
    status = run_checked([CODEX_BIN, "login", "status"], env=codex_env)
    codex_login = (status.stdout + status.stderr).strip()
    return {
        "grok": expected_grok,
        "agy": expected_agy,
        "codex_login": codex_login,
    }


def verify_manifest_and_oracles() -> dict:
    manifest_path = os.path.join(BENCHMARK_DIR, "manifest.json")
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    task_ids = [item.get("task_id") for item in manifest]
    if len(manifest) != EXPECTED_TASK_COUNT or len(set(task_ids)) != EXPECTED_TASK_COUNT:
        raise RuntimeError(f"Manifest must contain {EXPECTED_TASK_COUNT} unique tasks")

    total_cases = 0
    per_task = {}
    for item in manifest:
        task_dir = os.path.join(BENCHMARK_DIR, "tasks", item["task_id"])
        required = (
            os.path.join(task_dir, item["impl_file"]),
            os.path.join(task_dir, item["public_test_file"]),
            os.path.join(task_dir, "README.md"),
            os.path.join(BENCHMARK_DIR, "oracle", "solutions", item["impl_file"]),
            os.path.join(BENCHMARK_DIR, "oracle", "tests", item["test_file"]),
        )
        missing = [path for path in required if not os.path.isfile(path)]
        if missing:
            raise RuntimeError(f"Missing files for {item['task_id']}: {missing}")
        with tempfile.TemporaryDirectory() as workspace:
            shutil.copy2(required[3], os.path.join(workspace, item["impl_file"]))
            shutil.copy2(required[4], os.path.join(workspace, item["test_file"]))
            result = run_checked(
                [sys.executable, "-m", "unittest", "-v", item["test_file"]],
                cwd=workspace,
            )
            output = result.stdout + result.stderr
            import re

            match = re.search(r"Ran (\d+) tests?", output)
            if not match or "OK" not in output:
                raise RuntimeError(f"Oracle suite did not produce a clean result: {item['task_id']}")
            count = int(match.group(1))
            total_cases += count
            per_task[item["task_id"]] = count
    if total_cases != EXPECTED_ORACLE_TEST_CASES:
        raise RuntimeError(
            f"Oracle test-count drift: expected {EXPECTED_ORACLE_TEST_CASES}, got {total_cases}"
        )
    return {"task_count": len(manifest), "test_cases": total_cases, "per_task": per_task}


def verify_seatbelt() -> dict:
    with tempfile.TemporaryDirectory(prefix="harness_seatbelt_check_") as workspace:
        local = os.path.join(workspace, "allowed.txt")
        with open(local, "w", encoding="utf-8") as handle:
            handle.write("allowed")
        allowed = subprocess.run(
            sandbox_command(["/bin/cat", local], workspace), capture_output=True, text=True, timeout=10
        )
        denied = subprocess.run(
            sandbox_command(["/bin/cat", os.path.join(BENCHMARK_DIR, "manifest.json")], workspace),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if allowed.returncode != 0 or allowed.stdout != "allowed":
            raise RuntimeError(f"Seatbelt denied workspace access: {allowed.stderr}")
        if denied.returncode == 0 or "Operation not permitted" not in denied.stderr:
            raise RuntimeError("Seatbelt did not deny benchmark source-tree access")
    return {"workspace_read": "allowed", "benchmark_source_read": "denied"}


def source_hashes() -> dict:
    hashes = {}
    for relative in FROZEN_SOURCE_FILES:
        path = os.path.join(BASE_DIR, relative)
        if not os.path.isfile(path):
            raise RuntimeError(f"Frozen source missing: {relative}")
        hashes[relative] = sha256_file(path)
    return hashes


def preflight(run_id: str, prepare: bool = False) -> dict:
    if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in run_id):
        raise ValueError("run_id may contain only letters, digits, hyphen, and underscore")
    run_dir = os.path.join(RUNS_DIR, run_id)
    manifest_path = os.path.join(run_dir, "run_manifest.json")
    results_dir = os.path.join(run_dir, "results")
    if os.path.exists(manifest_path):
        raise FileExistsError(f"Run is already frozen and immutable: {manifest_path}")
    if os.path.isdir(results_dir) and os.listdir(results_dir):
        raise RuntimeError(f"Run results directory is not empty: {results_dir}")

    with tempfile.TemporaryDirectory(prefix="harness_preflight_") as runtime_dir:
        omp_dir = prepare_isolated_omp_agent_dir(runtime_dir)
        checks = {
            "binaries": verify_binary_pins(),
            "model_catalogs": verify_model_catalogs(runtime_dir),
            "oracle": verify_manifest_and_oracles(),
            "seatbelt": verify_seatbelt(),
            "isolated_omp_profile": {
                "auth_present": os.path.isfile(os.path.join(omp_dir, "auth.json")),
                "skills_present": os.path.exists(os.path.join(omp_dir, "skills")),
                "history_present": os.path.exists(os.path.join(omp_dir, "history.db")),
            },
        }
    if checks["isolated_omp_profile"]["skills_present"] or checks["isolated_omp_profile"]["history_present"]:
        raise RuntimeError("Isolated OMP profile unexpectedly contains skills/history")

    payload = {
        "schema_version": 2,
        "status": "ready",
        "run_id": run_id,
        "created_at": utc_now(),
        "project_root": PROJECT_ROOT,
        "results_dir": results_dir,
        "legacy_pilot_results": {
            "path": LEGACY_PILOT_RESULTS_DIR,
            "included": False,
            "reason": "Exploratory pilot failed final protocol audit; confirmatory run starts clean.",
        },
        "binary_pins": checks["binaries"],
        "model_pins": MODEL_PINS,
        "source_hashes": source_hashes(),
        "benchmark_sha256": hash_tree(BENCHMARK_DIR),
        "checks": checks,
    }
    if prepare:
        os.makedirs(run_dir, exist_ok=False)
        os.makedirs(results_dir)
        os.makedirs(os.path.join(run_dir, "traces"))
        with open(manifest_path, "x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        payload["manifest_path"] = manifest_path
        payload["manifest_sha256"] = sha256_file(manifest_path)
    return payload

def validate_frozen_manifest(manifest_path: str) -> dict:
    """Re-run non-model gates and reject any drift after a run was frozen."""

    with open(manifest_path, encoding="utf-8") as handle:
        frozen = json.load(handle)
    if frozen.get("status") != "ready" or frozen.get("schema_version") != 2:
        raise RuntimeError(f"Invalid frozen run manifest: {manifest_path}")
    if frozen.get("source_hashes") != source_hashes():
        raise RuntimeError("Frozen experiment source changed after preflight")
    if frozen.get("benchmark_sha256") != hash_tree(BENCHMARK_DIR):
        raise RuntimeError("Frozen benchmark changed after preflight")
    current_binaries = verify_binary_pins()
    if frozen.get("binary_pins") != current_binaries:
        raise RuntimeError("Pinned binary path/version/hash changed after preflight")
    with tempfile.TemporaryDirectory(prefix="harness_revalidate_") as runtime_dir:
        verify_model_catalogs(runtime_dir)
    verify_seatbelt()
    results_dir = frozen.get("results_dir")
    if not results_dir or os.path.realpath(results_dir) != os.path.realpath(
        os.path.join(os.path.dirname(manifest_path), "results")
    ):
        raise RuntimeError("Frozen results_dir is invalid")
    return frozen
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run non-model benchmark preflight")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--prepare", action="store_true", help="Freeze an immutable run manifest")
    arguments = parser.parse_args()
    print(json.dumps(preflight(arguments.run_id, prepare=arguments.prepare), indent=2, sort_keys=True))
