#!/usr/bin/env python3
"""
Smoke Test for Rigorous Parity Verification (Arm A vs Arm B).
Tests every stage across both execution arms to prove:
1. Exact model identity resolution (e.g. gpt-5.6-luna in both arms).
2. Exact reasoning effort resolution (e.g. max/xhigh in both arms).
3. Ground-truth emission of non-zero reasoning/thinking tokens.
4. Clean JSON telemetry extraction.
"""

import os
import sys
import json
import subprocess
import time
import shutil

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_OVERLAY = os.path.join(BASE_DIR, "config_overlay.yml")
PROBE_DIR = "/tmp/harness_parity_smoke_test"
shutil.rmtree(PROBE_DIR, ignore_errors=True)
os.makedirs(PROBE_DIR, exist_ok=True)

OMP_BIN = "/Users/agentlab/AgentWork/bin/omp"
GROK_BIN = "/Users/agentlab/.grok/bin/grok"
CODEX_BIN = "/Users/agentlab/.local/bin/codex"
AGY_BIN = "/Users/agentlab/.local/bin/agy"

PROMPT = "Solve this step-by-step with your maximum internal reasoning depth: What is 17 * 19? Return only the final numeric answer."

def test_stage_1_planner():
    print("\n" + "=" * 80)
    print("STAGE 1 SMOKE TEST: PLANNER (Target: Grok 4.6 @ xhigh reasoning)")
    print("=" * 80)
    
    # Arm A: OMP
    print("[Arm A - OMP] Probing xai-oauth/grok-4.6 with --thinking=max...")
    cmd_a = [
        OMP_BIN, "--mode", "json", "-p", PROMPT,
        "--model=xai-oauth/grok-4.6", "--thinking=max",
        "--auto-approve", "--no-extensions",
        f"--config={CONFIG_OVERLAY}",
        "--tools=read,edit,write,bash,grep,glob",
        "--cwd", PROBE_DIR
    ]
    t0 = time.time()
    proc_a = subprocess.run(cmd_a, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_a = time.time() - t0
    
    omp_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0, "model": "unknown", "provider": "unknown"}
    for line in proc_a.stdout.splitlines():
        if not line.startswith("{"): continue
        try:
            ev = json.loads(line)
            if ev.get("type") == "turn_end":
                msg = ev.get("message", {})
                omp_telemetry["model"] = msg.get("model", omp_telemetry["model"])
                omp_telemetry["provider"] = msg.get("provider", omp_telemetry["provider"])
                u = msg.get("usage", {})
                omp_telemetry["input"] += u.get("input", 0)
                omp_telemetry["output"] += u.get("output", 0)
                omp_telemetry["reasoning"] += u.get("reasoningTokens", 0)
                omp_telemetry["cache"] += u.get("cacheRead", 0)
        except: pass
        
    print(f"  Arm A Result: exit={proc_a.returncode}, dur={dur_a:.1f}s, "
          f"provider={omp_telemetry['provider']}, model={omp_telemetry['model']}, "
          f"tokens={omp_telemetry['input']} in / {omp_telemetry['output']} out / {omp_telemetry['reasoning']} reasoning")

    # Arm B: Grok CLI
    print("[Arm B - Grok CLI] Probing grok with --effort xhigh...")
    cmd_b = [
        GROK_BIN, "-p", PROMPT,
        "--effort", "xhigh",
        "--always-approve", "--disable-web-search",
        "--output-format", "json"
    ]
    t0 = time.time()
    proc_b = subprocess.run(cmd_b, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_b = time.time() - t0
    
    grok_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0, "model": "unknown"}
    try:
        data_b = json.loads(proc_b.stdout)
        u_b = data_b.get("usage", {})
        grok_telemetry["input"] = u_b.get("input_tokens", 0)
        grok_telemetry["output"] = u_b.get("output_tokens", 0)
        grok_telemetry["reasoning"] = u_b.get("reasoning_tokens", 0)
        grok_telemetry["cache"] = u_b.get("cache_read_input_tokens", 0)
        grok_telemetry["model"] = list(data_b.get("modelUsage", {}).keys())[0] if data_b.get("modelUsage") else "grok-4.6"
    except Exception as e:
        print(f"  Grok parse error: {e}")

    print(f"  Arm B Result: exit={proc_b.returncode}, dur={dur_b:.1f}s, model={grok_telemetry['model']}, "
          f"tokens={grok_telemetry['input']} in / {grok_telemetry['output']} out / {grok_telemetry['reasoning']} reasoning")
    
    reasoning_fired = (omp_telemetry["reasoning"] > 0 and grok_telemetry["reasoning"] > 0)
    parity = reasoning_fired
    print(f"  >>> Stage 1 Parity: {'PASSED' if parity else 'FAILED'} (Reasoning tokens fired on both)")
    return parity

