#!/usr/bin/env python3
"""
Arm B Runner: Disaggregated Multi-CLI Swarm.
Chains specialized standalone CLIs:
1. Grok CLI (Recon) -> 01_RECON.md
2. Claude Code CLI (Plan) -> 02_PLAN.md
3. Codex CLI (Implement) -> edits implementation file
4. Gemini / Antigravity CLI (Verify) -> reviews & fixes
"""

import os
import sys
import time
import subprocess
import json

GROK_BIN = "/Users/agentlab/.grok/bin/grok"
CODEX_BIN = "/Users/agentlab/.local/bin/codex"
AGY_BIN = "/Users/agentlab/.local/bin/agy"
def run_cli_stage(stage_name: str, cmd: list, cwd: str, timeout_sec: int = 180) -> dict:
    start_time = time.time()
    print(f"[Arm B - Multi-CLI] Starting {stage_name}: {' '.join(cmd[:3])}...")
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        elapsed = time.time() - start_time
        success = (proc.returncode == 0)
        return {
            "stage": stage_name,
            "tool": cmd[0],
            "success": success,
            "returncode": proc.returncode,
            "duration": round(elapsed, 2),
            "stdout": proc.stdout[-1500:],
            "stderr": proc.stderr[-1000:]
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[Arm B - Multi-CLI] {stage_name} TIMED OUT after {timeout_sec}s")
        return {
            "stage": stage_name,
            "tool": cmd[0],
            "success": False,
            "returncode": -1,
            "duration": round(elapsed, 2),
            "error": "TIMEOUT"
        }

def run_arm_b(task_meta: dict, workspace_dir: str) -> dict:
    task_id = task_meta["task_id"]
    impl_file = task_meta["impl_file"]
    
    total_start = time.time()
    stages = []
    
    # Stage 1: Planner with Grok CLI (Max reasoning)
    plan_prompt = (
        f"Inspect README.md and public_test.py. "
        f"Design the complete architecture, data structures, and edge-case handling for {impl_file}. "
        f"Write your step-by-step implementation guide and specifications to 01_PLAN.md. "
        f"DO NOT edit {impl_file} or any code files."
    )
    cmd_s1 = [GROK_BIN, "-p", plan_prompt, "--always-approve", "--disable-web-search"]
    s1 = run_cli_stage("1_PLANNER", cmd_s1, workspace_dir, timeout_sec=180)
    stages.append(s1)
    
    # Stage 2: Worker (Initial Implementation) with Codex CLI (Max reasoning)
    worker_initial_prompt = (
        f"Read 01_PLAN.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Run 'python3 -m unittest public_test.py' to verify basic functionality. "
        f"DO NOT modify public_test.py or any test files."
    )
    cmd_s2 = [CODEX_BIN, "-c", 'model_reasoning_effort="high"', "exec", "--dangerously-bypass-approvals-and-sandbox", worker_initial_prompt]
    s2 = run_cli_stage("2_WORKER_INITIAL", cmd_s2, workspace_dir, timeout_sec=240)
    stages.append(s2)
    
    # Stage 3: Reviewer with Antigravity / Gemini CLI (Max reasoning: --effort high)
    reviewer_prompt = (
        f"Inspect {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py'. Audit the code for subtle edge cases, algorithmic flaws, "
        f"off-by-one errors, or performance traps. Write your detailed code review findings, failing edge cases, "
        f"and required fixes to 02_REVIEW.md. DO NOT edit code files."
    )
    cmd_s3 = [AGY_BIN, "-p", reviewer_prompt, "--effort", "high", "--dangerously-skip-permissions"]
    s3 = run_cli_stage("3_REVIEWER", cmd_s3, workspace_dir, timeout_sec=180)
    stages.append(s3)
    
    # Stage 4: Worker (Refinement & Fixes) with Codex CLI (Max reasoning)
    worker_refine_prompt = (
        f"Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        f"Address all review findings, bug reports, and edge-case issues in {impl_file}. "
        f"Run 'python3 -m unittest public_test.py' to verify. "
        f"Ensure all requirements from README.md are satisfied. DO NOT edit test files."
    )
    cmd_s4 = [CODEX_BIN, "-c", 'model_reasoning_effort="high"', "exec", "--dangerously-bypass-approvals-and-sandbox", worker_refine_prompt]
    s4 = run_cli_stage("4_WORKER_REFINE", cmd_s4, workspace_dir, timeout_sec=240)
    stages.append(s4)
    total_elapsed = time.time() - total_start
    
    return {
        "arm": "arm_b_multicli",
        "task_id": task_id,
        "duration": round(total_elapsed, 2),
        "stages": stages
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: arm_b_multicli.py <task_id> <workspace_dir>")
        sys.exit(1)
    with open(os.path.join(os.path.dirname(__file__), "../../../benchmarks/aider-python/manifest.json")) as f:
        manifest = json.load(f)
    meta = next(item for item in manifest if item["task_id"] == sys.argv[1])
    res = run_arm_b(meta, sys.argv[2])
    print(json.dumps(res, indent=2))
