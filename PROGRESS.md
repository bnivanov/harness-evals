# Progress Log

## Session: 2026-09-05

### Objectives
- Establish an official evaluation setup for agent harnesses.
- Check starred open-source tools on GitHub (`bnivanov`).
- Integrate Oh My Pi (`omp`) into the chosen harness router infrastructure.
- Raise an upstream PR and unify all progress under a version-controlled workspace.

### Key Decisions & Actions
1. **Tool Selection**:
   - Analyzed starred repositories: `Human-Agent-Society/reef`, `trycua/cua`, and `HarnessRouter/harnessrouter`.
   - Selected `harnessrouter` as the unified orchestration and conformance layer: it implements the Unified Harness Protocol (UHP), runs 64+ standardized conformance checks across Core/Extended/Full profiles, and abstracts harness CLI execution into a single `/turn` API.

2. **Fork & Worktree Setup**:
   - Forked `HarnessRouter/harnessrouter` to `bnivanov/harnessrouter`.
   - Cloned locally and set up upstream tracking.
   - Cloned `bnivanov/llm-harness-eval` into the workspace to link evaluation protocol design with the execution engine.

3. **OMP Integration**:
   - Traced existing Pi and OpenCode implementations to determine the minimum viable surface for OMP.
   - Updated `docker/entrypoint.sh` with `install_omp()` to pull Linux binaries from `can1357/oh-my-pi`.
   - Updated `runner/server.py` with `_build_omp()` (generating `models.json`/`models.yml`, configuring `mcp.json`, auto-approve, no-extensions, tool filtering), resume verification, and `_omp_to_claude()` event streaming.
   - Updated `gateway/app.py` with `omp` backend wiring, base specifications, and path routing.
   - Updated UI components in `ui/` (`harness.ts`, `HarnessLogo.tsx`, `HarnessSettings.tsx`, `TaskChat.tsx`, `harnesses/page.tsx`).

4. **Testing & Verification**:
   - Added unit tests and an end-to-end turn test in `runner/tests/test_omp_backend.py`.
   - Verified 186/186 tests in `runner/tests/`.
   - Verified gateway tests (`test_backend_of_harness.py`, `test_hid_prefix.py`).
   - Verified 42/42 tests in `protocol/conformance/tests/`.
   - Verified live execution against a local SSE-streaming mock server running the real `omp` CLI.

5. **Upstream PR**:
   - Opened PR: **[HarnessRouter/harnessrouter#68](https://github.com/HarnessRouter/harnessrouter/pull/68)**.
   - Commit: `d068999` on branch `feat/omp-backend`.

6. **Workspace Consolidation**:
   - Linked `llm-harness-eval` milestone in `llm-harness-eval/STATUS.md` (commit `1d3f87a`).
   - Initialized git repository for the top-level `harness-evals` workspace.

### Next Steps
- Monitor upstream PR #68 for review feedback.
- Finalize Track A evaluation protocol in `llm-harness-eval` (Grok Build vs Pi vs OMP on identical benchmarks).
- Use HarnessRouter + UHP Conformance Suite to run head-to-head evals and log benchmark metrics in `llm-harness-eval/evaluation-log.md`.
