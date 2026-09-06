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
CONFIG_OVERLAY = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config_overlay.yml"))
# Pre-registered Reference Rate Card (PROTOCOL.md Section 5) in USD per 1M tokens
RATE_CARD = {
    "xai-oauth/grok-4.6": {"input": 3.00, "cache_read": 0.30, "output": 15.00, "reasoning": 15.00},
    "openai-codex/gpt-5.6-luna": {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00},
    "google-antigravity/gemini-3.8-flash": {"input": 0.50, "cache_read": 0.05, "output": 2.00, "reasoning": 2.00},
}

def calculate_stage_cost(model: str, input_tokens: int, cache_read_tokens: int, output_tokens: int, reasoning_tokens: int) -> float:
    rates = RATE_CARD.get(model, {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00})
    uncached_input = max(0, input_tokens - cache_read_tokens)
    cost = (
        (uncached_input * rates["input"]) +
        (cache_read_tokens * rates["cache_read"]) +
        (output_tokens * rates["output"]) +
        (reasoning_tokens * rates["reasoning"])
    ) / 1_000_000.0
    return round(cost, 6)

def parse_omp_telemetry(stdout_str: str, model: str) -> dict:
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    total_reasoning = 0
    total_tokens = 0
    tool_calls = []
    text_responses = []
    num_turns = 0
    
    for line in stdout_str.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        event_type = event.get("type")
        
        if event_type == "turn_end":
            num_turns += 1
            msg = event.get("message", {})
            usage = msg.get("usage", {})
            total_input += usage.get("input", 0)
            total_output += usage.get("output", 0)
            total_cache_read += usage.get("cacheRead", 0)
            total_cache_write += usage.get("cacheWrite", 0)
            total_reasoning += usage.get("reasoningTokens", 0)
            total_tokens += usage.get("totalTokens", 0)
            
            for c in msg.get("content", []):
                if c.get("type") == "text" and c.get("text"):
                    text_responses.append(c["text"])
                    
        elif event_type == "tool_execution_end":
            tool_calls.append({
                "tool": event.get("toolName"),
                "is_error": event.get("isError", False)
            })
            
        elif event_type == "agent_end":
            for m in event.get("messages", []):
                if m.get("role") == "assistant":
                    for c in m.get("content", []):
                        if c.get("type") == "text" and c.get("text"):
                            text_responses.append(c["text"])
                            
    final_text = "\n".join(text_responses[-2:]) if text_responses else ""
    cost_usd = calculate_stage_cost(model, total_input, total_cache_read, total_output, total_reasoning)
    
    return {
        "num_turns": num_turns,
        "input_tokens": total_input,
        "cache_read_tokens": total_cache_read,
        "cache_write_tokens": total_cache_write,
        "output_tokens": total_output,
        "reasoning_tokens": total_reasoning,
        "total_tokens": total_tokens if total_tokens > 0 else (total_input + total_output),
        "cost_usd": cost_usd,
        "tool_calls_count": len(tool_calls),
        "tool_calls": tool_calls,
        "final_text": final_text[:1500]
    }

def run_omp_stage(stage_name: str, model: str, prompt: str, cwd: str, timeout_sec: int = 180, continue_session: bool = False) -> dict:
    start_time = time.time()
    cmd = [
        OMP_BIN,
        "--mode", "json",
        "-p", prompt,
        f"--model={model}",
        "--thinking=max",
        "--auto-approve",
        "--no-extensions",
        f"--config={CONFIG_OVERLAY}",
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
        telemetry = parse_omp_telemetry(proc.stdout, model)
        return {
            "stage": stage_name,
            "model": model,
            "success": success,
            "returncode": proc.returncode,
            "duration": round(elapsed, 2),
            "telemetry": telemetry,
            "stdout_summary": telemetry["final_text"],
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
                "tool_calls_count": 0,
                "tool_calls": [],
                "final_text": ""
            }
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
    s1 = run_omp_stage("1_PLANNER", "xai-oauth/grok-4.6", plan_prompt, workspace_dir, timeout_sec=300, continue_session=False)
    stages.append(s1)
    # Stage 2: Worker (Initial Implementation) with Codex GPT-5.6 Luna (Max reasoning)
    worker_initial_prompt = (
        f"You are the Worker agent. Read 01_PLAN.md and README.md. "
        f"Implement the complete, working solution in {impl_file}. "
        f"Use bash to run 'python3 -m unittest public_test.py' to verify basic sanity. "
        f"DO NOT modify public_test.py or any test files."
    )
    s2 = run_omp_stage("2_WORKER_INITIAL", "openai-codex/gpt-5.6-luna", worker_initial_prompt, workspace_dir, timeout_sec=300, continue_session=True)
    stages.append(s2)
    # Stage 3: Reviewer with Gemini 3.8 Flash (Max reasoning)
    reviewer_prompt = (
        f"You are the Reviewer & Quality Audit agent. Inspect {impl_file} against README.md and public_test.py. "
        f"Run 'python3 -m unittest public_test.py' in bash. Audit the code for subtle edge cases, algorithmic flaws, "
        f"off-by-one errors, or performance traps. Write your detailed code review findings, failing edge cases, "
        f"and required fixes to 02_REVIEW.md and local://review.md. DO NOT edit code files."
    )
    s3 = run_omp_stage("3_REVIEWER", "google-antigravity/gemini-3.8-flash", reviewer_prompt, workspace_dir, timeout_sec=240, continue_session=True)
    stages.append(s3)
    # Stage 4: Worker (Refinement & Fixes) with Codex GPT-5.6 Luna (Max reasoning)
    worker_refine_prompt = (
        f"You are the Worker agent in refinement phase. Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        f"Address all review findings, bug reports, and edge-case issues in {impl_file}. "
        f"Use bash to run 'python3 -m unittest public_test.py' to verify. "
        f"Ensure all requirements from README.md are satisfied. DO NOT edit test files."
    )
    s4 = run_omp_stage("4_WORKER_REFINE", "openai-codex/gpt-5.6-luna", worker_refine_prompt, workspace_dir, timeout_sec=300, continue_session=True)
    stages.append(s4)
    total_elapsed = time.time() - total_start
    
    total_tokens = sum(s.get("telemetry", {}).get("total_tokens", 0) for s in stages)
    total_cost_usd = round(sum(s.get("telemetry", {}).get("cost_usd", 0.0) for s in stages), 6)
    total_tool_calls = sum(s.get("telemetry", {}).get("tool_calls_count", 0) for s in stages)
    total_turns = sum(s.get("telemetry", {}).get("num_turns", 0) for s in stages)
    
    return {
        "arm": "arm_a_omp",
        "task_id": task_id,
        "duration": round(total_elapsed, 2),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "total_turns": total_turns,
        "total_tool_calls": total_tool_calls,
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
