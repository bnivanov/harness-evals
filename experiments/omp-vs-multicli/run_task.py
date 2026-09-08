#!/usr/bin/env python3
"""Create an isolated task workspace, execute one immutable attempt, and score it."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "verifier"))
sys.path.insert(0, os.path.join(BASE_DIR, "runners"))

from experiment_config import BENCHMARK_DIR  # noqa: E402
from oracle_verifier import verify_task  # noqa: E402
from arm_a_omp import run_arm_a  # noqa: E402
from arm_b_multicli import run_arm_b  # noqa: E402
from runner_common import sha256_file  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json_write(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".result-", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def setup_workspace(task_meta: dict, arm_name: str) -> str:
    task_src = os.path.join(BENCHMARK_DIR, "tasks", task_meta["task_id"])
    workspace = tempfile.mkdtemp(prefix=f"harness_eval_{task_meta['task_id']}_{arm_name}_")
    for name in os.listdir(task_src):
        source = os.path.join(task_src, name)
        if os.path.isfile(source):
            shutil.copy2(source, os.path.join(workspace, name))

    commands = (
        ["git", "init"],
        ["git", "config", "user.name", "BenchmarkRunner"],
        ["git", "config", "user.email", "runner@benchmark.local"],
        ["git", "add", "."],
        ["git", "commit", "-m", "initial stub"],
    )
    for command in commands:
        subprocess.run(command, cwd=workspace, capture_output=True, text=True, check=True)
    if subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=workspace, capture_output=True, text=True, check=True).stdout.strip() != "1":
        raise RuntimeError("Workspace must contain exactly one baseline commit")
    if subprocess.run(["git", "remote"], cwd=workspace, capture_output=True, text=True, check=True).stdout.strip():
        raise RuntimeError("Workspace unexpectedly contains a git remote")
    return workspace


def failure_verification(task_id: str, reason: str, oracle: dict | None = None) -> dict:
    oracle = oracle or {}
    return {
        "task_id": task_id,
        "passed": False,
        "ratio": 0.0,
        "passed_tests": 0,
        "failed_tests": oracle.get("total_tests", 0),
        "total_tests": oracle.get("total_tests", 0),
        "returncode": oracle.get("returncode", -1),
        "failure_reason": reason,
    }


def run_evaluation(
    task_id: str,
    arm: str,
    results_dir: str,
    run_manifest_path: str,
    dry_run: bool = False,
) -> dict:
    with open(os.path.join(BENCHMARK_DIR, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    task_meta = next((item for item in manifest if item["task_id"] == task_id), None)
    if not task_meta:
        raise ValueError(f"Task not found in manifest: {task_id}")
    if arm not in {"arm_a", "arm_b"}:
        raise ValueError(f"Exactly one arm is required, got: {arm}")
    if not dry_run and not os.path.isfile(run_manifest_path):
        raise RuntimeError(f"Frozen run manifest is required: {run_manifest_path}")

    os.makedirs(results_dir, exist_ok=True)
    result_path = os.path.join(results_dir, f"{task_id}_{arm}.json")
    attempt_path = os.path.join(results_dir, f".{task_id}_{arm}.attempt.json")
    if not dry_run and (os.path.exists(result_path) or os.path.exists(attempt_path)):
        raise FileExistsError(f"Immutable attempt already exists for {task_id}/{arm}")

    workspace = None
    scratch_dir = None
    try:
        workspace = setup_workspace(task_meta, arm)
        scratch_dir = tempfile.mkdtemp(prefix=f"harness_scratch_{task_id}_{arm}_")
        artifact_dir = os.path.join(os.path.dirname(results_dir), "traces", task_id, arm)
        print(f"Initialized isolated workspace: {workspace}")
        if dry_run:
            oracle = verify_task(task_id, workspace)
            return {
                "task_id": task_id,
                "arm": arm,
                "dry_run": True,
                "workspace": workspace,
                "oracle_verification": oracle,
            }

        with open(run_manifest_path, "rb") as handle:
            run_manifest_sha256 = sha256_file(run_manifest_path)
        attempt = {
            "status": "running",
            "task_id": task_id,
            "arm": arm,
            "started_at": utc_now(),
            "workspace": workspace,
            "artifact_dir": artifact_dir,
            "run_manifest_path": run_manifest_path,
            "run_manifest_sha256": run_manifest_sha256,
        }
        atomic_json_write(attempt_path, attempt)
        try:
            # C3/§5.2: pilot_early_stop stays False on the matrix path. An arm
            # that misses a handoff can still score from the README here; the
            # pilot-only stop in run_arm_* must never change this outcome.
            execution = (
                run_arm_a(task_meta, workspace, artifact_dir, scratch_dir=scratch_dir)
                if arm == "arm_a"
                else run_arm_b(task_meta, workspace, artifact_dir, scratch_dir=scratch_dir)
            )
            oracle = verify_task(task_id, workspace)
            protocol_valid = bool(execution.get("protocol_valid")) and not oracle.get("tampered", False)
            if protocol_valid:
                scored = dict(oracle)
            else:
                reasons = execution.get("protocol_violations", [])
                if oracle.get("tampered"):
                    reasons = [*reasons, {"code": "TAMPERED", "detail": oracle.get("tamper_reason")}]
                scored = failure_verification(task_id, json.dumps(reasons, sort_keys=True), oracle)

            combined = {
                "status": "complete",
                "task_id": task_id,
                "arm": arm,
                "started_at": attempt["started_at"],
                "completed_at": utc_now(),
                "workspace": workspace,
                "run_manifest_path": run_manifest_path,
                "run_manifest_sha256": run_manifest_sha256,
                "execution": execution,
                "oracle_verification": oracle,
                "verification": scored,
            }
        except BaseException as error:
            combined = {
                "status": "failed",
                "task_id": task_id,
                "arm": arm,
                "started_at": attempt["started_at"],
                "completed_at": utc_now(),
                "workspace": workspace,
                "run_manifest_path": run_manifest_path,
                "run_manifest_sha256": run_manifest_sha256,
                "execution": {
                    "arm": arm,
                    "task_id": task_id,
                    "duration": 0.0,
                    "normalized_total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "protocol_valid": False,
                    "protocol_violations": [{"code": "RUNNER_EXCEPTION", "detail": str(error)}],
                    "stages": [],
                },
                "oracle_verification": {},
                "verification": failure_verification(task_id, f"RUNNER_EXCEPTION: {error}"),
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc(),
                },
            }
        atomic_json_write(result_path, combined)
        os.unlink(attempt_path)
        print(
            f"Saved immutable result: {result_path}\n"
            f"Score: {combined['verification']['passed_tests']}/{combined['verification']['total_tests']} "
            f"ratio={combined['verification']['ratio']} protocol_valid={combined['execution']['protocol_valid']}"
        )
        return combined
    finally:
        if scratch_dir:
            shutil.rmtree(scratch_dir, ignore_errors=True)
        if workspace:
            shutil.rmtree(workspace, ignore_errors=True)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one immutable experiment attempt")
    parser.add_argument("--task", required=True)
    parser.add_argument("--arm", required=True, choices=["arm_a", "arm_b"])
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--run-manifest", required=True)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    run_evaluation(
        arguments.task,
        arguments.arm,
        os.path.abspath(arguments.results_dir),
        os.path.abspath(arguments.run_manifest),
        dry_run=arguments.dry_run,
    )
