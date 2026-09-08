#!/usr/bin/env python3
"""Pre-flight parity gate and anti-cheating verification for Workflow Bench.

Enforces:
1. Binary pins match installed versions (exit code 0 + exact string matching).
2. Pre-registered effort matrix holds across all stages (Amendment A: planner
   and reviewer adapter-matched at token level; worker/refine input-matched by
   shared binary+flag).
3. Positive control: oracle solution is verified readable unconfined.
4. Negative filesystem containment: sandbox-exec denies read on oracle solution (EACCES).
5. Negative network execution containment: sandbox-exec blocks execution of curl (EPERM).
6. Statistical reasoning token parity on pilot tasks (Amendment A + v2 outcome §A.6):
   - Evaluates pilot tasks (k=7 repeats on grep and list-ops, N=14 paired observations).
   - Split equivalence gate: reviewer requires pooled ratio in
     [0.80, 1.25] AND TOST 90% CI inside [0.50, 2.00] (mapping OMP `medium` /
     AGY `medium` frozen by calibration v2, pooled 1.15); planner is TOST-only
     (neither candidate mapping enters the pooled band); worker/refine are
     input-matched (same binary+flag) so only zero/gap integrity applies and
     their divergence is reported as IV, not gated.
   - Incrementally persists pair results to runs/<run_id>/pilot_records.ndjson with resume support.
   - Infra-error handling with bounded retries (MAX_INFRA_RETRIES = 2); pairs with unrecovered
     infrastructure errors are excluded from the cached completed set so they can be re-attempted.
   - Throttle guard: ANY vendor rate-limit/quota signal (429/529,
     RESOURCE_EXHAUSTED, rate-limit/quota/overloaded text) in an arm result or
     exception aborts the WHOLE pilot immediately with NO retry — retrying a
     throttled endpoint converts a brush with quota into a lockout. Abort
     reason RATE_LIMITED:<task>:rep<n>:<arm>:<signal>; fresh run_id required
     after quota recovers. Applies even under --continue-diagnostics.
   - Telemetry-only blips (Arm A REASONING_TELEMETRY_MISSING) retry as infra;
     any other violation code blocks retry; Arm B never retries (no vendor
     reasoning-text stream exists). Retry rate > 10% of arm executions fails the gate.
   - Fail-fast: first dropped pair aborts (marker pilot_aborted.json; fresh run_id
     required); second arm of a dead pair is not launched; running 90% CI fully
     outside [0.50, 2.00] at n>=5 aborts unrecoverably (catastrophe backstop;
     validated on synthetic pairs, not on 010 — see Amendment A §A.5).
     --continue-diagnostics resumes diagnostically; such output is marked
     diagnostic_only and can never gate a matrix launch.
   - Both-arms-valid pairing with explicit dropped-pair, zero-token exclusion, and stage token-gap accounting.
7. Emits preflight_parity.json bound to run_id, mandatory non-null run_manifest_sha256, and composite source_hashes().
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import time
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from experiment_config import (  # noqa: E402
    BINARY_PINS,
    EFFORT_MATRIX,
    MODEL_PINS,
    RUNS_DIR,
    STAGE_TIMEOUT_SECONDS,
    TASK_TIMEOUT_SECONDS,
)
from preflight import source_hashes  # noqa: E402
from runner_common import find_throttle_signal, sandbox_command, scrub_workstation_paths, sha256_file  # noqa: E402
from runners.arm_a_omp import run_arm_a  # noqa: E402
from runners.arm_b_multicli import run_arm_b  # noqa: E402

PILOT_TASKS = ["grep", "list-ops"]
PILOT_REPEATS = 7  # N=14 paired observations per stage cell
POOLED_BAND_LOW = 0.80
POOLED_BAND_HIGH = 1.25
TOST_BAND_LOW = 0.50
TOST_BAND_HIGH = 2.00
MAX_INFRA_RETRIES = 2

# Amendment A (post-010, Opus C1-C8; calibration-v2 outcome in PROTOCOL §A.6):
# reviewer is adapter-matched (pooled ratio + TOST under OMP medium / AGY medium).
# §A.6: planner is TOST-only (pooled bypassed, TOST enforced); worker/refine
# bypass both (input-matched, integrity-only).
STAGE_TOST_REQUIRED = {
    "1_PLANNER": True,
    "2_WORKER_INITIAL": False,
    "3_REVIEWER": True,
    "4_WORKER_REFINE": False,
}
STAGE_POOLED_REQUIRED = {
    "1_PLANNER": False,
    "2_WORKER_INITIAL": False,
    "3_REVIEWER": True,
    "4_WORKER_REFINE": False,
}
# C4: hard FAIL when re-attempts exceed 10% of arm executions in either arm.
RETRY_RATE_GATE = 0.10
# C6: unrecoverable ratio-watch trigger (running 90% CI fully outside TOST).
WATCH_MIN_VALID_PAIRS = 5
# Codes whose SOLE presence (plus companion NO_REASONING_TOKENS) marks a vendor
# telemetry blip eligible for infra retry. Any other code blocks retry (Q3).
TELEMETRY_RETRY_CODES = frozenset({"REASONING_TELEMETRY_MISSING", "NO_REASONING_TOKENS"})
STAGES = ("1_PLANNER", "2_WORKER_INITIAL", "3_REVIEWER", "4_WORKER_REFINE")


def find_rate_limit(payload: Any) -> str | None:
    """Throttle pattern over the payload's non-telemetry text (shared scanner
    in runner_common: text-only, so reasoning_tokens=429 never false-fires)."""
    return find_throttle_signal(payload)


# Sequential-stepping quota guard (2026-09-08): the pilot runs ONE pair per
# invocation and checks `omp usage` before every new pair. Caps are
# account-protection (leave headroom for other work; never ride a window to
# 100%), NOT science: a QUOTA_CAP stop strands completed pairs exactly like a
# throttle abort and needs a fresh run_id after recovery.
QUOTA_CAPS = {
    "google_weekly": 97.0,
    "xai_weekly": 90.0,
    "codex_5h": 90.0,
    "codex_7d": 50.0,
}
_USAGE_KEYS = (
    ("google antigravity", "usage (google) (weekly)", "google_weekly"),
    ("google antigravity", "usage (google) (5 hour)", "google_5h"),
    ("xai oauth", "grok build (weekly)", "xai_weekly"),
    ("openai codex", "5 hours", "codex_5h"),
    ("openai codex", "7 days", "codex_7d"),
)


def parse_usage(text: str) -> dict[str, float | None]:
    """Parse `omp usage` human output into {quota_key: percent_used}."""
    snap: dict[str, float | None] = {key: None for _, _, key in _USAGE_KEYS}
    provider = ""
    for line in text.splitlines():
        header = re.match(r"^([A-Za-z][\w .]*?) — \d+ account", line.strip())
        if header:
            provider = header.group(1).strip().lower()
            continue
        bullet = re.match(r"●\s+(.*?)\s+([\d.]+)% used", line.strip())
        if not bullet or not provider:
            continue
        label = bullet.group(1).lower()
        for prov, fragment, key in _USAGE_KEYS:
            if provider.startswith(prov) and fragment in label:
                snap[key] = float(bullet.group(2))
    return snap


def read_usage() -> dict[str, float | None]:
    """Snapshot live quotas via `omp usage` (cached server-side; ~seconds).
    ANY failure (non-zero exit, timeout, missing binary) returns an all-None
    snapshot, which check_quota treats as a breach — a guarded run never
    spends blind, and an uncaught TimeoutExpired can never skip the marker."""
    try:
        proc = subprocess.run(["omp", "usage"], capture_output=True, text=True, timeout=120)
    except Exception:  # noqa: BLE001 - timeout/OSError: fail closed below
        return {key: None for _, _, key in _USAGE_KEYS}
    if proc.returncode != 0:
        return {key: None for _, _, key in _USAGE_KEYS}
    return parse_usage(proc.stdout)


def check_quota(snap: dict[str, float | None]) -> str | None:
    """First breached `key:pct>=cap`, else first unknown burn quota, else None.
    Every capped quota is burned by the pilot (Google: reviewers both arms;
    xAI: planners; Codex: workers), so an UNKNOWN reading is a breach: the
    run stops rather than spending against an unverified window."""
    for key, cap in QUOTA_CAPS.items():
        pct = snap.get(key)
        if pct is None:
            return f"unknown:{key}"
        if pct >= cap:
            return f"{key}:{pct}>=cap{cap}"
    return None

T_TABLE_90 = {
    1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015,
    6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833, 10: 1.812,
    13: 1.771, 15: 1.753,
}


def compute_composite_source_sha256() -> tuple[str, dict[str, str]]:
    hashes = source_hashes()
    hasher = hashlib.sha256()
    for rel_path in sorted(hashes.keys()):
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(hashes[rel_path].encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest(), hashes


def verify_binary_pins() -> dict[str, Any]:
    details = {}
    for name, pin in BINARY_PINS.items():
        cmd = [pin["path"]] + pin["version_args"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Binary {name} failed version check with return code {res.returncode}: {res.stderr}")
        version_str = (res.stdout or res.stderr).strip()
        matched = pin["version"] in version_str
        details[name] = {
            "expected": pin["version"],
            "actual": version_str.splitlines()[0] if version_str else "",
            "returncode": res.returncode,
            "matched": matched,
        }
        if not matched:
            raise RuntimeError(f"Binary pin mismatch for {name}: expected '{pin['version']}' in '{version_str}'")
    return details


def verify_containment_probes() -> dict[str, Any]:
    oracle_file = os.path.realpath(os.path.join(BASE_DIR, "../../benchmarks/aider-python/oracle/solutions/wordy.py"))
    if not os.path.isfile(oracle_file):
        raise RuntimeError(f"Positive control failed: oracle file missing at {oracle_file}")
    with open(oracle_file, "r", encoding="utf-8") as handle:
        sample = handle.read(100)
    if len(sample) == 0:
        raise RuntimeError("Positive control failed: oracle file is empty")

    with tempfile.TemporaryDirectory(prefix="harness_containment_probe_") as tmpdir:
        probe_code = f"""
