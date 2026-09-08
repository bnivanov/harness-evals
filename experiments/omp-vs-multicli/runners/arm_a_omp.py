#!/usr/bin/env python3
"""Arm A: four-stage multi-model lifecycle in one isolated OMP session."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from experiment_config import (  # noqa: E402
    EFFORT_MATRIX,
    MODEL_PINS,
    PROJECT_ROOT,
    PROMPTS,
    STAGES,
    STAGE_TIMEOUT_SECONDS,
    TASK_TIMEOUT_SECONDS,
    OMP_BIN,
    normalize_usage,
)
from runner_common import (  # noqa: E402
    copy_runtime_file,
    find_throttle_signal,
    prepare_isolated_omp_agent_dir,
    read_guard_events,
    run_captured_process,
    sandbox_command,
    trace_violations,
)

CONFIG_OVERLAY = os.path.join(BASE_DIR, "config_overlay.yml")
GUARD_EXTENSION = os.path.join(BASE_DIR, "security", "benchmark_guard.ts")


def parse_omp_telemetry(stdout: str, role: str) -> dict:
    turn_usages = []
    message_usages = []
    tool_calls = []
    text_responses = []
    thinking_chars = 0
    resolved_models = set()
    providers = set()
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type in {"turn_end", "message_end"}:
            message = event.get("message", event)
            usage = message.get("usage") or event.get("usage") or {}
            if usage:
                target = turn_usages if event_type == "turn_end" else message_usages
                target.append(usage)
            if message.get("model"):
                resolved_models.add(message["model"])
            if message.get("provider"):
                providers.add(message["provider"])
            for content in message.get("content", []):
                if not isinstance(content, dict):
                    continue
                c_type = content.get("type")
                if c_type == "text" and content.get("text"):
                    text_responses.append(content["text"])
                elif c_type == "thinking" and content.get("thinking"):
                    thinking_chars += len(content["thinking"])
        elif event_type == "tool_execution_start":
            tool_calls.append({"tool": event.get("toolName"), "args": event.get("args")})
        elif event_type == "agent_end":
            for message in event.get("messages", []):
                if message.get("role") != "assistant":
                    continue
                for content in message.get("content", []):
                    if not isinstance(content, dict):
                        continue
                    c_type = content.get("type")
                    if c_type == "text" and content.get("text"):
                        text_responses.append(content["text"])
                    elif c_type == "thinking" and content.get("thinking"):
                        thinking_chars += len(content["thinking"])

    # OMP currently emits the same completed message through multiple lifecycle
    # events. turn_end is authoritative; message_end is a compatibility fallback.
    usages = turn_usages or message_usages
    input_tokens = sum(item.get("input", 0) for item in usages)
    cache_read_tokens = sum(item.get("cacheRead", 0) for item in usages)
    cache_write_tokens = sum(item.get("cacheWrite", 0) for item in usages)
    output_tokens = sum(item.get("output", 0) for item in usages)
    reasoning_tokens = sum(item.get("reasoningTokens", 0) for item in usages)
    telemetry_missing = (reasoning_tokens <= 0 and thinking_chars > 0)
    normalized = normalize_usage(
        role,
        "omp",
        input_tokens,
        cache_read_tokens,
        output_tokens,
        reasoning_tokens,
    )
    return {
        "num_turns": len(usages),
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "telemetry_missing": telemetry_missing,
        **normalized,
        "tool_calls_count": len(tool_calls),
        "tool_calls": tool_calls,
        "resolved_models": sorted(resolved_models),
        "resolved_providers": sorted(providers),
        "final_text": "\n".join(text_responses[-2:])[-4000:],
    }


def empty_telemetry(role: str) -> dict:
    return {
        "num_turns": 0,
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        **normalize_usage(role, "omp", 0, 0, 0, 0),
        "tool_calls_count": 0,
        "tool_calls": [],
        "resolved_models": [],
        "resolved_providers": [],
        "final_text": "",
    }


def run_omp_stage(
    stage_name: str,
    role: str,
    prompt: str,
    cwd: str,
    artifact_dir: str,
    runtime_dir: str,
    omp_agent_dir: str,
    config_path: str,
    guard_path: str,
    guard_log: str,
    deadline: float,
    continue_session: bool,
    scratch_dir: str | None = None,
) -> dict:
    model = MODEL_PINS[role]["arm_a"]
    remaining = deadline - time.monotonic()
    timeout = min(STAGE_TIMEOUT_SECONDS, max(0.0, remaining))
    if timeout <= 0:
        return {
            "stage": stage_name,
            "role": role,
            "configured_model": model,
            "configured_effort": EFFORT_MATRIX[role]["arm_a"],
            "success": False,
            "returncode": -1,
            "duration": 0.0,
            "error": "TASK_TIMEOUT",
            "command": [],
            "telemetry": empty_telemetry(role),
            "stdout_summary": "",
            "stderr_summary": "",
            "protocol_violations": [{"code": "TASK_TIMEOUT"}],
        }

    command = [
        OMP_BIN,
        "--mode", "json",
        "-p", prompt,
        f"--model={model}",
        f"--thinking={EFFORT_MATRIX[role]['arm_a']}",
        "--auto-approve",
        "--no-extensions",
        "--no-skills",
        f"--hook={guard_path}",
        f"--config={config_path}",
        f"--session-dir={os.path.join(runtime_dir, 'sessions')}",
        f"--max-time={int(timeout)}",
        "--tools=read,edit,write,bash,grep,glob",
        "--cwd", cwd,
    ]
    if continue_session:
        command.append("--continue")

    env = os.environ.copy()
    env.update({
        "PI_CODING_AGENT_DIR": omp_agent_dir,
        "BENCHMARK_WORKSPACE": os.path.realpath(cwd),
        "BENCHMARK_GUARD_LOG": guard_log,
        "PROJECT_ROOT": os.path.realpath(PROJECT_ROOT),
    })
    if scratch_dir:
        env["BENCHMARK_SCRATCH_DIR"] = os.path.realpath(scratch_dir)
        env["TMPDIR"] = os.path.realpath(scratch_dir)
    stdout_path = os.path.join(artifact_dir, f"{stage_name}.stdout.jsonl")
    stderr_path = os.path.join(artifact_dir, f"{stage_name}.stderr.log")
    print(f"[Arm A - OMP] Starting {stage_name} with {model}...")
    process = run_captured_process(
        sandbox_command(command, cwd, scratch_dir),
        cwd,
        timeout,
        stdout_path,
        stderr_path,
        env,
    )
    telemetry = parse_omp_telemetry(process["stdout"], role)
    violations = trace_violations(process["stdout"], process["stderr"])
    expected_resolved = model.split("/", 1)[-1]
    if telemetry["resolved_models"] and expected_resolved not in telemetry["resolved_models"]:
        violations.append({
            "code": "MODEL_MISMATCH",
            "expected": expected_resolved,
            "actual": telemetry["resolved_models"],
        })
    if not telemetry["resolved_models"]:
        violations.append({"code": "MODEL_ID_UNRECORDED", "expected": expected_resolved})
    if telemetry["reasoning_tokens"] <= 0:
        violations.append({"code": "NO_REASONING_TOKENS"})
    if telemetry.get("telemetry_missing"):
        violations.append({"code": "REASONING_TELEMETRY_MISSING"})
    if process["timed_out"]:
        violations.append({"code": "STAGE_TIMEOUT"})

    success = process["returncode"] == 0 and not process["timed_out"]
    return {
        "stage": stage_name,
        "role": role,
        "configured_model": model,
        "configured_effort": EFFORT_MATRIX[role]["arm_a"],
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


def run_arm_a(task_meta: dict, workspace_dir: str, artifact_dir: str, scratch_dir: str | None = None, pilot_early_stop: bool = False) -> dict:
    runtime_dir = tempfile.mkdtemp(prefix=f"harness_runtime_{task_meta['task_id']}_arm_a_")
    try:
        omp_agent_dir = prepare_isolated_omp_agent_dir(runtime_dir)
        config_path = copy_runtime_file(CONFIG_OVERLAY, runtime_dir)
        guard_path = copy_runtime_file(GUARD_EXTENSION, runtime_dir)
        guard_log = os.path.join(artifact_dir, "benchmark_guard.ndjson")
        deadline = time.monotonic() + TASK_TIMEOUT_SECONDS
        started = time.monotonic()
        stages = []
        violations = []

        for index, (stage_name, role, required_artifact) in enumerate(STAGES):
            stage = run_omp_stage(
                stage_name,
                role,
                PROMPTS[stage_name].format(impl_file=task_meta["impl_file"]),
                workspace_dir,
                artifact_dir,
                runtime_dir,
                omp_agent_dir,
                config_path,
                guard_path,
                guard_log,
                deadline,
                continue_session=index > 0,
                scratch_dir=scratch_dir,
            )
            stages.append(stage)
            violations.extend({"stage": stage_name, **item} for item in stage["protocol_violations"])
            throttle = find_throttle_signal(stage)
            if throttle is not None:
                violations.append({"stage": stage_name, "code": "RATE_LIMITED", "signal": throttle})
                # Throttle break is UNCONDITIONAL (pilot and matrix alike):
                # later stages would spend quota against a throttled vendor.
                # Unlike the C3 handoff break it needs no pilot_early_stop.
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
                # C3: pilot-only within-pair stop. Guard TPs are visible only
                # via the post-loop guard-log read, so they still run out the
                # pair and drop post-hoc. Never enabled on the matrix path.
                if pilot_early_stop:
                    break

        guard_events = read_guard_events(guard_log)
        violations.extend({"stage": "guard", **event} for event in guard_events)
        total_duration = round(time.monotonic() - started, 2)
        if total_duration > TASK_TIMEOUT_SECONDS + 2:
            violations.append({"stage": "task", "code": "TASK_TIMEOUT"})

        return {
            "arm": "arm_a_omp",
            "task_id": task_meta["task_id"],
            "duration": total_duration,
            "normalized_total_tokens": sum(
                stage["telemetry"]["normalized_total_tokens"] for stage in stages
            ),
            "total_cost_usd": round(sum(stage["telemetry"]["cost_usd"] for stage in stages), 6),
            "total_turns": sum(stage["telemetry"]["num_turns"] for stage in stages),
            "total_tool_calls": sum(stage["telemetry"]["tool_calls_count"] for stage in stages),
            "protocol_valid": not violations,
            "protocol_violations": violations,
            "guard_log": guard_log,
            "stages": stages,
        }
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: arm_a_omp.py <task_id> <workspace_dir> <artifact_dir>")
    with open(os.path.join(BASE_DIR, "../../benchmarks/aider-python/manifest.json")) as handle:
        manifest = json.load(handle)
    metadata = next(item for item in manifest if item["task_id"] == sys.argv[1])
    print(json.dumps(run_arm_a(metadata, sys.argv[2], sys.argv[3]), indent=2))
