#!/usr/bin/env python3
"""Execute the Option 2 Arm A reruns under the hardened runner with concurrency=2."""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from run_task import run_evaluation  # noqa: E402
from run_matrix import result_is_final  # noqa: E402

RUN_ID = "reruns-hardened-001"
RUN_DIR = os.path.join(BASE_DIR, "runs", RUN_ID)
MANIFEST_PATH = os.path.join(RUN_DIR, "run_manifest.json")
RESULTS_DIR = os.path.join(RUN_DIR, "results")

# Option 2: 6 Arm A tasks needing hardened verification
TARGET_TASKS = [
    "robot-name",
    "two-bucket",
    "go-counting",
    "list-ops",
    "react",
    "rest-api",
]


def execute_task(task_id: str) -> dict:
    started = time.time()
    print(f"[{time.strftime('%X')}] Starting {task_id} (arm_a)...", flush=True)
    try:
        res = run_evaluation(
            task_id=task_id,
            arm="arm_a",
            results_dir=RESULTS_DIR,
            run_manifest_path=MANIFEST_PATH,
        )
        elapsed = round(time.time() - started, 1)
        passed = res.get("verification", {}).get("passed", False)
        p_tests = res.get("verification", {}).get("passed_tests", 0)
        t_tests = res.get("verification", {}).get("total_tests", 0)
        pv = res.get("execution", {}).get("protocol_valid", False)
        print(
            f"[{time.strftime('%X')}] Finished {task_id} in {elapsed}s: "
            f"passed={passed} ({p_tests}/{t_tests}) protocol_valid={pv}",
            flush=True,
        )
        return res
    except Exception as exc:
        elapsed = round(time.time() - started, 1)
        print(f"[{time.strftime('%X')}] Error on {task_id} in {elapsed}s: {exc}", flush=True)
        return {"task_id": task_id, "error": str(exc), "status": "failed"}


def main():
    if not os.path.isfile(MANIFEST_PATH):
        raise RuntimeError(f"Manifest not found: {MANIFEST_PATH}")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    pending = [
        task for task in TARGET_TASKS
        if not result_is_final(RESULTS_DIR, task, "arm_a")
    ]
    print(f"Pending tasks ({len(pending)}): {pending}")
    if not pending:
        print("All target tasks are already complete.")
        return

    # Execute with max_workers=2 to balance speed and provider rate limits
    print(f"Executing {len(pending)} tasks with concurrency=2...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(execute_task, t): t for t in pending}
        for future in concurrent.futures.as_completed(futures):
            task_name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Task {task_name} raised an unhandled exception: {e}")

    print("\nBatch execution complete. Verifying results...")


if __name__ == "__main__":
    main()
