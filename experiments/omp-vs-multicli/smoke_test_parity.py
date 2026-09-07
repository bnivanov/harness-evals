#!/usr/bin/env python3
"""Live, immutable model/reasoning parity gate for a frozen confirmatory run."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "runners"))

from experiment_config import (  # noqa: E402
    AGY_BIN,
    CODEX_BIN,
    EFFORT_MATRIX,
    GROK_BIN,
    MODEL_PINS,
    OMP_BIN,
)
from preflight import validate_frozen_manifest  # noqa: E402
from runner_common import (  # noqa: E402
    copy_runtime_file,
    prepare_isolated_agy_home,
    prepare_isolated_codex_home,
    prepare_isolated_grok_home,
    prepare_isolated_omp_agent_dir,
    run_captured_process,
    sandbox_command,
    scrub_workstation_paths,
    sha256_file,
)
from arm_a_omp import parse_omp_telemetry  # noqa: E402
from arm_b_multicli import (  # noqa: E402
    parse_agy_telemetry,
    parse_codex_telemetry,
    parse_grok_telemetry,
)

PROMPT = (
    "Calculate 17 * 19. "
    "Do not call tools. Return only the final numeric answer."
)
CONFIG_OVERLAY = os.path.join(BASE_DIR, "config_overlay.yml")
GUARD_EXTENSION = os.path.join(BASE_DIR, "security", "benchmark_guard.ts")


def run_probe(command, workspace, artifact_prefix, env):
    return run_captured_process(
        sandbox_command(command, workspace),
        workspace,
        120,
        f"{artifact_prefix}.stdout.jsonl",
        f"{artifact_prefix}.stderr.log",
        env,
    )


def omp_probe(role, workspace, artifact_dir, runtime_root):
    runtime = os.path.join(runtime_root, f"omp-{role}")
    os.makedirs(runtime)
    agent_dir = prepare_isolated_omp_agent_dir(runtime)
    config = copy_runtime_file(CONFIG_OVERLAY, runtime)
    guard = copy_runtime_file(GUARD_EXTENSION, runtime)
    guard_log = os.path.join(artifact_dir, f"omp-{role}.guard.ndjson")
    model = MODEL_PINS[role]["arm_a"]
    command = [
        OMP_BIN,
        "--mode", "json",
        "-p", PROMPT,
        f"--model={model}",
        f"--thinking={EFFORT_MATRIX[role]['arm_a']}",
        "--auto-approve",
        "--no-extensions",
        "--no-skills",
        f"--hook={guard}",
        f"--config={config}",
        f"--session-dir={os.path.join(runtime, 'sessions')}",
        "--max-time=120",
        "--tools=read,edit,write,bash,grep,glob",
        "--cwd", workspace,
    ]
    env = os.environ.copy()
    env.update({
        "PI_CODING_AGENT_DIR": agent_dir,
        "BENCHMARK_WORKSPACE": os.path.realpath(workspace),
        "BENCHMARK_GUARD_LOG": guard_log,
    })
    process = run_probe(command, workspace, os.path.join(artifact_dir, f"omp-{role}"), env)
    telemetry = parse_omp_telemetry(process["stdout"], role)
    expected = model.split("/", 1)[-1]
    passed = (
        process["returncode"] == 0
        and expected in telemetry["resolved_models"]
        and telemetry["reasoning_tokens"] > 0
    )
    return {
        "passed": passed,
        "command": command,
        "configured_model": model,
        "configured_effort": EFFORT_MATRIX[role]["arm_a"],
        "resolved_models": telemetry["resolved_models"],
        "reasoning_tokens": telemetry["reasoning_tokens"],
        "returncode": process["returncode"],
        "stdout_trace": process["stdout_trace"],
        "stderr_trace": process["stderr_trace"],
    }


def vendor_probe(role, workspace, artifact_dir, runtime_root):
    if role == "planner":
        provider = "grok"
        home = prepare_isolated_grok_home(os.path.join(runtime_root, "grok"))
        env = os.environ.copy()
        # No nested grok sandbox: --sandbox strict fails to initialize inside
        # the outer sandbox-exec wrapper (RC 1 nested vs RC 0 standalone with
        # reasoning). Containment is the outer seatbelt profile.
        env.update({"HOME": home})
        command = [
            GROK_BIN,
            "-p", PROMPT,
            "--model", MODEL_PINS[role]["arm_b"],
            "--effort", EFFORT_MATRIX[role]["arm_b"],
            "--always-approve",
            "--disable-web-search",
            "--session-id", str(uuid.uuid4()),
            "--output-format", "json",
        ]
        parser = parse_grok_telemetry
    elif role == "reviewer":
        provider = "agy"
        # Machine-bound AGY auth: probe runs with real HOME (see runner_common).
        home = prepare_isolated_agy_home(os.path.join(runtime_root, "agy"))
        env = os.environ.copy()
        env["HOME"] = home

        command = [
            AGY_BIN,
            "-p", PROMPT,
            "--model", MODEL_PINS[role]["arm_b"],
            "--effort", EFFORT_MATRIX[role]["arm_b"],
            "--sandbox",
            "--new-project",
            "--dangerously-skip-permissions",
            "--output-format", "json",
        ]
        parser = parse_agy_telemetry
    else:
        provider = "codex"
        home = prepare_isolated_codex_home(os.path.join(runtime_root, "codex"))
        env = os.environ.copy()
        env["CODEX_HOME"] = home
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
            PROMPT,
        ]
        parser = parse_codex_telemetry

    process = run_probe(command, workspace, os.path.join(artifact_dir, provider), env)
    telemetry = parser(process["stdout"], role)
    resolved = telemetry.get("resolved_models", [])
    if provider == "grok":
        identity_ok = bool(resolved) and all(item.startswith("grok-4.6") for item in resolved)
    elif provider == "agy":
        identity_ok = not resolved or MODEL_PINS[role]["arm_b"] in resolved
    else:
        # Codex JSONL omits the resolved model. --strict-config plus explicit -c
        # is the retained identity proof; preflight separately pins the binary hash.
        identity_ok = True
    passed = process["returncode"] == 0 and identity_ok and telemetry["reasoning_tokens"] > 0
    return {
        "passed": passed,
        "provider": provider,
        "command": command,
        "configured_model": MODEL_PINS[role]["arm_b"],
        "configured_effort": EFFORT_MATRIX[role]["arm_b"],
        "resolved_models": resolved,
        "identity_proof": "resolved telemetry" if resolved else "explicit strict argv + pinned binary",
        "reasoning_tokens": telemetry["reasoning_tokens"],
        "returncode": process["returncode"],
        "stdout_trace": process["stdout_trace"],
        "stderr_trace": process["stderr_trace"],
    }


def run_smoke(run_manifest_path: str) -> dict:
    frozen = validate_frozen_manifest(run_manifest_path)
    run_dir = os.path.dirname(run_manifest_path)
    report_path = os.path.join(run_dir, "smoke_report.json")
    if os.path.exists(report_path):
        raise FileExistsError(f"Smoke report is immutable: {report_path}")
    artifact_dir = os.path.join(run_dir, "smoke_traces")
    os.makedirs(artifact_dir, exist_ok=False)

    with tempfile.TemporaryDirectory(prefix="harness_parity_smoke_") as workspace, tempfile.TemporaryDirectory(
        prefix="harness_parity_runtime_"
    ) as runtime_root:
        with open(os.path.join(workspace, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("Parity smoke workspace. Do not call tools.\n")
        results = {}
        for role in ("planner", "worker", "reviewer"):
            results[role] = {
                "arm_a": omp_probe(role, workspace, artifact_dir, runtime_root),
                "arm_b": vendor_probe(role, workspace, artifact_dir, runtime_root),
            }

    passed = all(side["passed"] for role in results.values() for side in role.values())
    report = {
        "schema_version": 2,
        "status": "pass" if passed else "fail",
        "run_id": frozen["run_id"],
        "run_manifest_path": run_manifest_path,
        "run_manifest_sha256": sha256_file(run_manifest_path),
        "results": results,
    }
    report = scrub_workstation_paths(report)
    with open(report_path, "x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    if not passed:
        raise RuntimeError(f"Parity smoke failed; do not launch benchmark: {report_path}")
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run live parity smoke for a frozen run")
    parser.add_argument("--run-manifest", required=True)
    arguments = parser.parse_args()
    run_smoke(os.path.abspath(arguments.run_manifest))
