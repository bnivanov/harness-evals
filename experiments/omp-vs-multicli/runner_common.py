#!/usr/bin/env python3
"""Process isolation, trace capture, and provenance helpers for both arms."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

from experiment_config import PROJECT_ROOT, SANDBOX_EXEC

NETWORK_EXECUTABLES = (
    "/usr/bin/curl",
    "/usr/bin/nc",
    "/usr/bin/ssh",
    "/usr/bin/scp",
    "/usr/bin/rsync",
    "/opt/homebrew/bin/curl",
    "/opt/homebrew/bin/wget",
    "/opt/homebrew/bin/nc",
    "/opt/homebrew/bin/ssh",
    "/opt/homebrew/bin/scp",
    "/opt/homebrew/bin/rsync",
)

TRACE_VIOLATION_PATTERNS = (
    ("ORACLE_PATH", re.compile(r"(?:file://)?[^\s\"']*?/benchmarks/aider-python/(?:oracle|tasks)/", re.I)),
    ("NETWORK_COMMAND", re.compile(r"(?:^|[;&|\s])(?:curl|wget|ssh|scp|rsync)\s|(?:^|[;&|\s])nc\s+-[a-zA-Z0-9]|(?:^|[;&|\s])nc\s+[0-9a-zA-Z.-]+\s+\d+", re.I)),
    ("GIT_NETWORK", re.compile(r"\bgit\s+(?:clone|fetch|pull|remote\s+add)\b", re.I)),
    ("PACKAGE_FETCH", re.compile(r"\b(?:pip(?:3)?\s+install|python3?\s+-m\s+pip\s+install|npm\s+install|gem\s+install)\b", re.I)),
    ("RAW_NETWORK_CODE", re.compile(r"(?:import\s+(?:urllib(?:\.\w+)*|requests|httpx|socket)|from\s+(?:urllib(?:\.\w+)*|requests|httpx|socket)\s+import|(?:requests|httpx)\.(?:get|post|put|delete|patch|request)|socket\.(?:socket|create_connection)|require\s*\(\s*['\"](?:node:)?(?:https?|net)['\"]\)|fetch\s*\(\s*['\"]https?:)", re.I)),
)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seatbelt_profile(workspace: str) -> str:
    """Deny access to the source tree and execution of common network clients."""

    root = os.path.realpath(PROJECT_ROOT).replace('"', '\\"')
    workspace_real = os.path.realpath(workspace).replace('"', '\\"')
    deny_exec = "\n".join(
        f'  (deny process-exec (literal "{path}"))'
        for path in NETWORK_EXECUTABLES
        if os.path.exists(path)
    )
    return (
        "(version 1)\n"
        "(allow default)\n"
        f'(deny file-read* (subpath "{root}"))\n'
        f'(deny file-write* (subpath "{root}"))\n'
        f'(allow file-read* file-write* (subpath "{workspace_real}"))\n'
        f"{deny_exec}\n"
    )


def sandbox_command(command: list[str], workspace: str) -> list[str]:
    if not os.path.isfile(SANDBOX_EXEC):
        raise RuntimeError(f"Required sandbox executable is missing: {SANDBOX_EXEC}")
    return [SANDBOX_EXEC, "-p", seatbelt_profile(workspace), *command]


def write_trace(path: str, content: str) -> dict:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return {"path": path, "sha256": sha256_file(path), "bytes": os.path.getsize(path)}


def run_captured_process(
    command: list[str],
    cwd: str,
    timeout_seconds: float,
    stdout_path: str,
    stderr_path: str,
    env: dict[str, str] | None = None,
) -> dict:
    """Run a stage in its own process group and preserve complete/partial traces."""

    os.makedirs(os.path.dirname(stdout_path), exist_ok=True)
    os.makedirs(os.path.dirname(stderr_path), exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with open(stdout_path, "w", encoding="utf-8") as stdout_handle, open(
        stderr_path, "w", encoding="utf-8"
    ) as stderr_handle:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            stdin=subprocess.DEVNULL,
            text=True,
            start_new_session=True,
        )

        try:
            proc.wait(timeout=max(0.1, timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        stdout_handle.flush()
        stderr_handle.flush()
        os.fsync(stdout_handle.fileno())
        os.fsync(stderr_handle.fileno())

    duration = round(time.monotonic() - started, 2)
    with open(stdout_path, encoding="utf-8") as handle:
        stdout = handle.read()
    with open(stderr_path, encoding="utf-8") as handle:
        stderr = handle.read()
    stdout_meta = {"path": stdout_path, "sha256": sha256_file(stdout_path), "bytes": os.path.getsize(stdout_path)}
    stderr_meta = {"path": stderr_path, "sha256": sha256_file(stderr_path), "bytes": os.path.getsize(stderr_path)}
    return {
        "returncode": -1 if timed_out else proc.returncode,
        "duration": duration,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_trace": stdout_meta,
        "stderr_trace": stderr_meta,
    }


def trace_violations(*texts: str) -> list[dict]:
    joined = "\n".join(texts)
    violations = []
    for code, pattern in TRACE_VIOLATION_PATTERNS:
        match = pattern.search(joined)
        if match:
            violations.append({"code": code, "evidence": match.group(0)[:300]})
    return violations


def prepare_isolated_omp_agent_dir(runtime_dir: str) -> str:
    """Create an OMP profile containing auth/model metadata but no memory, skills, or history."""

    source = os.environ.get("PI_CODING_AGENT_DIR") or os.path.expanduser("~/.omp/agent")
    target = os.path.join(runtime_dir, "omp-agent")
    os.makedirs(target, mode=0o700, exist_ok=False)
    for name in ("auth.json", "models.yml", "secret-placeholder.key"):
        src = os.path.join(source, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(target, name))
    auth = os.path.join(target, "auth.json")
    if not os.path.isfile(auth):
        raise RuntimeError(f"OMP auth.json not found in source profile: {source}")
    os.chmod(auth, 0o600)
    return target
def prepare_isolated_grok_home(runtime_dir: str) -> str:
    """Copy only Grok authentication/model metadata into a clean HOME."""

    home = os.path.join(runtime_dir, "grok-home")
    target = os.path.join(home, ".grok")
    os.makedirs(target, mode=0o700, exist_ok=False)
    source = os.path.expanduser("~/.grok")
    for name in ("auth.json", "agent_id", "models_cache.json", "version.json"):
        src = os.path.join(source, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(target, name))
    if not os.path.isfile(os.path.join(target, "auth.json")):
        raise RuntimeError(f"Grok auth.json not found: {source}")
    os.chmod(os.path.join(target, "auth.json"), 0o600)
    return home


def prepare_isolated_codex_home(runtime_dir: str) -> str:
    """Copy only Codex authentication/model metadata into a clean CODEX_HOME."""

    target = os.path.join(runtime_dir, "codex-home")
    os.makedirs(target, mode=0o700, exist_ok=False)
    source = os.path.expanduser("~/.codex")
    for name in ("auth.json", "models_cache.json", "installation_id"):
        src = os.path.join(source, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(target, name))
    if not os.path.isfile(os.path.join(target, "auth.json")):
        raise RuntimeError(f"Codex auth.json not found: {source}")
    os.chmod(os.path.join(target, "auth.json"), 0o600)
    return target


def prepare_isolated_agy_home(runtime_dir: str) -> str:
    """Verify Antigravity auth exists; return the real HOME (machine-bound auth)."""
    source = os.path.expanduser("~/.gemini")
    if not os.path.isfile(os.path.join(source, "oauth_creds.json")):
        raise RuntimeError(f"Antigravity oauth_creds.json not found: {source}")
    os.makedirs(runtime_dir, exist_ok=True)
    return os.path.expanduser("~")


def read_guard_events(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    events = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"code": "MALFORMED_GUARD_LOG", "raw": line.rstrip()})
    return events


def copy_runtime_file(source: str, runtime_dir: str) -> str:
    os.makedirs(runtime_dir, exist_ok=True)
    target = os.path.join(runtime_dir, os.path.basename(source))
    shutil.copy2(source, target)
    return target
