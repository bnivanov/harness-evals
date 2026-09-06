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
RATE_CARD = {
    "grok": {"input": 3.00, "cache_read": 0.30, "output": 15.00, "reasoning": 15.00},
    "codex": {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00},
    "agy": {"input": 0.50, "cache_read": 0.05, "output": 2.00, "reasoning": 2.00},
}

def calculate_stage_cost(tool: str, input_tokens: int, cache_read_tokens: int, output_tokens: int, reasoning_tokens: int) -> float:
    rates = RATE_CARD.get(tool, {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00})
    uncached_input = max(0, input_tokens - cache_read_tokens)
    cost = (
        (uncached_input * rates["input"]) +
        (cache_read_tokens * rates["cache_read"]) +
        (output_tokens * rates["output"]) +
        (reasoning_tokens * rates["reasoning"])
    ) / 1_000_000.0
    return round(cost, 6)

def parse_grok_telemetry(stdout_str: str) -> dict:
    try:
        data = json.loads(stdout_str)
        usage = data.get("usage", {})
        inp = usage.get("input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)
        out = usage.get("output_tokens", 0)
        reasoning = usage.get("reasoning_tokens", 0)
        total = usage.get("total_tokens", inp + out)
        num_turns = data.get("num_turns", 1)
        cost = calculate_stage_cost("grok", inp, cache_read, out, reasoning)
        text = data.get("text", "")
        return {
            "num_turns": num_turns,
            "input_tokens": inp,
            "cache_read_tokens": cache_read,
            "cache_write_tokens": cache_write,
            "output_tokens": out,
            "reasoning_tokens": reasoning,
            "total_tokens": total,
            "cost_usd": cost,
            "final_text": text[:1500]
        }
    except Exception as e:
        return {"error": str(e), "num_turns": 1, "input_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0, "cost_usd": 0.0, "final_text": stdout_str[:1500]}

def parse_codex_telemetry(stdout_str: str) -> dict:
    total_inp = 0
    total_cache_read = 0
    total_cache_write = 0
    total_out = 0
    total_reasoning = 0
    num_turns = 0
    text_pieces = []
    
    for line in stdout_str.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        event_type = event.get("type")
        if event_type == "turn.completed":
            num_turns += 1
            usage = event.get("usage", {})
            total_inp += usage.get("input_tokens", 0)
            total_cache_read += usage.get("cached_input_tokens", 0)
            total_cache_write += usage.get("cache_write_input_tokens", 0)
            total_out += usage.get("output_tokens", 0)
            total_reasoning += usage.get("reasoning_output_tokens", 0)
        elif event_type == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message" and item.get("text"):
                text_pieces.append(item["text"])
                
    total_tokens = total_inp + total_out
    cost = calculate_stage_cost("codex", total_inp, total_cache_read, total_out, total_reasoning)
    return {
        "num_turns": num_turns,
        "input_tokens": total_inp,
        "cache_read_tokens": total_cache_read,
        "cache_write_tokens": total_cache_write,
        "output_tokens": total_out,
        "reasoning_tokens": total_reasoning,
        "total_tokens": total_tokens,
        "cost_usd": cost,
        "final_text": "\n".join(text_pieces[-2:]) if text_pieces else ""
    }

def parse_agy_telemetry(stdout_str: str) -> dict:
    try:
        data = json.loads(stdout_str)
        usage = data.get("usage", {})
        inp = usage.get("input_tokens", 0)
        cache_read = usage.get("cache_read_tokens", 0)
        out = usage.get("output_tokens", 0)
        reasoning = usage.get("thinking_tokens", 0)
        total = usage.get("total_tokens", inp + out)
        num_turns = data.get("num_turns", 1)
        cost = calculate_stage_cost("agy", inp, cache_read, out, reasoning)
        text = data.get("response", "")
        return {
            "num_turns": num_turns,
            "input_tokens": inp,
            "cache_read_tokens": cache_read,
            "cache_write_tokens": 0,
            "output_tokens": out,
            "reasoning_tokens": reasoning,
            "total_tokens": total,
            "cost_usd": cost,
            "final_text": text[:1500]
        }
    except Exception as e:
        return {"error": str(e), "num_turns": 1, "input_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0, "cost_usd": 0.0, "final_text": stdout_str[:1500]}

def run_cli_stage(stage_name: str, tool_kind: str, cmd: list, cwd: str, timeout_sec: int = 180) -> dict:
    start_time = time.time()
    print(f"[Arm B - Multi-CLI] Starting {stage_name}: {' '.join(cmd[:3])}...")
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        elapsed = time.time() - start_time
        success = (proc.returncode == 0)
        
        if tool_kind == "grok":
            telemetry = parse_grok_telemetry(proc.stdout)
        elif tool_kind == "codex":
            telemetry = parse_codex_telemetry(proc.stdout)
        elif tool_kind == "agy":
            telemetry = parse_agy_telemetry(proc.stdout)
        else:
            telemetry = {"total_tokens": 0, "cost_usd": 0.0, "final_text": proc.stdout[:500]}
            
        return {
            "stage": stage_name,
            "tool": cmd[0],
            "tool_kind": tool_kind,
            "success": success,
            "returncode": proc.returncode,
            "duration": round(elapsed, 2),
            "telemetry": telemetry,
            "stdout_summary": telemetry["final_text"],
            "stderr": proc.stderr[-1000:]
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[Arm B - Multi-CLI] {stage_name} TIMED OUT after {timeout_sec}s")
        return {
            "stage": stage_name,
            "tool": cmd[0],
            "tool_kind": tool_kind,
            "success": False,
            "returncode": -1,
            "duration": round(elapsed, 2),
            "error": "TIMEOUT",
            "telemetry": {
                "num_turns": 0,
                "input_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "output_tokens": 0,
                "reasoning_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
                "final_text": ""
            }
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
    cmd_s1 = [GROK_BIN, "-p", plan_prompt, "--effort", "xhigh", "--always-approve", "--disable-web-search", "--output-format", "json"]
    s1 = run_cli_stage("1_PLANNER", "grok", cmd_s1, workspace_dir, timeout_sec=300)
    stages.append(s1)
    
    # Stage 2: Worker (Initial Implementation) with Codex CLI (Max reasoning)
    worker_initial_prompt = (
        f"Read 01_PLAN.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Run 'python3 -m unittest public_test.py' to verify basic functionality. "
        f"DO NOT modify public_test.py or any test files."
    )
    cmd_s2 = [CODEX_BIN, "-c", 'model="gpt-5.6-luna"', "-c", 'model_reasoning_effort="max"', "exec", "--dangerously-bypass-approvals-and-sandbox", "--json", worker_initial_prompt]
    s2 = run_cli_stage("2_WORKER_INITIAL", "codex", cmd_s2, workspace_dir, timeout_sec=300)
    stages.append(s2)
    
    # Stage 3: Reviewer with Antigravity / Gemini CLI (Max reasoning: --effort high)
    reviewer_prompt = (
        f"Inspect {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py'. Audit the code for subtle edge cases, algorithmic flaws, "
        f"off-by-one errors, or performance traps. Write your detailed code review findings, failing edge cases, "
        f"and required fixes to 02_REVIEW.md. DO NOT edit code files."
    )
    cmd_s3 = [AGY_BIN, "-p", reviewer_prompt, "--effort", "high", "--dangerously-skip-permissions", "--output-format", "json"]
    s3 = run_cli_stage("3_REVIEWER", "agy", cmd_s3, workspace_dir, timeout_sec=240)
    stages.append(s3)
    
    # Stage 4: Worker (Refinement & Fixes) with Codex CLI (Max reasoning)
    worker_refine_prompt = (
        f"Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        f"Address all review findings, bug reports, and edge-case issues in {impl_file}. "
        f"Run 'python3 -m unittest public_test.py' to verify. "
        f"Ensure all requirements from README.md are satisfied. DO NOT edit test files."
    )
    cmd_s4 = [CODEX_BIN, "-c", 'model="gpt-5.6-luna"', "-c", 'model_reasoning_effort="max"', "exec", "--dangerously-bypass-approvals-and-sandbox", "--json", worker_refine_prompt]
    s4 = run_cli_stage("4_WORKER_REFINE", "codex", cmd_s4, workspace_dir, timeout_sec=300)
    stages.append(s4)
    total_elapsed = time.time() - total_start
    
    total_tokens = sum(s.get("telemetry", {}).get("total_tokens", 0) for s in stages)
    total_cost_usd = round(sum(s.get("telemetry", {}).get("cost_usd", 0.0) for s in stages), 6)
    total_turns = sum(s.get("telemetry", {}).get("num_turns", 0) for s in stages)
    
    return {
        "arm": "arm_b_multicli",
        "task_id": task_id,
        "duration": round(total_elapsed, 2),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "total_turns": total_turns,
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
