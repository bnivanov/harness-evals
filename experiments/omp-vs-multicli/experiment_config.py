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

OMP_BIN = "/Users/agentlab/AgentWork/bin/omp"
GROK_BIN = "/Users/agentlab/.grok/bin/grok"
CODEX_BIN = "/Users/agentlab/.local/bin/codex"
AGY_BIN = "/Users/agentlab/.local/bin/agy"
SANDBOX_EXEC = "/usr/bin/sandbox-exec"

BINARY_PINS = {
    "omp": {"path": OMP_BIN, "version": "omp/18.1.12", "version_args": ["--version"]},
    "grok": {"path": GROK_BIN, "version": "grok 1.0.5 (5115b46bc909) [stable]", "version_args": ["--version"]},
    "codex": {"path": CODEX_BIN, "version": "codex-cli 0.153.4", "version_args": ["--version"]},
    "agy": {"path": AGY_BIN, "version": "1.1.27", "version_args": ["--version"]},
}

MODEL_PINS = {
    "planner": {"arm_a": "xai-oauth/grok-4.6", "arm_b": "grok-4.6"},
    "worker": {"arm_a": "openai-codex/gpt-5.6-luna", "arm_b": "gpt-5.6-luna"},
    "reviewer": {"arm_a": "google-antigravity/gemini-3.8-flash", "arm_b": "gemini-3.8-flash-high"},
}

EFFORT_PINS = {
    "omp": "max",
    "grok": "xhigh",
    "codex": "max",
    "agy": "high",
}

RATE_CARD = {
    "planner": {"input": 3.00, "cache_read": 0.30, "output": 15.00, "reasoning": 15.00},
    "worker": {"input": 2.50, "cache_read": 0.25, "output": 10.00, "reasoning": 10.00},
    "reviewer": {"input": 0.50, "cache_read": 0.05, "output": 2.00, "reasoning": 2.00},
}

# All stages have the same five-minute ceiling. The task deadline is authoritative.
STAGE_TIMEOUT_SECONDS = int(os.environ.get("STAGE_TIMEOUT_SECONDS", "300"))
TASK_TIMEOUT_SECONDS = int(os.environ.get("TASK_TIMEOUT_SECONDS", "900"))
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


PROMPTS = {
    "1_PLANNER": (
        "You are the Planner agent. Inspect README.md, public_test.py, and the implementation stub. "
        "Design the complete architecture, data structures, algorithms, and edge-case handling for {impl_file}. "
        "Write the implementation guide to 01_PLAN.md. Do not edit {impl_file} or any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests."
    ),
    "2_WORKER_INITIAL": (
        "You are the Worker agent. Read 01_PLAN.md and README.md. Implement the complete solution in {impl_file}. "
        "Run python3 -m unittest public_test.py for basic verification. Do not modify any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests."
    ),
    "3_REVIEWER": (
        "You are the Reviewer agent. Inspect {impl_file} against README.md and public_test.py. "
        "Run python3 -m unittest public_test.py. Audit edge cases, algorithmic flaws, off-by-one errors, and performance traps. "
        "Write findings and required fixes to 02_REVIEW.md. Do not edit {impl_file} or any test file. "
        "Do not access files outside the current workspace, external networks, package registries, canonical solutions, or held-out tests."
    ),
    "4_WORKER_REFINE": (
        "You are the Worker agent in refinement. Read 02_REVIEW.md, 01_PLAN.md, and README.md. "
        "Address every review finding in {impl_file}, then run python3 -m unittest public_test.py. "
        "Do not modify any test file. Do not access files outside the current workspace, external networks, "
        "package registries, canonical solutions, or held-out tests."
    ),
}

STAGES = (
    ("1_PLANNER", "planner", "01_PLAN.md"),
    ("2_WORKER_INITIAL", "worker", None),
    ("3_REVIEWER", "reviewer", "02_REVIEW.md"),
    ("4_WORKER_REFINE", "worker", None),
)