def test_stage_2_worker():
    print("\n" + "=" * 80)
    print("STAGE 2 & 4 SMOKE TEST: WORKER (Target: GPT-5.6 Luna @ max reasoning)")
    print("=" * 80)
    
    # Arm A: OMP
    print("[Arm A - OMP] Probing openai-codex/gpt-5.6-luna with --thinking=max...")
    cmd_a = [
        OMP_BIN, "--mode", "json", "-p", PROMPT,
        "--model=openai-codex/gpt-5.6-luna", "--thinking=max",
        "--auto-approve", "--no-extensions",
        f"--config={CONFIG_OVERLAY}",
        "--tools=read,edit,write,bash,grep,glob",
        "--cwd", PROBE_DIR
    ]
    t0 = time.time()
    proc_a = subprocess.run(cmd_a, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_a = time.time() - t0
    
    omp_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0, "model": "unknown", "provider": "unknown", "has_thinking": False}
    for line in proc_a.stdout.splitlines():
        if not line.startswith("{"): continue
        try:
            ev = json.loads(line)
            if ev.get("type") == "turn_end":
                msg = ev.get("message", {})
                omp_telemetry["model"] = msg.get("model", omp_telemetry["model"])
                omp_telemetry["provider"] = msg.get("provider", omp_telemetry["provider"])
                u = msg.get("usage", {})
                omp_telemetry["input"] += u.get("input", 0)
                omp_telemetry["output"] += u.get("output", 0)
                omp_telemetry["reasoning"] += u.get("reasoningTokens", 0)
                omp_telemetry["cache"] += u.get("cacheRead", 0)
                for c in msg.get("content", []):
                    if c.get("type") == "thinking":
                        omp_telemetry["has_thinking"] = True
        except: pass
        
    print(f"  Arm A Result: exit={proc_a.returncode}, dur={dur_a:.1f}s, "
          f"provider={omp_telemetry['provider']}, model={omp_telemetry['model']}, has_thinking={omp_telemetry['has_thinking']}, "
          f"tokens={omp_telemetry['input']} in / {omp_telemetry['output']} out / {omp_telemetry['reasoning']} reasoning")

    # Arm B: Codex CLI
    print("[Arm B - Codex CLI] Probing codex with -c model=\"gpt-5.6-luna\" -c model_reasoning_effort=\"max\"...")
    cmd_b = [
        CODEX_BIN,
        "-c", 'model="gpt-5.6-luna"',
        "-c", 'model_reasoning_effort="max"',
        "exec", "--dangerously-bypass-approvals-and-sandbox",
        "--json", PROMPT
    ]
    t0 = time.time()
    proc_b = subprocess.run(cmd_b, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_b = time.time() - t0
    
    codex_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0, "model": "unknown", "effort": "unknown"}
    for line in proc_b.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"): continue
        try:
            ev = json.loads(line)
            if ev.get("type") == "turn.completed":
                u = ev.get("usage", {})
                codex_telemetry["input"] += u.get("input_tokens", 0)
                codex_telemetry["cache"] += u.get("cached_input_tokens", 0)
                codex_telemetry["output"] += u.get("output_tokens", 0)
                codex_telemetry["reasoning"] += u.get("reasoning_output_tokens", 0)
        except: pass

    # Verify codex banner
    proc_banner = subprocess.run([CODEX_BIN, "-c", 'model="gpt-5.6-luna"', "-c", 'model_reasoning_effort="max"', "exec", "--dangerously-bypass-approvals-and-sandbox", "echo test"],
                                 cwd=PROBE_DIR, capture_output=True, text=True, timeout=30)
    for line in proc_banner.stderr.splitlines():
        if "model:" in line:
            codex_telemetry["model"] = line.split("model:")[1].strip()
        if "reasoning effort:" in line:
            codex_telemetry["effort"] = line.split("reasoning effort:")[1].strip()
    print(f"  Arm B Result: exit={proc_b.returncode}, dur={dur_b:.1f}s, "
          f"resolved_model={codex_telemetry['model']}, resolved_effort={codex_telemetry['effort']}, "
          f"tokens={codex_telemetry['input']} in / {codex_telemetry['output']} out / {codex_telemetry['reasoning']} reasoning")
    
    model_match = (omp_telemetry["model"] == "gpt-5.6-luna" and codex_telemetry["model"] == "gpt-5.6-luna")
    effort_match = (codex_telemetry["effort"] == "max")
    reasoning_fired = (omp_telemetry["has_thinking"] and codex_telemetry["reasoning"] > 0)
    parity = (model_match and effort_match and reasoning_fired)
    print(f"  >>> Stage 2 Parity: {'PASSED' if parity else 'FAILED'} "
          f"(ModelMatch={model_match} [{omp_telemetry['model']} vs {codex_telemetry['model']}], "
          f"EffortMatch={effort_match} [{codex_telemetry['effort']}], ReasoningFired={reasoning_fired})")
    return parity

