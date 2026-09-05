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
CLAUDE_BIN = "/Users/agentlab/.local/bin/claude"
CODEX_BIN = "/Users/agentlab/.local/bin/codex"
GEMINI_BIN = "/Users/agentlab/.local/bin/gemini"

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
    
    # Stage 1: Recon with Grok CLI
    recon_prompt = (
        f"Inspect README.md and public_test.py. "
        f"Identify all functions and classes that must be implemented in {impl_file}. "
        f"Write your analysis and required specifications to 01_RECON.md. DO NOT edit {impl_file}."
    )
    cmd_s1 = [GROK_BIN, "-p", recon_prompt, "--always-approve"]
    s1 = run_cli_stage("1_RECON", cmd_s1, workspace_dir, timeout_sec=150)
    stages.append(s1)
    
    # Stage 2: Plan with Claude Code
    plan_prompt = (
        f"Read 01_RECON.md and README.md. "
        f"Design the exact algorithms, state structures, and edge-case handling for {impl_file}. "
        f"Write the step-by-step implementation guide to 02_PLAN.md. DO NOT edit code files."
    )
    cmd_s2 = [CLAUDE_BIN, "-p", plan_prompt, "--dangerously-skip-permissions"]
    s2 = run_cli_stage("2_PLAN", cmd_s2, workspace_dir, timeout_sec=150)
    stages.append(s2)
    
    # Stage 3: Implement with Codex CLI
    impl_prompt = (
        f"Read 02_PLAN.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Run 'python3 -m unittest public_test.py' to verify basic functionality. "
        f"DO NOT modify public_test.py."
    )
    cmd_s3 = [CODEX_BIN, "exec", impl_prompt, "--dangerously-bypass-approvals-and-sandbox"]
    s3 = run_cli_stage("3_IMPLEMENT", cmd_s3, workspace_dir, timeout_sec=240)
    stages.append(s3)
    
    # Stage 4: Verify with Gemini CLI
    verify_prompt = (
        f"Review {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py'. Fix any bugs or syntax errors in {impl_file}. "
        f"Ensure all requirements are met. DO NOT edit test files."
    )
    cmd_s4 = [GEMINI_BIN, "-p", verify_prompt, "-y"]
    s4 = run_cli_stage("4_VERIFY", cmd_s4, workspace_dir, timeout_sec=180)
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
