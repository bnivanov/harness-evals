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
import tempfile
from pathlib import Path

from experiment_config import PROJECT_ROOT, SANDBOX_EXEC

NETWORK_EXECUTABLES = (
    "/usr/bin/curl",
    "/usr/bin/nc",
    "/usr/bin/ncat",
    "/usr/bin/netcat",
    "/usr/bin/socat",
    "/usr/bin/telnet",
    "/usr/bin/ssh",
    "/usr/bin/scp",
    "/usr/bin/rsync",
    "/opt/homebrew/bin/curl",
    "/opt/homebrew/bin/wget",
    "/opt/homebrew/bin/nc",
    "/opt/homebrew/bin/ncat",
    "/opt/homebrew/bin/netcat",
    "/opt/homebrew/bin/socat",
    "/opt/homebrew/bin/telnet",
    "/opt/homebrew/bin/ssh",
    "/opt/homebrew/bin/scp",
    "/opt/homebrew/bin/rsync",
)

TRACE_VIOLATION_PATTERNS = (
    # Literal-anchored: a lazy `[^\s"']*?` prefix made this quadratic on
    # multi-hundred-KB traces (~2.4 s/MB) without widening the match set.
    ("ORACLE_PATH", re.compile(r"/benchmarks/aider-python/(?:oracle|tasks)/", re.I)),
    ("NETWORK_COMMAND", re.compile(
        r"(?:^|[;&|(`$\s{])(?:curl|wget|ssh|scp|rsync|ncat|netcat|socat|telnet)\b|"
        r"(?:^|[;&|(`$\s{])nc\s+-[a-zA-Z0-9]|"
        r"(?:^|[;&|(`$\s{])nc\s+[0-9a-zA-Z.-]+\s+\d+",
        re.I
    )),
    ("GIT_NETWORK", re.compile(r"\bgit\s+(?:clone|fetch|pull|remote\s+add)\b", re.I)),
    ("PACKAGE_FETCH", re.compile(r"\b(?:pip(?:3)?\s+install|python3?\s+-m\s+pip\s+install|npm\s+install|gem\s+install)\b", re.I)),
    ("RAW_NETWORK_CODE", re.compile(r"(?:import\s+(?:urllib(?:\.\w+)*|requests|httpx|socket)|from\s+(?:urllib(?:\.\w+)*|requests|httpx|socket)\s+import|(?:requests|httpx)\.(?:get|post|put|delete|patch|request)|socket\.(?:socket|create_connection)|require\s*\(\s*['\"](?:node:)?(?:https?|net)['\"]\)|fetch\s*\(\s*['\"]https?:)", re.I)),
)

# Amendment A (post-010, Opus C2): post-hoc temp-root write detection for Arm B.
# The in-process benchmark guard fail-closes Arm A; vendor CLIs in Arm B run at
# OS level, so an identical write attempt must carry the same disposition
# (violation -> pair dropped). Matches shell redirections, write-verb commands
# with a temp-root operand, and quoted temp-root paths after write verbs or a
# JSON "path" key. Deliberately NOT anchored on /var/folders: pilot workspaces
# and scratch dirs legitimately live there. MUST run on raw traces BEFORE
# scrub_workstation_paths (which rewrites /private/var/folders -> $TMPDIR).
TEMP_ROOT_WRITE_PATTERN = re.compile(
    r"(?:^|[;&|`$(){}\s])(?:echo|printf|cat|tee|touch|mkdir|rmdir|cp|mv|ln|rm|cd|python3?|perl|ruby|node)\b[^;&|`$\n]*?/(?:private/)?tmp(?:/|$)"
    r"|>{1,2}\s*/(?:private/)?tmp/"
    r"|(?:\bopen|\bwrite|\bsave|\bcreate|\"path\"\s*:)\s*\(?\s*['\"]/(?:private/)?tmp/",
    re.I,
)


