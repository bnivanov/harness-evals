#!/usr/bin/env python3
"""
Arm A Runner: Unified Multi-Model Coordination in Oh My Pi (OMP).
Orchestrates Grok (Recon) -> Claude (Plan) -> Codex/GPT (Implement) -> Gemini (Verify)
within a single OMP workspace using OMP tools and shared memory/state.
"""

import os
import sys
import time
import subprocess
import json

OMP_BIN = "/Users/agentlab/AgentWork/bin/omp"

def run_omp_stage(stage_name: str, model: str, prompt: str, cwd: str, timeout_sec: int = 180, continue_session: bool = False) -> dict:
    start_time = time.time()
    cmd = [
        OMP_BIN,
        "-p", prompt,
        f"--model={model}",
        "--thinking=max",
        "--auto-approve",
        "--no-extensions",
        "--tools=read,edit,write,bash,grep,glob",  # disable web_search
        "--cwd", cwd
    ]
    if continue_session:
        cmd.append("--continue")
    
    print(f"[Arm A - OMP] Starting {stage_name} with {model}...")
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        elapsed = time.time() - start_time
        success = (proc.returncode == 0)
        return {
            "stage": stage_name,
            "model": model,
            "success": success,
            "returncode": proc.returncode,
            "duration": round(elapsed, 2),
            "stdout": proc.stdout[-1500:],
            "stderr": proc.stderr[-1000:]
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[Arm A - OMP] {stage_name} TIMED OUT after {timeout_sec}s")
        return {
            "stage": stage_name,
            "model": model,
            "success": False,
            "returncode": -1,
            "duration": round(elapsed, 2),
            "error": "TIMEOUT"
        }

def run_arm_a(task_meta: dict, workspace_dir: str) -> dict:
    task_id = task_meta["task_id"]
    impl_file = task_meta["impl_file"]
    
    total_start = time.time()
    stages = []
    
    # Stage 1: Planner with Grok 4.6 (Max reasoning)
    plan_prompt = (
        f"You are the Planner agent. Inspect README.md and public_test.py. "
        f"Design the complete architecture, data structures, and edge-case handling for {impl_file}. "
        f"Write your step-by-step implementation guide and specifications to 01_PLAN.md and local://plan.md. "
        f"DO NOT edit {impl_file} or any code files."
    )
    s1 = run_omp_stage("1_PLANNER", "xai-oauth/grok-4.6", plan_prompt, workspace_dir, timeout_sec=180, continue_session=False)
    stages.append(s1)
    
    # Stage 2: Worker (Initial Implementation) with Codex GPT-5.6 Luna (Max reasoning)
    worker_initial_prompt = (
        f"You are the Worker agent. Read 01_PLAN.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Use bash to run 'python3 -m unittest public_test.py' to verify basic sanity. "
        f"DO NOT modify public_test.py or any test files."
    )
    s2 = run_omp_stage("2_WORKER_INITIAL", "openai-codex/gpt-5.6-luna", worker_initial_prompt, workspace_dir, timeout_sec=240, continue_session=True)
    stages.append(s2)
    
    # Stage 3: Reviewer with Gemini 3.8 Flash (Max reasoning)
    reviewer_prompt = (
        f"You are the Reviewer & Quality Audit agent. Inspect {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py' in bash. Audit the code for subtle edge cases, algorithmic flaws, "
        f"off-by-one errors, or performance traps. Write your detailed code review findings, failing edge cases, "
        f"and required fixes to 02_REVIEW.md and local://review.md. DO NOT edit code files."
    )
    s3 = run_omp_stage("3_REVIEWER", "google-antigravity/gemini-3.8-flash", reviewer_prompt, workspace_dir, timeout_sec=180, continue_session=True)
    stages.append(s3)
    
    # Stage 4: Worker (Refinement & Fixes) with Codex GPT-5.6 Luna (Max reasoning)
    worker_refine_prompt = (
        f"You are the Worker agent in refinement phase. Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        f"Address all review findings, bug reports, and edge-case issues in {impl_file}. "
        f"Use bash to run 'python3 -m unittest public_test.py' to verify. "
        f"Ensure all requirements from README.md are satisfied. DO NOT edit test files."
    )
    s4 = run_omp_stage("4_WORKER_REFINE", "openai-codex/gpt-5.6-luna", worker_refine_prompt, workspace_dir, timeout_sec=240, continue_session=True)
    stages.append(s4)
    total_elapsed = time.time() - total_start
    
    return {
        "arm": "arm_a_omp",
        "task_id": task_id,
        "duration": round(total_elapsed, 2),
        "stages": stages
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: arm_a_omp.py <task_id> <workspace_dir>")
        sys.exit(1)
    with open(os.path.join(os.path.dirname(__file__), "../../../benchmarks/aider-python/manifest.json")) as f:
        manifest = json.load(f)
    meta = next(item for item in manifest if item["task_id"] == sys.argv[1])
    res = run_arm_a(meta, sys.argv[2])
    print(json.dumps(res, indent=2))
