#!/usr/bin/env python3
"""Immutable pilot/full matrix runner with a mandatory frozen preflight manifest."""

from __future__ import annotations

import argparse
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "analysis"))

from calculate_stats import analyze  # noqa: E402
from experiment_config import BENCHMARK_DIR, RUNS_DIR  # noqa: E402
from preflight import validate_frozen_manifest  # noqa: E402
from run_task import run_evaluation  # noqa: E402
from runner_common import sha256_file  # noqa: E402

PILOT_TASKS = ("grade-school", "book-store", "wordy")


def load_task_ids() -> list[str]:
    with open(os.path.join(BENCHMARK_DIR, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    return [item["task_id"] for item in manifest]


def result_path(results_dir: str, task_id: str, arm: str) -> str:
    return os.path.join(results_dir, f"{task_id}_{arm}.json")


def result_is_final(results_dir: str, task_id: str, arm: str) -> bool:
    path = result_path(results_dir, task_id, arm)
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    if result.get("task_id") != task_id or result.get("arm") != arm:
        raise RuntimeError(f"Result identity mismatch: {path}")
    if result.get("status") not in {"complete", "failed"}:
        raise RuntimeError(f"Result is not final: {path}")
    verification = result.get("verification", {})
    if "ratio" not in verification or "passed" not in verification:
        raise RuntimeError(f"Result has no score: {path}")
    return True


def reject_interrupted_attempts(results_dir: str) -> None:
    attempts = sorted(
        name for name in os.listdir(results_dir)
        if name.startswith(".") and name.endswith(".attempt.json")
    )
    if attempts:
        raise RuntimeError(
            "Interrupted immutable attempts require manual telemetry adjudication; "
            f"they will not be retried or dropped: {attempts}"
        )


def planned_tasks(mode: str) -> list[str]:
    task_ids = load_task_ids()
    if mode == "pilot":
        missing = [task for task in PILOT_TASKS if task not in task_ids]
        if missing:
            raise RuntimeError(f"Pre-registered pilot task missing from manifest: {missing}")
        return list(PILOT_TASKS)
    return task_ids


def require_smoke_report(manifest_path: str) -> dict:
    smoke_path = os.path.join(os.path.dirname(manifest_path), "smoke_report.json")
    if not os.path.isfile(smoke_path):
        raise RuntimeError(f"Frozen live smoke report is required: {smoke_path}")
    with open(smoke_path, encoding="utf-8") as handle:
        smoke = json.load(handle)
    if smoke.get("status") != "pass":
        raise RuntimeError(f"Smoke report is not passing: {smoke_path}")
    if smoke.get("run_manifest_sha256") != sha256_file(manifest_path):
        raise RuntimeError("Smoke report does not match the frozen run manifest")
    return smoke

def require_parity_preflight(manifest_path: str) -> dict:
    run_dir = os.path.dirname(manifest_path)
    parity_path = os.path.join(run_dir, "preflight_parity.json")
    if not os.path.isfile(parity_path):
        raise RuntimeError(f"Preflight parity report is required before matrix launch: {parity_path}")
    with open(parity_path, encoding="utf-8") as handle:
        report = json.load(handle)
    if report.get("verdict") != "PASS":
        raise RuntimeError(f"Preflight parity gate did not pass: verdict={report.get('verdict')}")
    # C7: a diagnostics-only report (fail-fast abort or --continue-diagnostics)
    # can never gate a matrix launch, independently of the verdict field.
    if report.get("diagnostic_only"):
        raise RuntimeError("Preflight parity report is diagnostics-only; it cannot gate a matrix launch.")
    if report.get("abort_reason"):
        raise RuntimeError(f"Preflight parity run aborted: {report.get('abort_reason')}")
    expected_run_id = os.path.basename(run_dir)
    if report.get("run_id") != expected_run_id:
        raise RuntimeError(f"Preflight parity report run_id mismatch: expected {expected_run_id}, got {report.get('run_id')}")
    manifest_hash = sha256_file(manifest_path)
    report_manifest_hash = report.get("run_manifest_sha256")
    if not report_manifest_hash:
        raise RuntimeError("Preflight parity report is missing mandatory non-null run_manifest_sha256")
    if report_manifest_hash != manifest_hash:
        raise RuntimeError(
            f"Preflight parity manifest mismatch: report={report_manifest_hash} vs live={manifest_hash}"
        )
    from preflight_parity import STAGE_POOLED_REQUIRED, STAGE_TOST_REQUIRED, compute_composite_source_sha256
    live_gates = {s: {"pooled_required": STAGE_POOLED_REQUIRED[s], "tost_required": STAGE_TOST_REQUIRED[s]} for s in STAGE_POOLED_REQUIRED}
    if report.get("stage_gates") != live_gates:
        raise RuntimeError("Preflight stage-gate spec mismatch: re-run preflight on current code.")
    live_hash, _ = compute_composite_source_sha256()
    if report.get("composite_source_sha256") != live_hash:
        raise RuntimeError(
            f"Preflight parity hash mismatch: report={report.get('composite_source_sha256')} vs live={live_hash}"
        )
    return report


def run_matrix(run_id: str, mode: str, confirm_launch: bool) -> dict:
    run_dir = os.path.join(RUNS_DIR, run_id)
    manifest_path = os.path.join(run_dir, "run_manifest.json")
    frozen = validate_frozen_manifest(manifest_path)
    results_dir = frozen["results_dir"]
    reject_interrupted_attempts(results_dir)
    targets = planned_tasks(mode)
    smoke = require_smoke_report(manifest_path) if confirm_launch else None
    parity = require_parity_preflight(manifest_path) if confirm_launch else None

    pending = [
        (task_id, arm)
        for task_id in targets
        for arm in ("arm_a", "arm_b")
        if not result_is_final(results_dir, task_id, arm)
    ]
    plan = {
        "run_id": run_id,
        "mode": mode,
        "manifest_path": manifest_path,
        "results_dir": results_dir,
        "target_tasks": targets,
        "pending_attempts": pending,
        "legacy_pilot_included": frozen["legacy_pilot_results"]["included"],
        "launch_confirmed": confirm_launch,
        "smoke_report": (smoke["status"] if smoke else "not-required-for-preview"),
        "parity_preflight": (parity["verdict"] if parity else "not-required-for-preview"),
    }
    print(json.dumps(plan, indent=2))
    if not confirm_launch:
        print("\nPREVIEW ONLY: pass --confirm-launch after final human review.")
        return plan


    for index, task_id in enumerate(targets, 1):
        print(f"\n{'#' * 80}\n[{index}/{len(targets)}] {task_id}\n{'#' * 80}")
        for arm in ("arm_a", "arm_b"):
            if result_is_final(results_dir, task_id, arm):
                print(f"Skipping immutable completed attempt: {task_id}/{arm}")
                continue
            print(f"Launching immutable attempt: {task_id}/{arm}")
            result = run_evaluation(
                task_id,
                arm,
                results_dir,
                manifest_path,
                dry_run=False,
            )
            print(
                f"Completed {task_id}/{arm}: status={result['status']} "
                f"ratio={result['verification']['ratio']} "
                f"protocol_valid={result['execution']['protocol_valid']}"
            )
            sys.stdout.flush()

        print("\n--- Cumulative paired analysis ---")
        analyze(
            results_dir=results_dir,
            manifest_path=os.path.join(BENCHMARK_DIR, "manifest.json"),
            require_complete=False,
        )
        sys.stdout.flush()

    if mode == "full":
        report = analyze(
            results_dir=results_dir,
            manifest_path=os.path.join(BENCHMARK_DIR, "manifest.json"),
            require_complete=True,
        )
        print("\nFULL N=25 COMPLETENESS GATE: PASS")
    else:
        report = analyze(
            results_dir=results_dir,
            manifest_path=os.path.join(BENCHMARK_DIR, "manifest.json"),
            require_complete=False,
            report=False,
        )
        print("\nPILOT SLICE COMPLETE. Stop for human review before --full.")
    return {**plan, "analysis": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run frozen OMP vs Multi-CLI matrix")
    parser.add_argument("--run-id", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pilot", action="store_true", help="Run the three pre-registered pilot tasks")
    mode.add_argument("--full", action="store_true", help="Run/resume all 25 pre-registered tasks")
    parser.add_argument(
        "--confirm-launch",
        action="store_true",
        help="Required to execute model calls; omission performs a non-model preview",
    )
    arguments = parser.parse_args()
    run_matrix(
        arguments.run_id,
        "pilot" if arguments.pilot else "full",
        arguments.confirm_launch,
    )
