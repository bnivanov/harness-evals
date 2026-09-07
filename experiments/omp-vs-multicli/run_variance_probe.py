#!/usr/bin/env python3
"""Variance probe measuring Stage 1 (Grok 4.6 Planner) latency spread across repeated runs.

Evaluates k=3 contemporaneous repeats on 'grep' and 'list-ops' across:
- Arm A: Oh My Pi (in-process harness, Grok 4.6, native tool bindings)
- Arm B: Multi-CLI (standalone Grok 1.0.5 CLI, subshell execution)

Uses a 600s ceiling to observe natural completion distributions without hard-killing at 300s.
"""

from __future__ import annotations

import json
import os
import shutil
import statistics as st
import subprocess
import sys
import tempfile
import time
import uuid

# Ensure 600s ceiling for natural completion observation
os.environ["STAGE_TIMEOUT_SECONDS"] = "600"
os.environ["TASK_TIMEOUT_SECONDS"] = "600"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "runners"))
sys.path.insert(0, os.path.join(BASE_DIR, "verifier"))

import experiment_config as cfg  # noqa: E402
import runner_common as rc  # noqa: E402
from arm_a_omp import (  # noqa: E402
    CONFIG_OVERLAY,
    GUARD_EXTENSION,
    copy_runtime_file,
    prepare_isolated_omp_agent_dir,
    read_guard_events,
    run_omp_stage,
)
from arm_b_multicli import (  # noqa: E402
    prepare_isolated_grok_home,
    run_cli_stage,
)

# Enforce overrides in imported modules
cfg.STAGE_TIMEOUT_SECONDS = 600
cfg.TASK_TIMEOUT_SECONDS = 600

PROBE_RUN_DIR = os.path.join(BASE_DIR, "runs", "variance-probe-001")
RESULTS_DIR = os.path.join(PROBE_RUN_DIR, "results")
TRACES_DIR = os.path.join(PROBE_RUN_DIR, "traces")
TARGET_TASKS = ["grep", "list-ops"]
REPEATS = 3
ARMS = ["arm_a", "arm_b"]


def setup_task_workspace(task_meta: dict, prefix: str) -> str:
    task_src = os.path.join(cfg.BENCHMARK_DIR, "tasks", task_meta["task_id"])
    workspace = tempfile.mkdtemp(prefix=f"probe_{task_meta['task_id']}_{prefix}_")
    for name in os.listdir(task_src):
        source = os.path.join(task_src, name)
        if os.path.isfile(source):
            shutil.copy2(source, os.path.join(workspace, name))

    commands = (
        ["git", "init"],
        ["git", "config", "user.name", "BenchmarkRunner"],
        ["git", "config", "user.email", "runner@benchmark.local"],
        ["git", "add", "."],
        ["git", "commit", "-m", "initial stub"],
    )
    for command in commands:
        subprocess.run(command, cwd=workspace, capture_output=True, text=True, check=True)
    return workspace