import os, sys, subprocess

# Probe 1: Negative Oracle Quarantine Probe
try:
    with open("{oracle_file}", "r", encoding="utf-8") as f:
        print("SECURITY_BREACH_LEAKED_ORACLE")
        sys.exit(99)
except PermissionError:
    print("ORACLE_QUARANTINED_EACCES")
except OSError as e:
    if e.errno == 1:
        print("ORACLE_QUARANTINED_EPERM")
    else:
        print(f"ORACLE_UNEXPECTED_OS_ERROR: {{e}}")
        sys.exit(98)
except Exception as e:
    print(f"ORACLE_UNEXPECTED_ERROR: {{e}}")
    sys.exit(98)

# Probe 2: Negative Network Executable Probe
try:
    res = subprocess.run(["/usr/bin/curl", "--version"], capture_output=True)
    if res.returncode == 0:
        print("SECURITY_BREACH_CURL_EXECUTED")
        sys.exit(97)
    else:
        print(f"CURL_FAILED_RC_{{res.returncode}}")
except PermissionError:
    print("CURL_EXEC_BLOCKED_EPERM")
except OSError as e:
    if e.errno == 1:
        print("CURL_EXEC_BLOCKED_EPERM")
    else:
        print(f"CURL_UNEXPECTED_OS_ERROR: {{e}}")
        sys.exit(96)
