#!/usr/bin/env python3
"""
Master Experiment Orchestrator for OMP vs. Multi-CLI Comparison.
Sets up isolated sandboxes, dispatches Arm A or Arm B, and invokes Oracle Verifier.
"""

import os
import sys
import argparse
import json
import shutil
import tempfile
import subprocess
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BENCHMARK_DIR = os.path.join(BASE_DIR, "../../benchmarks/aider-python")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

sys.path.append(os.path.join(BASE_DIR, "verifier"))
from oracle_verifier import verify_task

sys.path.append(os.path.join(BASE_DIR, "runners"))
from arm_a_omp import run_arm_a
from arm_b_multicli import run_arm_b

def setup_workspace(task_meta: dict, arm_name: str) -> str:
    task_id = task_meta["task_id"]
    task_src = os.path.join(BENCHMARK_DIR, "tasks", task_id)
    
    # Create persistent workspace in /tmp
    ws_dir = f"/tmp/harness_eval_{task_id}_{arm_name}_{int(time.time())}"
    os.makedirs(ws_dir, exist_ok=True)
    
    # Copy task files (stub, README, public_test.py)
    for f in os.listdir(task_src):
        src_path = os.path.join(task_src, f)
        dst_path = os.path.join(ws_dir, f)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
            
    # Initialize clean single-commit git repository (anti-cheating ring 3)
    subprocess.run(["git", "init"], cwd=ws_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "BenchmarkRunner"], cwd=ws_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "runner@benchmark.local"], cwd=ws_dir, capture_output=True, check=True)
    subprocess.run(["git", "add", "."], cwd=ws_dir, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial stub"], cwd=ws_dir, capture_output=True, check=True)
    
    return ws_dir

def run_evaluation(task_id: str, arm: str = "both", dry_run: bool = False):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    with open(os.path.join(BENCHMARK_DIR, "manifest.json")) as f:
        manifest = json.load(f)
        
    task_meta = next((item for item in manifest if item["task_id"] == task_id), None)
    if not task_meta:
        print(f"Error: task {task_id} not found in manifest")
        sys.exit(1)
        
    arms_to_run = ["arm_a", "arm_b"] if arm == "both" else [arm]
    
    results = {}
    for a in arms_to_run:
        print(f"\n==========================================")
        print(f"EVALUATING TASK: {task_id} | ARM: {a}")
        print(f"==========================================")
        
        ws = setup_workspace(task_meta, a)
        print(f"Initialized workspace at: {ws}")
        
        if dry_run:
            print("[DRY RUN] Skipping actual LLM invocation.")
            exec_res = {"dry_run": True, "duration": 0.0, "stages": []}
        else:
            if a == "arm_a":
                exec_res = run_arm_a(task_meta, ws)
            else:
                exec_res = run_arm_b(task_meta, ws)
                
        # Run oracle verification
        print("Running Oracle Verification...")
        v_res = verify_task(task_id, ws)
        
        combined = {
            "task_id": task_id,
            "arm": a,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "workspace": ws,
            "execution": exec_res,
            "verification": v_res
        }
        
        res_file = os.path.join(RESULTS_DIR, f"{task_id}_{a}.json")
        with open(res_file, "w") as f:
            json.dump(combined, f, indent=2)
            
        print(f"Result saved to: {res_file}")
        print(f"Outcome: Passed={v_res.get('passed')} | Ratio={v_res.get('ratio')} ({v_res.get('passed_tests')}/{v_res.get('total_tests')})")
        results[a] = combined
        
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run OMP vs Multi-CLI experiment task")
    parser.add_argument("--task", type=str, required=True, help="Task ID from manifest (e.g. grade-school)")
    parser.add_argument("--arm", type=str, choices=["arm_a", "arm_b", "both"], default="both", help="Which arm to evaluate")
    parser.add_argument("--dry-run", action="store_true", help="Set up workspace and verify without calling LLMs")
    
    args = parser.parse_args()
    run_evaluation(args.task, args.arm, args.dry_run)
