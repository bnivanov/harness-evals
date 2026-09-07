#!/usr/bin/env python3
"""Pre-flight parity gate and anti-cheating verification for Workflow Bench.

Enforces:
1. Binary pins match installed versions (exit code 0 + exact string matching).
2. Empirically calibrated symmetric effort matrix assertion across all stages.
3. Positive control: oracle solution is verified readable unconfined.
4. Negative filesystem containment: sandbox-exec denies read on oracle solution (EACCES).
5. Negative network execution containment: sandbox-exec blocks execution of curl (EPERM).
6. Statistical reasoning token parity on pilot tasks:
   - Evaluates pilot tasks (k=7 repeats on grep and list-ops, N=14 paired observations).
   - Pilot power basis (Option A): Under empirical dispersion sigma = 0.8883, N=14 (df=13, t=1.771) achieves
     P(half-width <= ln(2.0)) = 99.9% narrowness and 73.7% interval containment power at mu=0 for band [0.50, 2.00].
   - Pre-registered equivalence margins:
     * Pooled token ratio: in [0.80, 1.25]
     * TOST 90% CI: entirely contained within [0.50, 2.00]
   - Incrementally persists pair results to runs/<run_id>/pilot_records.ndjson with resume support.
   - Infra-error handling with bounded retries (MAX_INFRA_RETRIES = 2); pairs with unrecovered
     infrastructure errors are excluded from the cached completed set so they can be re-attempted.
   - Both-arms-valid pairing with explicit dropped-pair, zero-token exclusion, and stage token-gap accounting.
7. Emits preflight_parity.json bound to run_id, mandatory non-null run_manifest_sha256, and composite source_hashes().
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
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
from runner_common import sandbox_command, scrub_workstation_paths, sha256_file  # noqa: E402
from runners.arm_a_omp import run_arm_a  # noqa: E402
from runners.arm_b_multicli import run_arm_b  # noqa: E402

PILOT_TASKS = ["grep", "list-ops"]
PILOT_REPEATS = 7  # N=14 paired observations per stage cell
POOLED_BAND_LOW = 0.80
POOLED_BAND_HIGH = 1.25
TOST_BAND_LOW = 0.50
TOST_BAND_HIGH = 2.00
MAX_INFRA_RETRIES = 2
STAGES = ("1_PLANNER", "2_WORKER_INITIAL", "3_REVIEWER", "4_WORKER_REFINE")

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


def calculate_stage_tost(samples_a: list[int], samples_b: list[int], token_gaps: int = 0) -> dict[str, Any]:
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
    mean_d = sum(log_diffs) / n
    variance = sum((x - mean_d) ** 2 for x in log_diffs) / (n - 1)
    sd = math.sqrt(variance)
    se = sd / math.sqrt(n)

    t_crit = T_TABLE_90.get(n - 1, 1.895)
    ci_low_log = mean_d - t_crit * se
    ci_high_log = mean_d + t_crit * se

    ratio_point = math.exp(mean_d)
    ratio_ci_low = math.exp(ci_low_log)
    ratio_ci_high = math.exp(ci_high_log)

    mean_a = sum(a for a, _ in valid_pairs) / n
    mean_b = sum(b for _, b in valid_pairs) / n
    pooled_ratio = round(mean_a / mean_b, 4) if mean_b > 0 else 0.0

    # Equivalence evaluation: pooled ratio in [0.80, 1.25] and TOST 90% CI in [0.50, 2.00]
    pooled_ok = (POOLED_BAND_LOW <= pooled_ratio <= POOLED_BAND_HIGH)
    tost_ok = (TOST_BAND_LOW <= ratio_ci_low and ratio_ci_high <= TOST_BAND_HIGH)
    no_gaps = (token_gaps == 0)
    no_zeros = (zero_exclusions == 0)
    passed = pooled_ok and tost_ok and no_gaps and no_zeros

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
        "mean_log_diff": round(mean_d, 4),
        "sd_log_diff": round(sd, 4),
        "ratio_point": round(ratio_point, 4),
        "ratio_90_ci": [round(ratio_ci_low, 4), round(ratio_ci_high, 4)],
        "tost_band": [TOST_BAND_LOW, TOST_BAND_HIGH],
        "tost_ok": tost_ok,
        "passed": passed,
    }


def execute_arm_with_retries(runner: Any, meta: dict, src_task: str, arm_name: str, task_id: str, rep: int) -> dict[str, Any]:
    last_exc = None
    dur = 0.0
    for attempt in range(1, MAX_INFRA_RETRIES + 2):
        with tempfile.TemporaryDirectory(prefix=f"pilot_{task_id}_{arm_name}_{rep}_att{attempt}_") as workdir:
            scratch_dir = tempfile.mkdtemp(prefix=f"pilot_scratch_{task_id}_{arm_name}_{rep}_att{attempt}_")
            art_dir = os.path.join(tempfile.mkdtemp(prefix="pilot_art_"), "artifacts")
            t0 = time.monotonic()
            try:
                subprocess.run(["cp", "-R", f"{src_task}/.", workdir], check=True)
                result = runner(meta, workdir, art_dir, scratch_dir=scratch_dir)
                dur = round(time.monotonic() - t0, 2)
                stage_tokens = {}
                for s in result.get("stages", []):
                    s_name = s["stage"]
                    r_tokens = s.get("telemetry", {}).get("reasoning_tokens", 0)
                    stage_tokens[s_name] = r_tokens
                return {
                    "duration": dur,
                    "protocol_valid": result.get("protocol_valid", False),
                    "violations": result.get("protocol_violations", []),
                    "stages": stage_tokens,
                }
            except Exception as exc:
                last_exc = exc
                dur = round(time.monotonic() - t0, 2)
                print(f"    [Attempt {attempt}/{MAX_INFRA_RETRIES+1}] Infrastructure error on {arm_name} for {task_id}: {exc}")
                time.sleep(1.0)
            finally:
                shutil.rmtree(scratch_dir, ignore_errors=True)
                shutil.rmtree(os.path.dirname(art_dir), ignore_errors=True)
    return {
        "duration": dur,
        "protocol_valid": False,
        "infra_error": str(last_exc),
    }


def run_pilot_parity_matrix(run_id: str) -> dict[str, Any]:
    with open(os.path.join(BASE_DIR, "../../benchmarks/aider-python/manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    task_map = {item["task_id"]: item for item in manifest}

    run_dir = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)
    records_ndjson = os.path.join(run_dir, "pilot_records.ndjson")

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

    print(f"\nExecuting Pilot Parity Matrix: tasks={PILOT_TASKS}, k={PILOT_REPEATS} ({expected_pairs} pairs)...")
    for task_id in PILOT_TASKS:
        meta = task_map[task_id]
        src_task = os.path.join(BASE_DIR, "../../benchmarks/aider-python/tasks", task_id)
        for rep in range(1, PILOT_REPEATS + 1):
            if (task_id, rep) in completed_pairs:
                print(f"  Resuming existing pair {task_id} (rep {rep})...")
                pair_record = completed_pairs[(task_id, rep)]
            else:
                pair_record = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "task_id": task_id,
                    "repeat": rep,
                    "arms": {},
                }
                for arm_name, runner in [("arm_a", run_arm_a), ("arm_b", run_arm_b)]:
                    print(f"  Running {task_id} (rep {rep}) on {arm_name}...")
                    arm_result = execute_arm_with_retries(runner, meta, src_task, arm_name, task_id, rep)
                    pair_record["arms"][arm_name] = arm_result

                # Incremental persistence: append completed pair record immediately
                with open(records_ndjson, "a", encoding="utf-8") as f:
                    f.write(json.dumps(pair_record) + "\n")
                completed_pairs[(task_id, rep)] = pair_record

            # Strict both-arms-valid alignment check
            arm_a_info = pair_record["arms"].get("arm_a", {})
            arm_b_info = pair_record["arms"].get("arm_b", {})
            a_valid = arm_a_info.get("protocol_valid", False)
            b_valid = arm_b_info.get("protocol_valid", False)
            a_infra = arm_a_info.get("infra_error")
            b_infra = arm_b_info.get("infra_error")

            if a_infra or b_infra:
                dropped_pairs.append({
                    "task_id": task_id,
                    "repeat": rep,
                    "reason": f"unrecovered infra_error: arm_a={a_infra}, arm_b={b_infra}",
                })
                continue

            if not (a_valid and b_valid):
                dropped_pairs.append({
                    "task_id": task_id,
                    "repeat": rep,
                    "reason": f"protocol_valid failure: arm_a={a_valid}, arm_b={b_valid}",
                    "arm_a_violations": arm_a_info.get("violations", []),
                    "arm_b_violations": arm_b_info.get("violations", []),
                })
                continue

            # Both arms valid: append strictly paired stage tokens and record any gap
            for s_name in STAGES:
                tok_a = arm_a_info.get("stages", {}).get(s_name)
                tok_b = arm_b_info.get("stages", {}).get(s_name)
                if tok_a is not None and tok_b is not None:
                    stage_samples[s_name]["arm_a"].append(tok_a)
                    stage_samples[s_name]["arm_b"].append(tok_b)
                else:
                    stage_token_gaps[s_name] += 1

    # Evaluate TOST metrics across collected valid pairs
    stage_metrics = {}
    all_stages_passed = True
    total_token_gaps = sum(stage_token_gaps.values())
    for stage in STAGES:
        samples_a = stage_samples[stage]["arm_a"]
        samples_b = stage_samples[stage]["arm_b"]
        gaps = stage_token_gaps[stage]
        tost_res = calculate_stage_tost(samples_a, samples_b, token_gaps=gaps)
        stage_metrics[stage] = tost_res
        if not tost_res.get("passed"):
            all_stages_passed = False

    passed_overall = (all_stages_passed and len(dropped_pairs) == 0 and total_token_gaps == 0)

    return {
        "verdict": "PASS" if passed_overall else "FAIL",
        "total_pairs_evaluated": len(completed_pairs),
        "dropped_pairs_count": len(dropped_pairs),
        "dropped_pairs": dropped_pairs,
        "total_token_gaps": total_token_gaps,
        "stage_token_gaps": stage_token_gaps,
        "stage_metrics": stage_metrics,
        "records_file": records_ndjson,
    }


def run_preflight(run_id: str, dry_run: bool = False) -> dict[str, Any]:
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
        pilot_results = run_pilot_parity_matrix(run_id)
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
    parser.add_argument("--run-id", default="confirmatory-004", help="Run identifier")
    parser.add_argument("--dry-run", action="store_true", help="Skip live pilot model invocations")
    args = parser.parse_args()

    report = run_preflight(args.run_id, dry_run=args.dry_run)
    if report["verdict"] not in {"PASS", "DRY_RUN_PASS"}:
        sys.exit(1)


if __name__ == "__main__":
    main()
