#!/usr/bin/env python3
"""Frozen configuration and accounting rules for the confirmatory experiment."""

from __future__ import annotations

import os
from dataclasses import dataclass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
BENCHMARK_DIR = os.path.join(PROJECT_ROOT, "benchmarks", "aider-python")
RUNS_DIR = os.path.join(BASE_DIR, "runs")
LEGACY_PILOT_RESULTS_DIR = os.path.join(BASE_DIR, "results")
HOME = os.path.expanduser("~")
OMP_BIN = os.path.join(HOME, "AgentWork/bin/omp")
GROK_BIN = os.path.join(HOME, ".grok/bin/grok")
CODEX_BIN = os.path.join(HOME, ".local/bin/codex")
AGY_BIN = os.path.join(HOME, ".local/bin/agy")
SANDBOX_EXEC = "/usr/bin/sandbox-exec"

BINARY_PINS = {
    "omp": {"path": OMP_BIN, "version": "omp/18.1.14", "version_args": ["--version"]},
    "grok": {"path": GROK_BIN, "version": "grok 1.0.5 (5115b46bc909) [stable]", "version_args": ["--version"]},
    "codex": {"path": CODEX_BIN, "version": "codex-cli 0.153.4", "version_args": ["--version"]},
    "agy": {"path": AGY_BIN, "version": "1.1.28", "version_args": ["--version"]},
}

MODEL_PINS = {
    "planner": {"arm_a": "xai-oauth/grok-4.6", "arm_b": "grok-4.6"},
    "worker": {"arm_a": "openai-codex/gpt-5.6-luna", "arm_b": "gpt-5.6-luna"},
    "reviewer": {"arm_a": "google-antigravity/gemini-3.8-flash", "arm_b": "gemini-3.8-flash"},
}

# Empirically calibrated effort matrix achieving matched-compute token parity across provider adapters
# (v1 in calibration/*_effort_calibration.json; v2 outcome in PROTOCOL Amendment A §A.6):
# - Planner: OMP medium retained (010 pooled 0.47) with OMP high rejected (v2 pooled 3.22);
#   planner is TOST-only — OMP thinking levels are too coarse to match grok medium at token level.
# - Reviewer: OMP at medium aligns with AGY at medium (v2 4-task pooled ratio 1.15, in band;
#   OMP high re-measured 1.71, out of band; AGY high stays forbidden as uncapped)
# - Worker: both codex arms at max (producing ~2.9k reasoning tokens, 0.4% diff)
EFFORT_MATRIX = {
    "planner": {"arm_a": "medium", "arm_b": "medium"},
    "worker": {"arm_a": "max", "arm_b": "max"},
    "reviewer": {"arm_a": "medium", "arm_b": "medium"},
}

RATE_CARD = {
    "planner": {"input": 3.00, "cache_read": 0.30, "output": 15.00, "reasoning": 15.00},
    "worker": {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00},
    "reviewer": {"input": 0.50, "cache_read": 0.05, "output": 2.00, "reasoning": 2.00},
}

# Decoupled hygiene ceilings (hang protection only, not an SLA cutoff metric).
STAGE_TIMEOUT_SECONDS = int(os.environ.get("STAGE_TIMEOUT_SECONDS", "600"))
TASK_TIMEOUT_SECONDS = int(os.environ.get("TASK_TIMEOUT_SECONDS", "1800"))
EXPECTED_TASK_COUNT = 25
EXPECTED_ORACLE_TEST_CASES = 439

FORBIDDEN_TRACE_MARKERS = (
    "/benchmarks/aider-python/oracle/",
    "/benchmarks/aider-python/tasks/",
    "CHEATED_NETWORK",
)


@dataclass(frozen=True)
class UsageContract:
    """Provider token-field semantics needed for comparable accounting."""

    input_includes_cache: bool
    output_includes_reasoning: bool = True


USAGE_CONTRACTS = {
    "omp": UsageContract(input_includes_cache=False),
    "grok": UsageContract(input_includes_cache=False),
    "codex": UsageContract(input_includes_cache=True),
    "agy": UsageContract(input_includes_cache=False),
}


def normalize_usage(
    role: str,
    provider: str,
    input_tokens: int,
    cache_read_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> dict:
    """Return comparable token totals and rate-card cost for one stage."""

    contract = USAGE_CONTRACTS[provider]
    rates = RATE_CARD[role]
    if contract.input_includes_cache:
        uncached_input = max(0, input_tokens - cache_read_tokens)
        normalized_input = input_tokens
    else:
        uncached_input = input_tokens
        normalized_input = input_tokens + cache_read_tokens

    if contract.output_includes_reasoning:
        visible_output = max(0, output_tokens - reasoning_tokens)
        normalized_output = output_tokens
    else:
        visible_output = output_tokens
        normalized_output = output_tokens + reasoning_tokens

    cost = (
        uncached_input * rates["input"]
        + cache_read_tokens * rates["cache_read"]
        + visible_output * rates["output"]
        + reasoning_tokens * rates["reasoning"]
    ) / 1_000_000.0

    return {
        "uncached_input_tokens": uncached_input,
        "normalized_input_tokens": normalized_input,
        "normalized_output_tokens": normalized_output,
        "normalized_total_tokens": normalized_input + normalized_output,
        "cost_usd": round(cost, 6),
        "input_includes_cache": contract.input_includes_cache,
        "output_includes_reasoning": contract.output_includes_reasoning,
    }


# Shared scratch-file policy (Amendment A, post-010): identical sentence in every
# stage prompt for both arms (PROTOCOL §6.3). Deliberately names no literal
# temp-root path so prompt text cannot self-trigger temp-root trace detection.
SCRATCH_POLICY_SENTENCE = (
    "Write scratch, temp, and test-helper files only inside the current working "
    "directory (or `$TMPDIR` when set); never write outside it."
)

PROMPTS = {
    "1_PLANNER": (
        "You are the Planner agent. Inspect README.md, public_test.py, and the implementation stub. "
        "Design the complete architecture, data structures, algorithms, and edge-case handling for {impl_file}. "
        "Write the implementation guide to 01_PLAN.md. Do not edit {impl_file} or any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests. "
        + SCRATCH_POLICY_SENTENCE
    ),
    "2_WORKER_INITIAL": (
        "You are the Worker agent. Read 01_PLAN.md and README.md. Implement the complete solution in {impl_file}. "
        "Run python3 -m unittest public_test.py for basic verification. Do not modify any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests. "
        + SCRATCH_POLICY_SENTENCE
    ),
    "3_REVIEWER": (
        "You are the Reviewer agent. Inspect {impl_file} against README.md and public_test.py. "
        "Run python3 -m unittest public_test.py. Audit edge cases, algorithmic flaws, off-by-one errors, and performance traps. "
        "Write findings and required fixes to 02_REVIEW.md. Do not edit {impl_file} or any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests. "
        + SCRATCH_POLICY_SENTENCE
    ),
    "4_WORKER_REFINE": (
        "You are the Worker agent in refinement. Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        "Address every review finding in {impl_file}, then run python3 -m unittest public_test.py. "
        "Do not modify any test file. Do not access files outside the current workspace, external networks, "
        + "package registries, canonical solutions, or held-out tests. "
        + SCRATCH_POLICY_SENTENCE
    ),
}

STAGES = (
    ("1_PLANNER", "planner", "01_PLAN.md"),
    ("2_WORKER_INITIAL", "worker", None),
    ("3_REVIEWER", "reviewer", "02_REVIEW.md"),
    ("4_WORKER_REFINE", "worker", None),
)