def temp_root_write_violations(stdout: str, stderr: str) -> list[dict]:
    """Return one TEMP_ROOT_WRITE violation per temp-root write attempt."""
    hits: list[dict] = []
    for text in (stdout or "", stderr or ""):
        for match in TEMP_ROOT_WRITE_PATTERN.finditer(text):
            hits.append({"code": "TEMP_ROOT_WRITE", "match": match.group(0)[:120]})
    return hits


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# C8 ordering rule: temp-root detection (above) consumes raw traces at stage
# time. This scrub runs only at report time and would mask that evidence.
def scrub_workstation_paths(obj: Any) -> Any:
    home = os.path.expanduser("~")
    tmp = tempfile.gettempdir()
    if isinstance(obj, str):
        res = obj.replace(home, "$HOME")
        if tmp and tmp in res:
            res = res.replace(tmp, "$TMPDIR")
        res = res.replace("/private/var/folders", "$TMPDIR")
        return res
    elif isinstance(obj, dict):
        return {scrub_workstation_paths(k): scrub_workstation_paths(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [scrub_workstation_paths(v) for v in obj]
    return obj



def seatbelt_profile(workspace: str, scratch_dir: str | None = None) -> str:
    """Deny access to the source tree and execution of common network clients."""

    root = os.path.realpath(PROJECT_ROOT).replace('"', '\\"')
    workspace_real = os.path.realpath(workspace).replace('"', '\\"')
    scratch_allow = ""
    if scratch_dir:
        scratch_real = os.path.realpath(scratch_dir).replace('"', '\\"')
        scratch_allow = f'(allow file-read* file-write* (subpath "{scratch_real}"))\n'
    # Sign-off change 4: fail closed if the allowed roots sit under a denied
    # temp root. With TMPDIR unset, tempfile resolves under /tmp and the C1
    # denies below would revoke these allows (SBPL last-match-wins), failing
    # every stage in both arms while reading as instrumentation trouble.
    for label, raw_path in (("workspace", workspace), ("scratch_dir", scratch_dir)):
        if not raw_path:
            continue
        resolved = os.path.realpath(raw_path)
        if resolved in ("/tmp", "/private/tmp") or resolved.startswith(("/tmp/", "/private/tmp/")):
            raise RuntimeError(
                f"Amendment A C1: {label} resolves under a denied temp root ({resolved}); "
                "set TMPDIR/scratch outside /tmp before building the profile."
            )
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
        f"{scratch_allow}"
        # Amendment A C1: deny shared temp roots for BOTH arms (SBPL
        # last-match-wins keeps these effective after the allows above).
        # /var/folders is deliberately NOT denied: both arms allocate
        # runtime_dir, agent HOME, and (in pilot path) guard logs under the
        # host TMPDIR, so denying it would fail every stage in both arms.
        '(deny file-read* (subpath "/tmp"))\n'
        '(deny file-write* (subpath "/tmp"))\n'
        '(deny file-read* (subpath "/private/tmp"))\n'
        '(deny file-write* (subpath "/private/tmp"))\n'
        f"{deny_exec}\n"
    )


def sandbox_command(command: list[str], workspace: str, scratch_dir: str | None = None) -> list[str]:
    if not os.path.isfile(SANDBOX_EXEC):
        raise RuntimeError(f"Required sandbox executable is missing: {SANDBOX_EXEC}")
    return [SANDBOX_EXEC, "-p", seatbelt_profile(workspace, scratch_dir), *command]


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


# Vendor throttle signals: TEXT-ONLY patterns, deliberately no bare numbers.
# A whole-blob `\b429\b` false-fires on legitimate telemetry such as
# reasoning_tokens=429 or duration=429.12 (reviewer 2026-09-08). Real vendor
# throttle errors always wrap the code in error text, covered below.
THROTTLE_PATTERNS = (
    r"RESOURCE_EXHAUSTED",
    r"rate.?limit",
    r"too many requests",
    r"quota.{0,30}(exceed|exhaust|deplet)",
    r"(exceed|exhaust|deplet).{0,30}quota",
    r"insufficient.?quota",
    r"\boverloaded\b",
    r"error.{0,40}(429|529)",
    r"(429|529).{0,40}(error|fail|exceed|exhaust)",
)
_THROTTLE_RES = [re.compile(pattern, re.IGNORECASE) for pattern in THROTTLE_PATTERNS]
# Telemetry subtrees hold numeric usage accounting (reasoning_tokens,
# durations) that must never enter throttle text; agent prose survives via
# the top-level stdout_summary/stderr_summary copies.
_THROTTLE_SKIP_KEYS = frozenset({"telemetry"})


def iter_throttle_texts(node, _skip=False):
    """Yield string leaves of node, excluding telemetry subtrees."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from iter_throttle_texts(value, _skip or key in _THROTTLE_SKIP_KEYS)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from iter_throttle_texts(value, _skip)
    elif isinstance(node, str) and not _skip:
        yield node


def find_throttle_signal(payload) -> str | None:
    """First throttle pattern over the payload's non-telemetry text."""
    for text in iter_throttle_texts(payload):
        for pattern, compiled in zip(THROTTLE_PATTERNS, _THROTTLE_RES):
            if compiled.search(text):
                return pattern
    return None


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