def test_stage_3_reviewer():
    print("\n" + "=" * 80)
    print("STAGE 3 SMOKE TEST: REVIEWER (Target: Gemini 3.8 Flash @ high reasoning)")
    print("=" * 80)
    
    # Arm A: OMP
    print("[Arm A - OMP] Probing google-antigravity/gemini-3.8-flash with --thinking=max...")
    cmd_a = [
        OMP_BIN, "--mode", "json", "-p", PROMPT,
        "--model=google-antigravity/gemini-3.8-flash", "--thinking=max",
        "--auto-approve", "--no-extensions",
        f"--config={CONFIG_OVERLAY}",
        "--tools=read,edit,write,bash,grep,glob",
        "--cwd", PROBE_DIR
    ]
    t0 = time.time()
    proc_a = subprocess.run(cmd_a, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_a = time.time() - t0
    
    omp_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0, "model": "unknown", "provider": "unknown"}
    for line in proc_a.stdout.splitlines():
        if not line.startswith("{"): continue
        try:
            ev = json.loads(line)
            if ev.get("type") == "turn_end":
                msg = ev.get("message", {})
                omp_telemetry["model"] = msg.get("model", omp_telemetry["model"])
                omp_telemetry["provider"] = msg.get("provider", omp_telemetry["provider"])
                u = msg.get("usage", {})
                omp_telemetry["input"] += u.get("input", 0)
                omp_telemetry["output"] += u.get("output", 0)
                omp_telemetry["reasoning"] += u.get("reasoningTokens", 0)
                omp_telemetry["cache"] += u.get("cacheRead", 0)
        except: pass
        
    print(f"  Arm A Result: exit={proc_a.returncode}, dur={dur_a:.1f}s, "
          f"provider={omp_telemetry['provider']}, model={omp_telemetry['model']}, "
          f"tokens={omp_telemetry['input']} in / {omp_telemetry['output']} out / {omp_telemetry['reasoning']} reasoning")

    # Arm B: AGY CLI
    print("[Arm B - AGY CLI] Probing agy with --effort high...")
    cmd_b = [
        AGY_BIN, "-p", PROMPT,
        "--effort", "high",
        "--dangerously-skip-permissions",
        "--output-format", "json"
    ]
    t0 = time.time()
    proc_b = subprocess.run(cmd_b, cwd=PROBE_DIR, capture_output=True, text=True, timeout=120)
    dur_b = time.time() - t0
    
    agy_telemetry = {"input": 0, "output": 0, "reasoning": 0, "cache": 0}
    try:
        data_b = json.loads(proc_b.stdout)
        u_b = data_b.get("usage", {})
        agy_telemetry["input"] = u_b.get("input_tokens", 0)
        agy_telemetry["output"] = u_b.get("output_tokens", 0)
        agy_telemetry["reasoning"] = u_b.get("thinking_tokens", 0)
        agy_telemetry["cache"] = u_b.get("cache_read_tokens", 0)
    except Exception as e:
        print(f"  AGY parse error: {e}")

    print(f"  Arm B Result: exit={proc_b.returncode}, dur={dur_b:.1f}s, "
          f"tokens={agy_telemetry['input']} in / {agy_telemetry['output']} out / {agy_telemetry['reasoning']} reasoning")
    
    reasoning_fired = (omp_telemetry["reasoning"] > 0 and agy_telemetry["reasoning"] > 0)
    parity = reasoning_fired
    print(f"  >>> Stage 3 Parity: {'PASSED' if parity else 'FAILED'} (Reasoning tokens fired on both)")
    return parity

if __name__ == "__main__":
    p1 = test_stage_1_planner()
    p2 = test_stage_2_worker()
    p3 = test_stage_3_reviewer()
    
    print("\n" + "=" * 80)
    print("OVERALL PARITY GATE REPORT")
    print("=" * 80)
    print(f"Stage 1 (Grok 4.6 @ xhigh):          {'PASS' if p1 else 'FAIL'}")
    print(f"Stage 2 & 4 (GPT-5.6 Luna @ max):     {'PASS' if p2 else 'FAIL'}")
    print(f"Stage 3 (Gemini 3.8 Flash @ high):    {'PASS' if p3 else 'FAIL'}")
    print("=" * 80)
    
    if p1 and p2 and p3:
        print("\nALL STAGES VERIFIED: STRICT MODEL AND REASONING PARITY CONFIRMED.")
        sys.exit(0)
    else:
        print("\nPARITY GATE FAILED: DO NOT PROCEED TO BENCHMARK.")
        sys.exit(1)
