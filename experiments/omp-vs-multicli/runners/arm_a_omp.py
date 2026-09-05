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

def run_omp_stage(stage_name: str, model: str, prompt: str, cwd: str, timeout_sec: int = 180) -> dict:
    start_time = time.time()
    cmd = [
        OMP_BIN,
        "-p", prompt,
        f"--model={model}",
        "--tools=read,edit,write,bash,grep,glob",  # disable web_search
        "--cwd", cwd
    ]
    
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
    
    # Stage 1: Recon with Grok
    recon_prompt = (
        f"You are the Reconnaissance agent. Inspect README.md and public_test.py. "
        f"Identify all functions and classes that must be implemented in {impl_file}. "
        f"Write your analysis and requirements to local://recon.md. DO NOT edit {impl_file}."
    )
    s1 = run_omp_stage("1_RECON", "xai-oauth/grok-4.6", recon_prompt, workspace_dir, timeout_sec=150)
    stages.append(s1)
    
    # Stage 2: Plan with Claude
    plan_prompt = (
        f"You are the Architectural Planning agent. Read local://recon.md and README.md. "
        f"Design the algorithm, state representation, and edge-case handling for {impl_file}. "
        f"Write a step-by-step implementation guide to local://plan.md. DO NOT edit code files."
    )
    s2 = run_omp_stage("2_PLAN", "anthropic/claude-3-7-sonnet", plan_prompt, workspace_dir, timeout_sec=150)
    stages.append(s2)
    
    # Stage 3: Implement with Codex / GPT
    impl_prompt = (
        f"You are the Implementation agent. Read local://plan.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Use bash to run 'python3 -m unittest public_test.py' to verify basic sanity. "
        f"DO NOT modify public_test.py or any test files."
    )
    s3 = run_omp_stage("3_IMPLEMENT", "openai-codex/gpt-5.6-luna", impl_prompt, workspace_dir, timeout_sec=240)
    stages.append(s3)
    
    # Stage 4: Verify with Gemini
    verify_prompt = (
        f"You are the Verification & Quality agent. Review {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py' in bash. Fix any bugs or syntax errors in {impl_file}. "
        f"Ensure all requirements from README.md are satisfied. DO NOT edit test files."
    )
    s4 = run_omp_stage("4_VERIFY", "google/gemini-3.8-flash", verify_prompt, workspace_dir, timeout_sec=180)
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
