#!/usr/bin/env python3
"""Arm B: four isolated vendor CLI processes joined by disk handoffs."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import uuid

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from experiment_config import (  # noqa: E402
    AGY_BIN,
    CODEX_BIN,
    EFFORT_MATRIX,
    GROK_BIN,
    MODEL_PINS,
    PROMPTS,
    STAGES,
    STAGE_TIMEOUT_SECONDS,
    TASK_TIMEOUT_SECONDS,
    normalize_usage,
)
from runner_common import (  # noqa: E402
    find_throttle_signal,
    prepare_isolated_agy_home,
    prepare_isolated_codex_home,
    prepare_isolated_grok_home,
    run_captured_process,
    sandbox_command,
    temp_root_write_violations,
    trace_violations,
)


def parse_grok_telemetry(stdout: str, role: str) -> dict:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as error:
        data = {"parse_error": str(error), "text": stdout[-4000:]}
    usage = data.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    cache_read_tokens = usage.get("cache_read_input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    reasoning_tokens = usage.get("reasoning_tokens", 0)
    # Sign-off change 2: grok CLI output carries response text only — no
    # reasoning-text stream exists — so zero accounted reasoning tokens with
    # text present is vendor accounting (arm failure), never a telemetry blip.
    # Length is kept as output_text_chars for reporting only.
    output_text_chars = len(data.get("text", "") or "")
    normalized = normalize_usage(
        role, "grok", input_tokens, cache_read_tokens, output_tokens, reasoning_tokens
    )
    return {
        "num_turns": data.get("num_turns", 0),
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": usage.get("cache_creation_input_tokens", 0),
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_text_chars": output_text_chars,
        "telemetry_missing": False,
        **normalized,
        "resolved_models": sorted(data.get("modelUsage", {}).keys()),
        "session_id": data.get("sessionId"),
        "request_id": data.get("requestId"),
        "parse_error": data.get("parse_error"),
        "final_text": data.get("text", "")[-4000:],
    }


def parse_codex_telemetry(stdout: str, role: str) -> dict:
    input_tokens = cache_read_tokens = cache_write_tokens = 0
    output_tokens = reasoning_tokens = num_turns = 0
    messages = []
    resolved_models = set()
    tool_calls = []
    parse_errors = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        if event.get("model"):
            resolved_models.add(event["model"])
        if event.get("type") == "turn.completed":
            num_turns += 1
            usage = event.get("usage", {})
            input_tokens += usage.get("input_tokens", 0)
            cache_read_tokens += usage.get("cached_input_tokens", 0)
            cache_write_tokens += usage.get("cache_write_input_tokens", 0)
            output_tokens += usage.get("output_tokens", 0)
            reasoning_tokens += usage.get("reasoning_output_tokens", 0)
        elif event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(item["text"])
            elif item.get("type") in {"command_execution", "mcp_tool_call", "file_change"}:
                tool_calls.append(item)
    normalized = normalize_usage(
        role, "codex", input_tokens, cache_read_tokens, output_tokens, reasoning_tokens
    )
    # Sign-off change 2: 50/50 sampled codex traces carry only
    # agent_message/command_execution/file_change items — no reasoning stream —
    # so the response-text length is reporting-only, never retryable.
    output_text_chars = sum(len(message) for message in messages)
    return {
        "num_turns": num_turns,
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_text_chars": output_text_chars,
        "telemetry_missing": False,
        **normalized,
        "resolved_models": sorted(resolved_models),
        "tool_calls_count": len(tool_calls),
        "tool_calls": tool_calls,
        "parse_errors": parse_errors,
        "final_text": "\n".join(messages[-2:])[-4000:],
    }


def parse_agy_telemetry(stdout: str, role: str) -> dict:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as error:
        data = {"parse_error": str(error), "response": stdout[-4000:]}
    usage = data.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    cache_read_tokens = usage.get("cache_read_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    reasoning_tokens = usage.get("thinking_tokens", 0)
    normalized = normalize_usage(
        role, "agy", input_tokens, cache_read_tokens, output_tokens, reasoning_tokens
    )
    resolved = data.get("model") or data.get("model_id")
    response_text = data.get("response", data.get("text", "")) or ""
    # Sign-off change 2: agy exposes thinking *tokens* in usage but no reasoning
    # text stream; response length is reporting-only, never retryable.
    output_text_chars = len(response_text)
    return {
        "num_turns": data.get("num_turns", 0),
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": usage.get("cache_write_tokens", 0),
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "output_text_chars": output_text_chars,
        "telemetry_missing": False,
        **normalized,
        "resolved_models": [resolved] if resolved else [],
        "parse_error": data.get("parse_error"),
        "final_text": data.get("response", data.get("text", ""))[-4000:],
    }


def empty_telemetry(role: str, provider: str) -> dict:
    return {
        "num_turns": 0,
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "output_text_chars": 0,
        "telemetry_missing": False,
        **normalize_usage(role, provider, 0, 0, 0, 0),
        "resolved_models": [],
        "final_text": "",
    }


def run_cli_stage(
    stage_name: str,
    role: str,
    provider: str,
    command: list[str],
    cwd: str,
    artifact_dir: str,
    deadline: float,
    env: dict[str, str],
    scratch_dir: str | None = None,
) -> dict:
    remaining = deadline - time.monotonic()
    timeout = min(STAGE_TIMEOUT_SECONDS, max(0.0, remaining))
    configured_model = MODEL_PINS[role]["arm_b"]
    configured_effort = EFFORT_MATRIX[role]["arm_b"]
    if timeout <= 0:
        return {
            "stage": stage_name,
            "role": role,
            "provider": provider,
            "configured_model": configured_model,
            "configured_effort": configured_effort,
            "success": False,
            "returncode": -1,
            "duration": 0.0,
            "error": "TASK_TIMEOUT",
            "command": command,
            "telemetry": empty_telemetry(role, provider),
            "stdout_summary": "",
            "stderr_summary": "",
            "protocol_violations": [{"code": "TASK_TIMEOUT"}],
        }

    stdout_path = os.path.join(artifact_dir, f"{stage_name}.stdout.jsonl")
    stderr_path = os.path.join(artifact_dir, f"{stage_name}.stderr.log")
    print(f"[Arm B - Multi-CLI] Starting {stage_name} with {provider}...")
    process = run_captured_process(
        sandbox_command(command, cwd, scratch_dir),
        cwd,
        timeout,
        stdout_path,
        stderr_path,
        env,
    )
    if provider == "grok":
        telemetry = parse_grok_telemetry(process["stdout"], role)
    elif provider == "codex":
        telemetry = parse_codex_telemetry(process["stdout"], role)
    else:
        telemetry = parse_agy_telemetry(process["stdout"], role)

    violations = trace_violations(process["stdout"], process["stderr"])
    # C2: temp-root write attempts carry the Arm A guard-TP disposition.
    violations.extend(temp_root_write_violations(process["stdout"], process["stderr"]))
    if telemetry.get("parse_error"):
        violations.append({"code": "TELEMETRY_PARSE_ERROR", "detail": telemetry["parse_error"]})
    if telemetry["reasoning_tokens"] <= 0:
        violations.append({"code": "NO_REASONING_TOKENS"})
    # Sign-off change 2: Arm B never emits REASONING_TELEMETRY_MISSING (no
    # reasoning-text stream in any vendor CLI). Zero reasoning tokens with text
    # stays an arm failure via NO_REASONING_TOKENS above; retry is Arm-A-only.
    if process["timed_out"]:
        violations.append({"code": "STAGE_TIMEOUT"})
    if provider == "grok":
        actual = telemetry["resolved_models"]
        if not actual or not all(model.startswith("grok-4.6") for model in actual):
            violations.append({"code": "MODEL_MISMATCH", "expected": configured_model, "actual": actual})

    success = process["returncode"] == 0 and not process["timed_out"]
    return {
        "stage": stage_name,
        "role": role,
        "provider": provider,
        "configured_model": configured_model,
        "configured_effort": configured_effort,
        "success": success,
        "returncode": process["returncode"],
        "duration": process["duration"],
        "error": "TIMEOUT" if process["timed_out"] else None,
        "command": command,
        "telemetry": telemetry,
        "stdout_trace": process["stdout_trace"],
        "stderr_trace": process["stderr_trace"],
        "stdout_summary": telemetry["final_text"],
        "stderr_summary": process["stderr"][-2000:],
        "protocol_violations": violations,
    }


def run_arm_b(task_meta: dict, workspace_dir: str, artifact_dir: str, scratch_dir: str | None = None, pilot_early_stop: bool = False) -> dict:
    runtime_dir = tempfile.mkdtemp(prefix=f"harness_runtime_{task_meta['task_id']}_arm_b_")
    try:
        grok_home = prepare_isolated_grok_home(runtime_dir)
        codex_home = prepare_isolated_codex_home(runtime_dir)
        agy_home = prepare_isolated_agy_home(runtime_dir)
        deadline = time.monotonic() + TASK_TIMEOUT_SECONDS
        started = time.monotonic()
        stages = []
        violations = []

        for stage_name, role, required_artifact in STAGES:
            prompt = PROMPTS[stage_name].format(impl_file=task_meta["impl_file"])
            env = os.environ.copy()
            if scratch_dir:
                env["BENCHMARK_SCRATCH_DIR"] = os.path.realpath(scratch_dir)
                env["TMPDIR"] = os.path.realpath(scratch_dir)
            if role == "planner":
                provider = "grok"
                env["HOME"] = grok_home
                # Single containment layer (outer sandbox-exec): grok's internal
                # --sandbox strict cannot initialize nested (see smoke evidence).
                command = [
                    GROK_BIN,
                    "-p", prompt,
                    "--model", MODEL_PINS[role]["arm_b"],
                    "--effort", EFFORT_MATRIX[role]["arm_b"],
                    "--always-approve",
                    "--disable-web-search",
                    "--session-id", str(uuid.uuid4()),
                    "--output-format", "json",
                ]
            elif role == "reviewer":
                provider = "agy"
                # agy_home is the real HOME: AGY auth is machine-bound, so the
                # reviewer runs with real auth under --new-project + sandbox.
                env["HOME"] = agy_home

                command = [
                    AGY_BIN,
                    "-p", prompt,
                    "--model", MODEL_PINS[role]["arm_b"],
                    "--effort", EFFORT_MATRIX[role]["arm_b"],
                    "--sandbox",
                    "--new-project",
                    "--dangerously-skip-permissions",
                    "--output-format", "json",
                ]
            else:
                provider = "codex"
                env["CODEX_HOME"] = codex_home
                command = [
                    CODEX_BIN,
                    "-c", f'model="{MODEL_PINS[role]["arm_b"]}"',
                    "-c", f'model_reasoning_effort="{EFFORT_MATRIX[role]["arm_b"]}"',
                    "exec",
                    "--dangerously-bypass-approvals-and-sandbox",
                    "--skip-git-repo-check",
                    "--ignore-user-config",
                    "--ephemeral",
                    "--strict-config",
                    "--json",
                    prompt,
                ]

            stage = run_cli_stage(
                stage_name, role, provider, command, workspace_dir, artifact_dir, deadline, env, scratch_dir=scratch_dir
            )
            stages.append(stage)
            violations.extend({"stage": stage_name, **item} for item in stage["protocol_violations"])
            throttle = find_throttle_signal(stage)
            if throttle is not None:
                violations.append({"stage": stage_name, "code": "RATE_LIMITED", "signal": throttle})
                # Unconditional (see arm_a_omp): never spend into a throttle.
                break
            if not stage["success"]:
                violations.append({"stage": stage_name, "code": "STAGE_FAILED"})
            handoff_missing = required_artifact and not os.path.isfile(os.path.join(workspace_dir, required_artifact))
            if handoff_missing:
                violations.append({
                    "stage": stage_name,
                    "code": "MISSING_HANDOFF",
                    "path": required_artifact,
                })
                # C3: pilot-only within-pair stop. Never enabled on the matrix
                # path (run_task.py uses the default False).
                if pilot_early_stop:
                    break

        duration = round(time.monotonic() - started, 2)
        if duration > TASK_TIMEOUT_SECONDS + 2:
            violations.append({"stage": "task", "code": "TASK_TIMEOUT"})
        return {
            "arm": "arm_b_multicli",
            "task_id": task_meta["task_id"],
            "duration": duration,
            "normalized_total_tokens": sum(
                stage["telemetry"]["normalized_total_tokens"] for stage in stages
            ),
            "total_cost_usd": round(sum(stage["telemetry"]["cost_usd"] for stage in stages), 6),
            "total_turns": sum(stage["telemetry"]["num_turns"] for stage in stages),
            "total_tool_calls": sum(stage["telemetry"].get("tool_calls_count", 0) for stage in stages),
            "protocol_valid": not violations,
            "protocol_violations": violations,
            "stages": stages,
        }
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: arm_b_multicli.py <task_id> <workspace_dir> <artifact_dir>")
    with open(os.path.join(BASE_DIR, "../../benchmarks/aider-python/manifest.json")) as handle:
        manifest = json.load(handle)
    metadata = next(item for item in manifest if item["task_id"] == sys.argv[1])
    print(json.dumps(run_arm_b(metadata, sys.argv[2], sys.argv[3]), indent=2))
