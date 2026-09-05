# Harness Evals Workspace

Workspace for official, reproducible LLM coding harness evaluation and multi-harness orchestration.

This repository unifies:
1. **`llm-harness-eval`** — Public research project evaluating native LLM coding harness performance under controlled conditions (holding models fixed to isolate harness effects: context retrieval, tool invocation, shell loops, edit mechanisms, subagents).
2. **`harnessrouter`** — Self-hosted execution runtime implementing the Unified Harness Protocol (UHP) to run and benchmark agents (Codex, Claude Code, Hermes, Pi, DSH, and OMP) through a single unified API with session management, progressive streaming, and conformance checks.

---

## Workspace Structure

```
harness-evals/
├── README.md
├── PROGRESS.md
├── harnessrouter/       # Unified Harness Protocol (UHP) router & execution engine (OMP backend)
└── llm-harness-eval/    # LLM coding harness evaluation protocol, benchmarks, and research
```

---

## Milestones & Daily Log

### 2026-09-05: HarnessRouter Discovery & OMP Backend Integration

1. **Target Tool Discovery**:
   - Inspected starred repositories on GitHub (`bnivanov`), identifying **HarnessRouter** (`HarnessRouter/harnessrouter`, Apache-2.0) as the ideal unified agent harness router and evaluation engine.
   - Set up fork (`bnivanov/harnessrouter`) and workspace linking both `harnessrouter` and `llm-harness-eval`.

2. **Oh My Pi (`omp`) Backend Implementation**:
   - Implemented native `omp` harness support in `harnessrouter` on branch `feat/omp-backend`:
     - **Container / Installer (`docker/entrypoint.sh`)**: Added automated installer fetching prebuilt binaries from `can1357/oh-my-pi` for x64/arm64.
     - **Runner (`runner/server.py`)**: Added `_build_omp()`, custom endpoint model configuration (`models.json`, `models.yml`), native MCP config generation (`mcp.json`), tool filtering, session resume detection (`_omp_has_session`), and progressive UHP event normalizer (`_omp_to_claude`).
     - **Gateway (`gateway/app.py`)**: Added `omp` to base catalog, model catalog, integration wiring, and prefix routing (`/omp/v1/responses`).
     - **UI (`ui/`)**: Added `omp` base option, logo, brand styling, and instructions mapping.
     - **Tests (`runner/tests/test_omp_backend.py`)**: 13 comprehensive tests including CLI building, config formats, error handling, and a live end-to-end turn test against an SSE mock LLM server.

3. **Verification**:
   - `runner/tests`: 186/186 passed.
   - `gateway/tests`: All routing and base resolution tests passed.
   - `protocol/conformance/tests`: 42/42 passed.
   - Live turn test verified real `omp` CLI execution with progressive token streaming and token accounting.

4. **Upstream Pull Request**:
   - Submitted **[PR #68 on HarnessRouter/harnessrouter](https://github.com/HarnessRouter/harnessrouter/pull/68)**.
   - Linked infrastructure milestone to `llm-harness-eval/STATUS.md` for Track A head-to-head evaluations (Grok Build × Pi × OMP).