except Exception as e:
    print(f"CURL_UNEXPECTED_ERROR: {{e}}")
    sys.exit(95)

sys.exit(0)
"""
        probe_py = os.path.join(tmpdir, "containment_probe.py")
        with open(probe_py, "w", encoding="utf-8") as f:
            f.write(probe_code)

        cmd = sandbox_command(["python3", probe_py], tmpdir)
        res = subprocess.run(cmd, capture_output=True, text=True)
        stdout_lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]

        if res.returncode != 0:
            raise RuntimeError(f"Containment probe script failed with code {res.returncode}: {res.stderr}")
        if "ORACLE_QUARANTINED_EACCES" not in stdout_lines and "ORACLE_QUARANTINED_EPERM" not in stdout_lines:
            raise RuntimeError(f"Oracle quarantine probe failed: {stdout_lines}")
        if "CURL_EXEC_BLOCKED_EPERM" not in stdout_lines:
            raise RuntimeError(f"Network client block probe failed: {stdout_lines}")

    return {
        "positive_control": {"oracle_file": oracle_file, "verified_readable": True},
        "negative_oracle_probe": {"status": "quarantined", "evidence": stdout_lines[0]},
        "negative_network_probe": {"status": "blocked", "evidence": stdout_lines[1]},
    }


def _log_ratio_ci(valid_pairs: list[tuple[float, float]]) -> tuple[float, float, float, float, float]:
    """Mean log-diff, sd, point ratio, and 90% CI bounds for paired samples."""
    n = len(valid_pairs)
    log_diffs = [math.log(a) - math.log(b) for a, b in valid_pairs]
    mean_d = sum(log_diffs) / n
    variance = sum((x - mean_d) ** 2 for x in log_diffs) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(variance)
    se = sd / math.sqrt(n)
    t_crit = T_TABLE_90.get(n - 1, 1.895)
    return mean_d, sd, math.exp(mean_d), math.exp(mean_d - t_crit * se), math.exp(mean_d + t_crit * se)


def calculate_stage_tost(samples_a: list[int], samples_b: list[int], token_gaps: int = 0, pooled_required: bool = True, tost_required: bool = True) -> dict[str, Any]:
    assert len(samples_a) == len(samples_b), (
        f"Paired length mismatch: {len(samples_a)} != {len(samples_b)}"
    )
    total_pairs = len(samples_a)
    zero_exclusions = sum(1 for a, b in zip(samples_a, samples_b) if a <= 0 or b <= 0)
    valid_pairs = [(a, b) for a, b in zip(samples_a, samples_b) if a > 0 and b > 0]
    n = len(valid_pairs)

    if n < 2:
        return {
            "total_pairs": total_pairs,
            "zero_exclusions": zero_exclusions,
            "token_gaps": token_gaps,
            "n": n,
            "tost_passed": False,
            "error": "Insufficient valid non-zero pairs (n < 2)",
        }

    log_diffs = [math.log(a) - math.log(b) for a, b in valid_pairs]
    mean_log_diff, sd, ratio_point, ratio_ci_low, ratio_ci_high = _log_ratio_ci(valid_pairs)

    mean_a = sum(a for a, _ in valid_pairs) / n
    mean_b = sum(b for _, b in valid_pairs) / n
    pooled_ratio = round(mean_a / mean_b, 4) if mean_b > 0 else 0.0

    # Equivalence evaluation: pooled ratio in [0.80, 1.25] and TOST 90% CI in [0.50, 2.00].
    # Three gate modes: pooled+TOST (reviewer), TOST-only (planner, §A.6 —
    # pooled_required=False must NOT bypass TOST), and integrity-only
    # (worker/refine: input-matched, C5a — tost_required=False).
    pooled_ok = (POOLED_BAND_LOW <= pooled_ratio <= POOLED_BAND_HIGH)
    tost_ok = (TOST_BAND_LOW <= ratio_ci_low and ratio_ci_high <= TOST_BAND_HIGH)
    no_gaps = (token_gaps == 0)
    no_zeros = (zero_exclusions == 0)
    equivalence_ok = (pooled_ok if pooled_required else True) and (tost_ok if tost_required else True)
    passed = equivalence_ok and no_gaps and no_zeros

    return {
        "total_pairs": total_pairs,
        "zero_exclusions": zero_exclusions,
        "token_gaps": token_gaps,
        "n": n,
        "mean_arm_a": round(mean_a, 1),
        "mean_arm_b": round(mean_b, 1),
        "pooled_ratio": pooled_ratio,
        "pooled_band": [POOLED_BAND_LOW, POOLED_BAND_HIGH],
        "pooled_ok": pooled_ok,
        "mean_log_diff": round(mean_log_diff, 4),
        "sd_log_diff": round(sd, 4),
        "ratio_point": round(ratio_point, 4),
        "ratio_90_ci": [round(ratio_ci_low, 4), round(ratio_ci_high, 4)],
        "tost_band": [TOST_BAND_LOW, TOST_BAND_HIGH],
        "tost_ok": tost_ok,
        "pooled_required": pooled_required,
        "tost_required": tost_required,
        "passed": passed,
    }


def _telemetry_only_retryable(violations: list[dict]) -> bool:
    """True iff every violation is the vendor telemetry-blip pair (C4/Q3 taxonomy).

    Arm stages always emit NO_REASONING_TOKENS alongside
    REASONING_TELEMETRY_MISSING when usage accounting is absent, so both codes
    together still mark a pure blip. Any third code (handoff, guard, timeout,
    model, parse, task) blocks retry: those are arm failures, not infra.
    """
    codes = {item.get("code") for item in violations}
    return bool(codes) and "REASONING_TELEMETRY_MISSING" in codes and codes <= TELEMETRY_RETRY_CODES


class _RetainableTempDir:
    """mkdtemp whose cleanup can be disarmed for one attempt.
    (A wrapped TemporaryDirectory cannot serve: its weakref finalizer fires
    on GC regardless of __exit__, deleting kept trees. Owning the lifetime
    avoids the trap and any private-API detach.)"""
    def __init__(self, prefix: str) -> None:
        self.name = tempfile.mkdtemp(prefix=prefix)
        self.keep = False
    def __enter__(self) -> "_RetainableTempDir":
        return self
    def __exit__(self, exc_type, exc, tb) -> bool:
        if not self.keep:
            shutil.rmtree(self.name, ignore_errors=True)
        return False



def _retain_attempt(retain_root: str | None, task_id: str, rep: int, arm_name: str,
                    attempt: int, workdir: str, art_parent: str,
                    arm_result: dict | None, error: str | None) -> str | None:
    """Copy per-attempt evidence under the run dir before temp cleanup.
    Reviewer 2026-09-08 (doubt-stop verdict b): the pilot deleted every
    attempt's raw evidence, making telemetry-vs-parser adjudication
    impossible post-hoc. Retain the full arm result, the workspace snapshot
    (handoff artifacts), and the runner artifact dir (guard/stage traces),
    for failed and retried attempts alike. Returns the run-relative dir."""
    if not retain_root:
        return None
    # Unique suffix: --continue-diagnostics re-executes identical
    # task/rep/arm/attempt keys; deterministic names would overwrite prior
    # evidence and merge stale workspace files.
    name = f"{task_id}_rep{rep}_{arm_name}_att{attempt}_{uuid.uuid4().hex[:8]}"
    dest = os.path.join(retain_root, "attempts", name)
    try:
        os.makedirs(dest, exist_ok=False)
        with open(os.path.join(dest, "attempt_meta.json"), "w", encoding="utf-8") as handle:
            json.dump({"task_id": task_id, "rep": rep, "arm": arm_name,
                       "attempt": attempt, "error": error}, handle, indent=2)
        if arm_result is not None:
            with open(os.path.join(dest, "arm_result.json"), "w", encoding="utf-8") as handle:
                json.dump(arm_result, handle, indent=2, default=str)
        if os.path.isdir(workdir):
            # symlinks=True: preserve links without traversal. Dereferencing
            # (default) would copy outside-tree bytes (auth, oracle paths)
            # into retained runs and expand directory links off-tree.
            shutil.copytree(workdir, os.path.join(dest, "workspace"), symlinks=True)
        art_dir = os.path.join(art_parent, "artifacts")
        if os.path.isdir(art_dir):
            shutil.copytree(art_dir, os.path.join(dest, "artifacts"), symlinks=True)
    except OSError as exc:
        print(f"    [Attempt {attempt}] WARNING: attempt retention failed ({exc}); "
              f"workspace cleanup disarmed, scratch/art left at {art_parent}")
        return f"RETENTION_FAILED:{name}:{exc}"
    return os.path.relpath(dest, retain_root)


def execute_arm_with_retries(runner: Any, meta: dict, src_task: str, arm_name: str, task_id: str, rep: int, pilot_early_stop: bool = False, retain_root: str | None = None) -> dict[str, Any]:
    attempt_dirs: list[str] = []
    last_exc = None
    dur = 0.0
    retries = 0
    retry_log: list[dict] = []
    for attempt in range(1, MAX_INFRA_RETRIES + 2):
        with _RetainableTempDir(prefix=f"pilot_{task_id}_{arm_name}_{rep}_att{attempt}_") as _workdir_ctx:
            workdir = _workdir_ctx.name
            scratch_dir = tempfile.mkdtemp(prefix=f"pilot_scratch_{task_id}_{arm_name}_{rep}_att{attempt}_")
            art_dir = os.path.join(tempfile.mkdtemp(prefix="pilot_art_"), "artifacts")
            t0 = time.monotonic()
            payload_result = None
            payload_error = None
            try:
                subprocess.run(["cp", "-R", f"{src_task}/.", workdir], check=True)
                result = runner(meta, workdir, art_dir, scratch_dir=scratch_dir, pilot_early_stop=pilot_early_stop)
                payload_result = result
                dur = round(time.monotonic() - t0, 2)
                stage_tokens = {}
                for s in result.get("stages", []):
                    s_name = s["stage"]
                    r_tokens = s.get("telemetry", {}).get("reasoning_tokens", 0)
                    stage_tokens[s_name] = r_tokens
                violations = result.get("protocol_violations", [])
                # Throttle guard: a 429/quota signal anywhere in the arm result
                # returns immediately with NO retry and NO sleep — hammering a
                # throttled endpoint converts a brush with quota into a lockout.
                throttle = find_rate_limit(result)
                if throttle is not None:
                    print(f"    [Attempt {attempt}] RATE LIMITED on {arm_name} for {task_id} (signal {throttle!r}); aborting pilot, no retry.")
                    return {
                        "duration": round(time.monotonic() - t0, 2),
                        "protocol_valid": False,
                        "rate_limited": True,
                        "throttle_signal": throttle,
                        "infra_error": f"RATE_LIMITED ({throttle})",
                        "violations": violations,
                        "stages": stage_tokens,
                        "retries": retries,
                        "retry_log": retry_log,
                        "attempt_dirs": attempt_dirs,
                    }
                if _telemetry_only_retryable(violations):
                    blip_stages = [
                        s["stage"] for s in result.get("stages", [])
                        if any(v.get("code") == "REASONING_TELEMETRY_MISSING" for v in s.get("protocol_violations", []))
                    ]
                    if retries < MAX_INFRA_RETRIES:
                        retries += 1
                        retry_log.append({"attempt": attempt, "stages": blip_stages})
                        print(f"    [Attempt {attempt}/{MAX_INFRA_RETRIES+1}] Telemetry-only blip on {arm_name} for {task_id} ({blip_stages}); retrying with fresh workdir.")
                        time.sleep(1.0)
                        continue
                    return {
                        "duration": dur,
                        "protocol_valid": False,
                        "infra_error": f"unrecovered REASONING_TELEMETRY_MISSING after {retries} retries",
                        "violations": violations,
                        "stages": stage_tokens,
                        "retries": retries,
                        "retry_log": retry_log,
                        "attempt_dirs": attempt_dirs,
                    }
                return {
                    "duration": dur,
                    "protocol_valid": result.get("protocol_valid", False),
                    "violations": violations,
                    "stages": stage_tokens,
                    "retries": retries,
                    "retry_log": retry_log,
                    "attempt_dirs": attempt_dirs,
                }
            except Exception as exc:
                payload_result = None
                payload_error = f"{type(exc).__name__}: {exc}"
                # Throttle guard (exception path): same no-retry abort. The
                # run loop converts rate_limited into a whole-pilot abort.
                throttle = find_rate_limit(str(exc))
                if throttle is not None:
                    print(f"    [Attempt {attempt}] RATE LIMITED on {arm_name} for {task_id} (signal {throttle!r}); aborting pilot, no retry.")
                    return {
                        "duration": round(time.monotonic() - t0, 2),
                        "protocol_valid": False,
                        "rate_limited": True,
                        "throttle_signal": throttle,
                        "infra_error": f"RATE_LIMITED ({throttle}): {exc}",
                        "retries": retries,
                        "retry_log": retry_log,
                        "attempt_dirs": attempt_dirs,
                    }
                last_exc = exc
                dur = round(time.monotonic() - t0, 2)
                print(f"    [Attempt {attempt}/{MAX_INFRA_RETRIES+1}] Infrastructure error on {arm_name} for {task_id}: {exc}")
                time.sleep(1.0)
            finally:
                retained = _retain_attempt(retain_root, task_id, rep, arm_name, attempt, workdir, os.path.dirname(art_dir), payload_result, payload_error)
                if retained is not None:
                    attempt_dirs.append(retained)
                if retained is not None and retained.startswith("RETENTION_FAILED:"):
                    # Fail-SAFE: disarm the workdir cleanup so the workspace
                    # survives in place (no allocation that could fail), skip
                    # scratch/art deletes, and leave the sentinel in the
                    # record. In-flight return/exception/continue unchanged.
                    _workdir_ctx.keep = True
                    print(f"    [Attempt {attempt}] workspace preserved in place: {workdir}; "
                          f"scratch/art left at {scratch_dir} {os.path.dirname(art_dir)}")
                else:
                    shutil.rmtree(scratch_dir, ignore_errors=True)
                    shutil.rmtree(os.path.dirname(art_dir), ignore_errors=True)
    return {
        "duration": dur,
        "protocol_valid": False,
        "infra_error": str(last_exc),
        "retries": retries,
        "retry_log": retry_log,
        "attempt_dirs": attempt_dirs,
    }


def _write_abort_marker(abort_marker: str, run_id: str, abort_reason: str) -> None:
    with open(abort_marker, "w", encoding="utf-8") as handle:
        json.dump({
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "abort_reason": abort_reason,
        }, handle, indent=2)


def run_pilot_parity_matrix(
    run_id: str,
    runners: dict[str, Any] | None = None,
    task_meta_map: dict[str, dict] | None = None,
    task_source: dict[str, str] | None = None,
    continue_diagnostics: bool = False,
    max_new_pairs: int | None = None,
    quota_guard: bool = False,
) -> dict[str, Any]:
    with open(os.path.join(BASE_DIR, "../../benchmarks/aider-python/manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    task_map = task_meta_map or {item["task_id"]: item for item in manifest}
    arm_runners = runners or {"arm_a": run_arm_a, "arm_b": run_arm_b}

    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    records_ndjson = os.path.join(run_dir, "pilot_records.ndjson")
    abort_marker = os.path.join(run_dir, "pilot_aborted.json")
    if os.path.isfile(abort_marker) and not continue_diagnostics:
        with open(abort_marker, encoding="utf-8") as handle:
            prior = json.load(handle)
        raise RuntimeError(
            f"Pilot {run_id} previously aborted ({prior.get('abort_reason')}). "
            f"A fresh run_id is required; --continue-diagnostics only resumes diagnostically."
        )

    completed_pairs: dict[tuple[str, int], dict[str, Any]] = {}
    if os.path.isfile(records_ndjson):
        with open(records_ndjson, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    t_id = rec.get("task_id")
                    rep = rec.get("repeat")
                    if t_id and rep and "arms" in rec and "arm_a" in rec["arms"] and "arm_b" in rec["arms"]:
                        a_infra = rec["arms"]["arm_a"].get("infra_error")
                        b_infra = rec["arms"]["arm_b"].get("infra_error")
                        if not (a_infra or b_infra):
                            completed_pairs[(t_id, rep)] = rec
                        else:
                            print(f"Skipping cached pair {t_id} (rep {rep}) due to recorded infra error; will re-attempt.")
                except Exception:
                    pass
        print(f"Loaded {len(completed_pairs)} previously persisted pilot pairs from {records_ndjson}.")
    expected_pairs = len(PILOT_TASKS) * PILOT_REPEATS
    stage_samples: dict[str, dict[str, list[int]]] = {
        s: {"arm_a": [], "arm_b": []} for s in STAGES
    }
    stage_token_gaps: dict[str, int] = {s: 0 for s in STAGES}
    dropped_pairs: list[dict[str, Any]] = []
    abort_reason: str | None = None
    stop = False
    new_pairs = 0
    quota_snapshots: list[dict[str, Any]] = []

    print(f"\nExecuting Pilot Parity Matrix: tasks={PILOT_TASKS}, k={PILOT_REPEATS} ({expected_pairs} pairs)...")
    for task_id in PILOT_TASKS:
        meta = task_map[task_id]
        if task_source and task_id in task_source:
            src_task = task_source[task_id]
        else:
            src_task = os.path.join(BASE_DIR, "../../benchmarks/aider-python/tasks", task_id)
        for rep in range(1, PILOT_REPEATS + 1):
            if (task_id, rep) in completed_pairs:
                print(f"  Resuming existing pair {task_id} (rep {rep})...")
                pair_record = completed_pairs[(task_id, rep)]
            else:
                if quota_guard:
                    snap = read_usage()
                    quota_snapshots.append({"phase": "pre", "task_id": task_id, "repeat": rep, "quotas": snap})
                    breach = check_quota(snap)
                    if breach is not None:
                        if abort_reason is None:
                            abort_reason = f"QUOTA_CAP:pre:{task_id}:rep{rep}:{breach}"
                            _write_abort_marker(abort_marker, run_id, abort_reason)
                            print(f"  Quota-cap stop: {abort_reason} — pilot stops before spending; fresh run_id required after recovery.")
                        stop = True
                        break
                    print(f"  Quotas pre-pair: {snap}")
                pair_record = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "task_id": task_id,
                    "repeat": rep,
                    "arms": {},
                }
                print(f"  Running {task_id} (rep {rep}) on arm_a...")
                arm_a_res = execute_arm_with_retries(
                    arm_runners["arm_a"], meta, src_task, "arm_a", task_id, rep, pilot_early_stop=True, retain_root=run_dir
                )
                pair_record["arms"]["arm_a"] = arm_a_res
                if arm_a_res.get("protocol_valid", False) and not arm_a_res.get("infra_error"):
                    print(f"  Running {task_id} (rep {rep}) on arm_b...")
                    pair_record["arms"]["arm_b"] = execute_arm_with_retries(
                        arm_runners["arm_b"], meta, src_task, "arm_b", task_id, rep, pilot_early_stop=True, retain_root=run_dir
                    )
                else:
                    # Fail-fast: a dead pair cannot become valid; spare arm_b.
                    pair_record["arms"]["arm_b"] = {
                        "skipped": True,
                        "reason": "arm_a protocol-failed or infra-unrecovered; second arm not launched (fail-fast)",
                    }
                    print(f"  Skipping {task_id} (rep {rep}) on arm_b (arm_a dead)...")

                # Incremental persistence: append completed pair record immediately
                with open(records_ndjson, "a", encoding="utf-8") as f:
                    f.write(json.dumps(pair_record) + "\n")
                completed_pairs[(task_id, rep)] = pair_record
                new_pairs += 1
                if quota_guard:
                    post = read_usage()
                    quota_snapshots.append({"phase": "post", "task_id": task_id, "repeat": rep, "quotas": post})
                    print(f"  Quotas post-pair: {post}")
                    breach = check_quota(post)
                    if breach is not None and abort_reason is None:
                        abort_reason = f"QUOTA_CAP:post:{task_id}:rep{rep}:{breach}"
                        _write_abort_marker(abort_marker, run_id, abort_reason)
                        print(f"  Quota-cap stop: {abort_reason} — no further pairs; fresh run_id required after recovery.")
                        stop = True
                if max_new_pairs is not None and new_pairs >= max_new_pairs and not stop:
                    print(f"  Step limit reached ({new_pairs} new pair(s) this invocation); stopping for health/usage review. Resume with the same run_id.")
                    stop = True
            # Throttle guard (run level): a rate-limited arm aborts the WHOLE
            # pilot immediately — no second arm, no further pairs, not even in
            # --continue-diagnostics (diagnostic traffic hammers quota too).
            arm_a_info = pair_record["arms"].get("arm_a", {})
            arm_b_info = pair_record["arms"].get("arm_b", {})
            throttled = (
                "arm_a" if arm_a_info.get("rate_limited")
                else ("arm_b" if arm_b_info.get("rate_limited") else None)
            )
            if throttled is not None:
                if abort_reason is None:
                    abort_reason = (
                        f"RATE_LIMITED:{task_id}:rep{rep}:{throttled}:"
                        f"{pair_record['arms'][throttled].get('throttle_signal', '?')}"
                    )
                    _write_abort_marker(abort_marker, run_id, abort_reason)
                    print(f"  Throttle abort: {abort_reason} — pilot stops, fresh run_id required after quota recovers.")
                stop = True

            # Strict both-arms-valid alignment check (arm infos from throttle block above)
            a_valid = arm_a_info.get("protocol_valid", False)
            b_valid = arm_b_info.get("protocol_valid", False)
            a_infra = arm_a_info.get("infra_error")
            b_infra = arm_b_info.get("infra_error")
            b_skipped = arm_b_info.get("skipped", False)

            drop_kind: str | None = None
            if b_skipped:
                drop_kind = "infra" if a_infra else "protocol"
                dropped_pairs.append({
                    "task_id": task_id,
                    "repeat": rep,
                    "reason": f"second arm skipped: arm_a valid={a_valid}, infra={a_infra}",
                    "arm_a_violations": arm_a_info.get("violations", []),
                    "arm_b_violations": [],
                })
            elif a_infra or b_infra:
                drop_kind = "infra"
                dropped_pairs.append({
                    "task_id": task_id,
                    "repeat": rep,
                    "reason": f"unrecovered infra_error: arm_a={a_infra}, arm_b={b_infra}",
                })
            elif not (a_valid and b_valid):
                drop_kind = "protocol"
                dropped_pairs.append({
                    "task_id": task_id,
                    "repeat": rep,
                    "reason": f"protocol_valid failure: arm_a={a_valid}, arm_b={b_valid}",
                    "arm_a_violations": arm_a_info.get("violations", []),
                    "arm_b_violations": arm_b_info.get("violations", []),
                })
            else:
                # Both arms valid: append strictly paired stage tokens and record any gap
                for s_name in STAGES:
                    tok_a = arm_a_info.get("stages", {}).get(s_name)
                    tok_b = arm_b_info.get("stages", {}).get(s_name)
                    if tok_a is not None and tok_b is not None:
                        stage_samples[s_name]["arm_a"].append(tok_a)
                        stage_samples[s_name]["arm_b"].append(tok_b)
                    else:
                        stage_token_gaps[s_name] += 1
                # Running pooled prints + C6 ratio watch on pooled-gated stages.
                # Backstop only: synthetic off-band pairs trip it at n=5
                # (test_ratio_watch_aborts_at_five_valid_pairs); 010 replay never
                # leaves the band, so first-drop remains the expected trigger.
                for s_name in STAGES:
                    xs_a = stage_samples[s_name]["arm_a"]
                    xs_b = stage_samples[s_name]["arm_b"]
                    n_valid = len(xs_a)
                    if n_valid == 0:
                        continue
                    sum_a = sum(xs_a)
                    sum_b = sum(xs_b)
                    running_pooled = sum_a / sum_b if sum_b else 0.0
                    print(f"    [running {s_name}] n={n_valid} sumA={sum_a} sumB={sum_b} pooled={running_pooled:.4f} bands pooled[0.80,1.25] tost[0.50,2.00]")
                    if STAGE_POOLED_REQUIRED[s_name] and n_valid >= WATCH_MIN_VALID_PAIRS:
                        _, _, _, ci_lo, ci_hi = _log_ratio_ci(list(zip(xs_a, xs_b)))
                        if ci_hi < TOST_BAND_LOW or ci_lo > TOST_BAND_HIGH:
                            abort_reason = (
                                f"UNRECOVERABLE_POOLED_RATIO:{s_name}:"
                                f"90CI[{ci_lo:.4f},{ci_hi:.4f}]@n={n_valid}"
                            )
                            _write_abort_marker(abort_marker, run_id, abort_reason)
                            print(f"  UNRECOVERABLE ratio watch triggered: {abort_reason}")
                            stop = True
                            break

            if drop_kind is not None:
                if abort_reason is None:
                    abort_reason = f"FIRST_DROP:{task_id}:rep{rep}:{drop_kind}"
                    _write_abort_marker(abort_marker, run_id, abort_reason)
                    print(f"  Fail-fast abort: {abort_reason}")
                if not continue_diagnostics:
                    stop = True
            if stop:
                break
        if stop:
            break

    # Evaluate TOST metrics across collected valid pairs
    stage_metrics = {}
    all_stages_passed = True
    total_token_gaps = sum(stage_token_gaps.values())
    for stage in STAGES:
        samples_a = stage_samples[stage]["arm_a"]
        samples_b = stage_samples[stage]["arm_b"]
        gaps = stage_token_gaps[stage]
        tost_res = calculate_stage_tost(
            samples_a, samples_b, token_gaps=gaps, pooled_required=STAGE_POOLED_REQUIRED[stage],
            tost_required=STAGE_TOST_REQUIRED[stage],
        )
        stage_metrics[stage] = tost_res
        if not tost_res.get("passed"):
            all_stages_passed = False

    # C4 retry hard gate over executed (non-skipped) arm runs.
    arm_runs = {"arm_a": 0, "arm_b": 0}
    arm_retries = {"arm_a": 0, "arm_b": 0}
    for rec in completed_pairs.values():
        arms = rec.get("arms", {})
        for arm in ("arm_a", "arm_b"):
            info = arms.get(arm, {})
            if not isinstance(info, dict) or info.get("skipped"):
                continue
            arm_runs[arm] += 1
            arm_retries[arm] += int(info.get("retries", 0))
    retry_rates = {
        arm: (arm_retries[arm] / arm_runs[arm] if arm_runs[arm] else 0.0)
        for arm in ("arm_a", "arm_b")
    }
    retry_gate_ok = all(rate <= RETRY_RATE_GATE for rate in retry_rates.values())

    complete = (len(completed_pairs) == expected_pairs)
    # Sign-off change 5: any shortfall is diagnostic by construction (a drop or
    # abort sets the flag above), and PASS additionally requires `complete`.
    # The matrix side independently rejects diagnostic_only reports (C7).
    diagnostic_only = bool(dropped_pairs) or abort_reason is not None or continue_diagnostics or not complete
    passed_overall = (
        all_stages_passed
        and len(dropped_pairs) == 0
        and total_token_gaps == 0
        and retry_gate_ok
        and complete
    )

    return {
        "verdict": "PASS" if passed_overall else "FAIL",
        "total_pairs_evaluated": len(completed_pairs),
        "expected_pairs": expected_pairs,
        "dropped_pairs_count": len(dropped_pairs),
        "dropped_pairs": dropped_pairs,
        "total_token_gaps": total_token_gaps,
        "stage_token_gaps": stage_token_gaps,
        "stage_metrics": stage_metrics,
        "stage_gates": {s: {"pooled_required": STAGE_POOLED_REQUIRED[s], "tost_required": STAGE_TOST_REQUIRED[s]} for s in STAGES},
        "abort_reason": abort_reason,
        "diagnostic_only": diagnostic_only,
        "continue_diagnostics": continue_diagnostics,
        "retry_gate": {
            "threshold": RETRY_RATE_GATE,
            "arm_runs": arm_runs,
            "arm_retries": arm_retries,
            "rates": retry_rates,
            "ok": retry_gate_ok,
        },
        "records_file": records_ndjson,
        "new_pairs": new_pairs,
        "quota_guard": quota_guard,
        "quota_snapshots": quota_snapshots,
    }


def run_preflight(run_id: str, dry_run: bool = False, continue_diagnostics: bool = False, max_new_pairs: int | None = None, quota_guard: bool = False) -> dict[str, Any]:
    print("=== WORKFLOW BENCH PRE-FLIGHT PARITY GATE ===")
    print(f"Target Run ID: {run_id}")

    composite_hash, source_map = compute_composite_source_sha256()
    print(f"Composite Source SHA-256: {composite_hash} ({len(source_map)} frozen files)")

    print("\n1. Verifying installed binary pins...")
    binary_status = verify_binary_pins()
    print("   All binaries match frozen version pins.")

    print("\n2. Verifying containment seatbelts...")
    containment_status = verify_containment_probes()
    print("   Positive control & negative containment probes PASSED.")

    # Strict non-null manifest requirement
    manifest_path = os.path.join(RUNS_DIR, run_id, "run_manifest.json")
    if not os.path.isfile(manifest_path):
        raise RuntimeError(
            f"Mandatory run_manifest.json missing at {manifest_path}. "
            f"Freeze manifest first with: python3 preflight.py --prepare --run-id {run_id}"
        )
    manifest_hash = sha256_file(manifest_path)
    print(f"\n3. Bound to run manifest SHA-256: {manifest_hash}")

    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "composite_source_sha256": composite_hash,
        "run_manifest_sha256": manifest_hash,
        "source_hashes": source_map,
        "binary_pins": binary_status,
        "containment": containment_status,
        "effort_matrix": EFFORT_MATRIX,
        "model_pins": MODEL_PINS,
        "pilot_power_basis": {
            "pilot_tasks": PILOT_TASKS,
            "pilot_repeats": PILOT_REPEATS,
            "total_pairs": len(PILOT_TASKS) * PILOT_REPEATS,
            "pooled_band": [POOLED_BAND_LOW, POOLED_BAND_HIGH],
            "tost_band": [TOST_BAND_LOW, TOST_BAND_HIGH],
            "max_infra_retries": MAX_INFRA_RETRIES,
            "protocol_amendment": "A",
            "stage_gates": {s: {"pooled_required": STAGE_POOLED_REQUIRED[s], "tost_required": STAGE_TOST_REQUIRED[s]} for s in STAGES},
            "retry_rate_gate": RETRY_RATE_GATE,
            "ratio_watch": {"min_valid_pairs": WATCH_MIN_VALID_PAIRS, "tost_band": [TOST_BAND_LOW, TOST_BAND_HIGH]},
        },
        "ceilings": {
            "stage_seconds": STAGE_TIMEOUT_SECONDS,
            "task_seconds": TASK_TIMEOUT_SECONDS,
        },
    }

    if dry_run:
        print("\nDry-run mode: skipping pilot model invocations.")
        report["verdict"] = "DRY_RUN_PASS"
    else:
        pilot_results = run_pilot_parity_matrix(run_id, continue_diagnostics=continue_diagnostics, max_new_pairs=max_new_pairs, quota_guard=quota_guard)
        report.update(pilot_results)

    # Save artifact strictly inside run directory
    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    target_json = os.path.join(run_dir, "preflight_parity.json")
    report = scrub_workstation_paths(report)
    with open(target_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nWrote {target_json}")

    print(f"Final Preflight Verdict: {report['verdict']}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="confirmatory-011", help="Run identifier")
    parser.add_argument("--dry-run", action="store_true", help="Skip live pilot model invocations")
    parser.add_argument(
        "--continue-diagnostics",
        action="store_true",
        help="After a fail-fast abort, run remaining pairs diagnostically. Output is marked diagnostic_only and can never gate a matrix launch.",
    )
    parser.add_argument("--max-new-pairs", type=int, default=None, help="Sequential stepping: stop after this many NEW pairs; resume with the same run_id for pair-by-pair health/usage review.")
    parser.add_argument("--quota-guard", action="store_true", help="Check `omp usage` before every new pair; stop on QUOTA_CAP breach (pre and post snapshots recorded).")
    args = parser.parse_args()

    report = run_preflight(args.run_id, dry_run=args.dry_run, continue_diagnostics=args.continue_diagnostics, max_new_pairs=args.max_new_pairs, quota_guard=args.quota_guard)
    if report["verdict"] not in {"PASS", "DRY_RUN_PASS"}:
        sys.exit(1)


if __name__ == "__main__":
    main()