def run_stage1_arm_a(task_meta: dict, workspace_dir: str, artifact_dir: str) -> dict:
    os.makedirs(artifact_dir, exist_ok=True)
    runtime_dir = tempfile.mkdtemp(prefix=f"probe_runtime_{task_meta['task_id']}_a_")
    try:
        omp_agent_dir = prepare_isolated_omp_agent_dir(runtime_dir)
        config_path = copy_runtime_file(CONFIG_OVERLAY, runtime_dir)
        guard_path = copy_runtime_file(GUARD_EXTENSION, runtime_dir)
        guard_log = os.path.join(artifact_dir, "benchmark_guard.ndjson")
        deadline = time.monotonic() + 600.0

        stage = run_omp_stage(
            stage_name="1_PLANNER",
            role="planner",
            prompt=cfg.PROMPTS["1_PLANNER"].format(impl_file=task_meta["impl_file"]),
            cwd=workspace_dir,
            artifact_dir=artifact_dir,
            runtime_dir=runtime_dir,
            omp_agent_dir=omp_agent_dir,
            config_path=config_path,
            guard_path=guard_path,
            guard_log=guard_log,
            deadline=deadline,
            continue_session=False,
        )
        guard_events = read_guard_events(guard_log)
        plan_path = os.path.join(workspace_dir, "01_PLAN.md")
        plan_exists = os.path.isfile(plan_path) and os.path.getsize(plan_path) > 0
        plan_bytes = os.path.getsize(plan_path) if plan_exists else 0
        if plan_exists:
            shutil.copy2(plan_path, os.path.join(artifact_dir, "01_PLAN.md"))

        return {
            "arm": "arm_a",
            "stage": stage,
            "guard_events": guard_events,
            "plan_created": plan_exists,
            "plan_bytes": plan_bytes,
        }
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def run_stage1_arm_b(task_meta: dict, workspace_dir: str, artifact_dir: str) -> dict:
    os.makedirs(artifact_dir, exist_ok=True)
    runtime_dir = tempfile.mkdtemp(prefix=f"probe_runtime_{task_meta['task_id']}_b_")
    try:
        grok_home = prepare_isolated_grok_home(runtime_dir)
        deadline = time.monotonic() + 600.0
        prompt = cfg.PROMPTS["1_PLANNER"].format(impl_file=task_meta["impl_file"])
        env = os.environ.copy()
        env["HOME"] = grok_home

        command = [
            cfg.GROK_BIN,
            "-p", prompt,
            "--model", cfg.MODEL_PINS["planner"]["arm_b"],
            "--effort", cfg.EFFORT_MATRIX["planner"]["arm_b"],
            "--always-approve",
            "--disable-web-search",
            "--session-id", str(uuid.uuid4()),
            "--output-format", "json",
        ]

        stage = run_cli_stage(
            stage_name="1_PLANNER",
            role="planner",
            provider="grok",
            command=command,
            cwd=workspace_dir,
            artifact_dir=artifact_dir,
            deadline=deadline,
            env=env,
        )
        plan_path = os.path.join(workspace_dir, "01_PLAN.md")
        plan_exists = os.path.isfile(plan_path) and os.path.getsize(plan_path) > 0
        plan_bytes = os.path.getsize(plan_path) if plan_exists else 0
        if plan_exists:
            shutil.copy2(plan_path, os.path.join(artifact_dir, "01_PLAN.md"))

        return {
            "arm": "arm_b",
            "stage": stage,
            "guard_events": [],
            "plan_created": plan_exists,
            "plan_bytes": plan_bytes,
        }
    finally:
        shutil.rmtree(runtime_dir, ignore_errors=True)


