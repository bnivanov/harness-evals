#!/usr/bin/env python3
"""
Tier 3 Ablation Runner: Extended-Horizon Grok CLI Evaluation.
Re-runs the 8 tasks where Grok CLI hit the 300s planning ceiling under an expanded 600s ceiling.
"""

import os
import sys
import json
import time

# Set extended timeouts in environment BEFORE importing experiment modules
os.environ["STAGE_TIMEOUT_SECONDS"] = "600"
os.environ["TASK_TIMEOUT_SECONDS"] = "1800"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
RUN_ID = "ablation-extended-grok"
RUN_DIR = os.path.join(RUNS_DIR, RUN_ID)
MANIFEST_PATH = os.path.join(RUN_DIR, "run_manifest.json")
RESULTS_DIR = os.path.join(RUN_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

sys.path.append(BASE_DIR)
from run_task import run_evaluation

TARGET_TASKS = [
    "scale-generator",
    "sgf-parsing",
    "react",
    "rest-api",
    "pov",
    "list-ops",
    "grep",
    "go-counting"
]

def main():
    print("=" * 80)
    print("STARTING TIER 3 ABLATION: EXTENDED-HORIZON GROK CLI (600s CEILING)")
    print(f"Target Tasks ({len(TARGET_TASKS)}): {TARGET_TASKS}")
    print(f"Results Dir: {RESULTS_DIR}")
    print(f"Stage Ceiling: {os.environ['STAGE_TIMEOUT_SECONDS']}s | Task Ceiling: {os.environ['TASK_TIMEOUT_SECONDS']}s")
    print("=" * 80)
    
    results = {}
    for idx, task_id in enumerate(TARGET_TASKS, 1):
        print(f"\n[{idx}/{len(TARGET_TASKS)}] Evaluating {task_id} (Arm B with 600s Grok ceiling)...")
        res_file = os.path.join(RESULTS_DIR, f"{task_id}_arm_b.json")
        if os.path.isfile(res_file):
            print(f"Skipping already completed ablation: {task_id}")
            continue
        try:
            res = run_evaluation(
                task_id=task_id,
                arm="arm_b",
                results_dir=RESULTS_DIR,
                run_manifest_path=MANIFEST_PATH,
                dry_run=False
            )
            v = res.get("verification", {})
            e = res.get("execution", {})
            print(f"Result for {task_id}: Passed={v.get('passed')} | Ratio={v.get('ratio')} ({v.get('passed_tests')}/{v.get('total_tests')}) | Dur={e.get('duration')}s | Cost=${e.get('total_cost_usd', 0.0):.4f}")
            results[task_id] = res
        except Exception as err:
            print(f"Error on {task_id}: {err}")
            
    print("\n" + "=" * 80)
    print("TIER 3 ABLATION RUN COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
