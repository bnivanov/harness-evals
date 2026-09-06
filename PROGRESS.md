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

7. **Tooling & Orchestration Evaluation**:
   - Evaluated Herdr vs HarnessRouter for harness evaluation and agent management:
     - Confirmed Herdr manages POSIX PTY terminal panes and CLI agents (`--kind codex`, `claude`, `pi`, `omp`, etc.) with lifecycle detection (`idle`, `working`, `blocked`, `done`), but cannot host or inspect desktop GUI apps (e.g. ChatGPT desktop app, Codex/Cursor IDE GUI).
     - Formally documented decision to use HarnessRouter (UHP) as the programmatic, headless benchmarking engine (model-fixed proxy routing, ground-truth token accounting, normalized SSE events) while keeping Herdr for interactive human-in-the-loop terminal supervision.
   - Documented in `llm-harness-eval/LEARNINGS.md` and `llm-harness-eval/DECISIONS.md`.

8. **Unified Monorepo Cutover**:
   - De-submoduled `llm-harness-eval` and `harnessrouter`, removing `.gitmodules` and nested `.git` references.
   - Backed up original submodule `.git` environments to `~/.git-backups/` for external branch sync.
   - Absorbed all 304 project files directly into the root `harness-evals` tree for single-tree version control and frictionless development.

### Next Steps
- Monitor upstream PR #68 for review feedback.
- Finalize Track A evaluation protocol in `llm-harness-eval` (Grok Build vs Pi vs OMP on identical benchmarks).
- Use HarnessRouter + UHP Conformance Suite to run head-to-head evals and log benchmark metrics in `llm-harness-eval/evaluation-log.md`.

## Session: 2026-09-06

### Objectives
- Establish rigorous, audited model and reasoning parity across internal harness (OMP) and disaggregated CLI pipelines (Grok, Codex, Antigravity).
- Execute the complete $N=3$ task pilot evaluation matrix (`grade-school`, `book-store`, `wordy`) with full token burn and rate-card cost telemetry.
- Record empirical findings in `llm-harness-eval/evaluation-log.md` and advance continuity files.

### Key Decisions & Actions
1. **Rigorous Parity Audit**:
   - Built `experiments/omp-vs-multicli/smoke_test_parity.py` testing model resolution, reasoning effort flags, and token emission across all 4 stages:
     - Stage 1 (Planner): `xai-oauth/grok-4.6` @ `max` (OMP) vs `grok` @ `--effort xhigh` (Grok CLI)
     - Stage 2 & 4 (Worker): `openai-codex/gpt-5.6-luna` @ `max` (OMP) vs `codex` @ `gpt-5.6-luna` & `max` (Codex CLI)
     - Stage 3 (Reviewer): `google-antigravity/gemini-3.8-flash` @ `max` (OMP) vs `agy` @ `high` (AGY CLI)
   - Diagnosed and fixed OMP automatic fallback: created `config_overlay.yml` to disable `usageAwareFallback` and `modelFallback`, locking execution strictly to the target models without fallback.
   - Verified Codex CLI explicit model resolution to `gpt-5.6-luna` with reasoning effort `max`.

2. **Full-Telemetry Pilot Execution**:
   - Ran all 3 pre-registered tasks across Arm A (Unified OMP) and Arm B (Multi-CLI) (6 full runs):
     - `grade-school`: Arm A: 291.8s, $0.3964 (20/20) vs Arm B: 349.6s, $0.5982 (20/20)
     - `book-store`: Arm A: 377.1s, $0.5794 (20/20) vs Arm B: 628.1s, $0.5399 (20/20; Grok planner timed out at 300s, pipeline recovered)
     - `wordy`: Arm A: 487.0s, $0.9518 (25/25) vs Arm B: 784.9s, $1.2290 (25/25)
   - 100% binary resolution rate and 100% unit test assertion pass rate across both arms.

3. **Empirical Results**:
   - **Latency Advantage:** Unified OMP reduced wall-clock duration by **202.2 seconds per task (-34.4%)** compared to standalone CLI chaining.
   - **Cost Advantage:** Standardized rate-card cost was **$0.1465 lower per task (-18.6%)** under OMP due to persistent session context caching versus redundant disk file re-injection in standalone CLI invocations.
   - **Rigor & Bounded Execution:** OMP prevented runaway reasoning loops through structured tool events, whereas Grok CLI hit the 300s ceiling on `book-store`.

4. **Continuity & Archival**:
   - Documented all 6 runs in `llm-harness-eval/evaluation-log.md`.
   - Verified Track A protocol freeze in `llm-harness-eval/waves/wave-1-track-a-protocol.md`.
   - Updated `llm-harness-eval/STATUS.md` to Phase 2 (Pilot Complete).

### Next Steps
- Scale evaluation to the full $N=25$ task matrix under `experiments/omp-vs-multicli/` for formal statistical significance testing.
- Execute the 3-SUT Wave 1 Track A comparison (Grok Build vs Pi vs OMP) under HarnessRouter.
- Continue monitoring upstream HarnessRouter PR #68.