def execute_probe() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(TRACES_DIR, exist_ok=True)

    with open(os.path.join(cfg.BENCHMARK_DIR, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    task_map = {t["task_id"]: t for t in manifest}

    total_runs = len(TARGET_TASKS) * REPEATS * len(ARMS)
    current_run = 0
    records = []

    print("=" * 80)
    print("WORKFLOW BENCH EXPERIMENT 2: STAGE 1 PLANNER VARIANCE PROBE")
    print(f"Tasks: {TARGET_TASKS} | Repeats: {REPEATS} | Arms: {ARMS} | Total Runs: {total_runs}")
    print(f"Ceiling: 600.0s (measuring natural completion spread and <300s SLA compliance)")
    print("=" * 80)

    for r in range(1, REPEATS + 1):
        for task_id in TARGET_TASKS:
            task_meta = task_map[task_id]
            for arm in ARMS:
                current_run += 1
                run_tag = f"{task_id}_{arm}_rep{r}"
                artifact_dir = os.path.join(TRACES_DIR, task_id, f"{arm}_rep{r}")
                print(f"\n[{current_run}/{total_runs}] Executing {run_tag}...")

                ws = setup_task_workspace(task_meta, f"{arm}_rep{r}")
                started_wall = time.time()
                try:
                    if arm == "arm_a":
                        res = run_stage1_arm_a(task_meta, ws, artifact_dir)
                    else:
                        res = run_stage1_arm_b(task_meta, ws, artifact_dir)

                    stg = res["stage"]
                    tel = stg["telemetry"]
                    dur = round(stg["duration"], 2)
                    success = stg["success"]
                    plan_created = res["plan_created"]
                    plan_bytes = res["plan_bytes"]
                    under_300 = dur <= 300.0 and success and plan_created

                    record = {
                        "task_id": task_id,
                        "arm": arm,
                        "repeat": r,
                        "duration": dur,
                        "success": success,
                        "completed_under_300s": under_300,
                        "plan_created": plan_created,
                        "plan_bytes": plan_bytes,
                        "returncode": stg["returncode"],
                        "error": stg.get("error"),
                        "input_tokens": tel.get("input_tokens", 0),
                        "cache_read_tokens": tel.get("cache_read_tokens", 0),
                        "output_tokens": tel.get("output_tokens", 0),
                        "reasoning_tokens": tel.get("reasoning_tokens", 0),
                        "cost_usd": tel.get("cost_usd", 0.0),
                        "tool_calls_count": tel.get("tool_calls_count", 0),
                        "num_turns": tel.get("num_turns", 0),
                        "violations": [v["code"] for v in stg.get("protocol_violations", [])],
                        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    records.append(record)

                    # Save single result
                    result_path = os.path.join(RESULTS_DIR, f"{run_tag}.json")
                    with open(result_path, "w", encoding="utf-8") as f:
                        json.dump(record, f, indent=2)

                    status_str = "OK" if success and plan_created else "FAIL"
                    sla_str = "<300s YES" if under_300 else "<300s NO"
                    print(
                        f"  -> {status_str} in {dur:.1f}s ({sla_str}) | "
                        f"Plan: {plan_bytes}B | "
                        f"Reasoning Toks: {tel.get('reasoning_tokens', 0)} | "
                        f"Cost: ${tel.get('cost_usd', 0.0):.4f}"
                    )
                finally:
                    shutil.rmtree(ws, ignore_errors=True)

    # Compile and display aggregate summary
    print("\n" + "=" * 80)
    print("PROBE RESULTS SUMMARY TABLE")
    print("=" * 80)
    header = f"{'Task':<10} {'Repeat':<8} {'Arm':<8} {'Duration':<10} {'<300s?':<10} {'Success':<10} {'Plan Bytes':<12} {'Reasoning Tok':<14} {'Cost ($)':<10}"
    print(header)
    print("-" * len(header))
    for rec in records:
        print(
            f"{rec['task_id']:<10} "
            f"rep{rec['repeat']:<5} "
            f"{rec['arm']:<8} "
            f"{rec['duration']:>7.1f}s   "
            f"{str(rec['completed_under_300s']):<10} "
            f"{str(rec['success']):<10} "
            f"{rec['plan_bytes']:>8} B   "
            f"{rec['reasoning_tokens']:>12}   "
            f"${rec['cost_usd']:>7.4f}"
        )

    # Compute statistics per task and arm
    summary_stats = {}
    print("\n" + "=" * 80)
    print("AGGREGATE LATENCY & SPREAD ANALYSIS")
    print("=" * 80)

    for task_id in TARGET_TASKS:
        summary_stats[task_id] = {}
        print(f"\n### Task: {task_id}")
        for arm in ARMS:
            arm_recs = [r for r in records if r["task_id"] == task_id and r["arm"] == arm]
            durs = [r["duration"] for r in arm_recs]
            under_300_count = sum(1 for r in arm_recs if r["completed_under_300s"])
            mean_dur = st.mean(durs)
            std_dur = st.stdev(durs) if len(durs) > 1 else 0.0
            min_dur = min(durs)
            max_dur = max(durs)
            spread = max_dur - min_dur

            summary_stats[task_id][arm] = {
                "durations": durs,
                "mean_duration": round(mean_dur, 2),
                "stdev_duration": round(std_dur, 2),
                "min_duration": round(min_dur, 2),
                "max_duration": round(max_dur, 2),
                "spread_duration": round(spread, 2),
                "completed_under_300s": f"{under_300_count}/{len(arm_recs)}",
                "mean_reasoning_tokens": round(st.mean(r["reasoning_tokens"] for r in arm_recs), 1),
                "mean_cost_usd": round(st.mean(r["cost_usd"] for r in arm_recs), 4),
            }

            arm_name = "Arm A (OMP)" if arm == "arm_a" else "Arm B (Multi-CLI)"
            print(
                f"  {arm_name:<20}: "
                f"Mean = {mean_dur:6.1f}s (±{std_dur:5.1f}s) | "
                f"Min = {min_dur:5.1f}s | Max = {max_dur:5.1f}s | Spread = {spread:5.1f}s | "
                f"<300s = {under_300_count}/{len(arm_recs)}"
            )

    summary_path = os.path.join(PROBE_RUN_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "config": {
                    "tasks": TARGET_TASKS,
                    "repeats": REPEATS,
                    "arms": ARMS,
                    "stage": "1_PLANNER",
                    "stage_timeout": 600,
                },
                "summary": summary_stats,
                "records": records,
            },
            f,
            indent=2,
        )
    print(f"\nWrote full probe summary to: {summary_path}")


if __name__ == "__main__":
    execute_probe()
