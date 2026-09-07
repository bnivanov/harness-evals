# Experiment Protocol: Unified OMP Agent Orchestration vs. Disaggregated Vendor CLI Pipeline

**Status:** Pre-registered Protocol  
**Date:** 2026-09-05  
**Subject:** Comparative Efficiency of Internal Harness Multi-Agent Orchestration (Oh My Pi `omp`) vs. External Standalone Vendor CLI Pipeline Chaining (`grok`, `codex`, `agy`)  
**Target Benchmark:** 25 Curated Algorithmic Tasks (Aider Python / Exercism Suite)  
**Primary Statistical Gate:** Paired Wilcoxon Signed-Rank Test on Partial/Total Pass Rates & Token Efficiency ($N=25, \alpha=0.05, 1-\beta \ge 0.80$)

---

## 1. Research Question & Core Study Focus

**Question:** When completing an end-to-end software engineering task through the full SWE lifecycle:

$$\mathbf{Planner} \;\longrightarrow\; \mathbf{Worker} \;\longrightarrow\; \mathbf{Reviewer} \;\longrightarrow\; \mathbf{Worker}$$

> *Does an integrated coding harness (OMP) orchestrating specialized frontier models via internal session state, shared memory, and hashline editing outperform an external script orchestrating the official standalone vendor CLIs (`grok`, `codex`, `agy`) chaining markdown artifacts over disk?*

### Core Principles & Hard Constraints

1. **Default Pinned Versions, No Plugins, No Amends**:
   * Both arms execute the official, latest pinned first-party binaries out-of-the-box.
   * Zero community overlays, zero third-party plugins, zero custom prompt injections or wrappers.
   * Pinned executables:
     * `omp` (v18.1.13)
     * `grok` (xAI Grok Build CLI 1.0.5)
     * `codex` (OpenAI Codex CLI 0.153.4)
     * `agy` (Google Antigravity CLI 1.1.27)

2. **Pre-Registered Matched-Compute Effort**:
   * All stages follow the pre-registered `EFFORT_MATRIX` calibrated to match token budgets:
     * Stage 1 (Planner): `high` (OMP) / `high` (Grok Build CLI)
     * Stage 2 & 4 (Worker): `max` (OMP) / `max` (Codex CLI)
     * Stage 3 (Reviewer): `high` (OMP) / `medium` (AGY CLI)
3. **Model & Stage Parity (Held Strictly Constant)**:
   * Model capability is NOT the independent variable. Both arms execute the identical frontier model for each lifecycle step.

### The Efficiency Function

$$\text{Efficiency} = \frac{\text{Verification Pass Ratio } R \in [0.0, 1.0]}{\text{Total Cost (USD)} \times \text{Duration (seconds)}}$$

Where:
* $R = \frac{\text{Passed Test Assertions}}{\text{Total Oracle Test Assertions}}$ (measured by quarantined oracle verifier).
* **Cost** = Standardized rate-card token cost across all stages.
* **Duration** = Total wall-clock runtime including reasoning time, tool execution, and handoff overhead.

---

## 2. Experimental Lifecycle & Model Assignment

| Stage | Role | Function | Assigned Model | Arm A: Unified OMP | Arm B: Standalone Multi-CLI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Planner** | System Architecture | Inspects problem, designs data structures & algorithm | **xAI Grok 4.6** | `omp -p --model=xai-oauth/grok-4.6 --thinking=high` | `grok -p --effort high` $\to$ `01_PLAN.md` |
| **2. Worker** | Implementation | Implements full code from plan & README | **OpenAI Codex GPT-5.6 Luna** | `omp -p --model=openai-codex/gpt-5.6-luna --thinking=max --continue` | `codex exec -c model_reasoning_effort="max"` |
| **3. Reviewer**| Audit & Verification | Runs tests, hunts bugs & edge cases, audits code | **Google Gemini 3.8 Flash** | `omp -p --model=google-antigravity/gemini-3.8-flash --thinking=high --continue` | `agy -p --effort medium` $\to$ `02_REVIEW.md` |
| **4. Worker** | Refinement & Fixes | Addresses reviewer findings, fixes bugs & verifies | **OpenAI Codex GPT-5.6 Luna** | `omp -p --model=openai-codex/gpt-5.6-luna --thinking=max --continue` | `codex exec -c model_reasoning_effort="max"` |

### Pre-Registered Matched-Compute Design & Effort Calibration

To ensure that differences in pass rate, latency, and cost reflect harness coordination rather than divergent vendor reasoning budgets, model configurations follow a strictly pre-registered **matched-compute** design:
1. **Planner (Grok 4.6)**: Both arms use `high` effort, producing matched ~4.8k–5.5k reasoning tokens. (Arm B's `xhigh` in exploratory pilot was retired due to severe SLA timeout pathology).
2. **Worker (Codex GPT-5.6 Luna)**: Both arms use `max` effort, producing matched ~2.9k reasoning tokens (<0.5% disparity).
3. **Reviewer (Gemini 3.8 Flash)**: OMP at `high` matches AGY CLI at `medium`. In vendor adapters, AGY's `--effort high` defaults to an uncapped ~32k budget (averaging 26,539 tokens in confirmatory-003), whereas OMP's `high` budgets ~13k tokens. Empirical measurements across 3 strictly disjoint calibration tasks (`affine-cipher`, `book-store`, `proverb` recorded in `calibration/reviewer_effort_calibration.json`) demonstrate a 3-task pooled ratio of 1.067 (17,207 OMP tokens vs. 16,124 AGY medium tokens; mean log-ratio -0.1383, $s=0.8883$, point ratio 0.871, 90% CI [0.195, 3.882]), avoiding the massive 26.5k token compute blowup of AGY `high` (ratio 0.51).
4. **Pilot Parity Power Basis**: With empirical log standard deviation $s \approx 0.75$, achieving a strict 90% CI half-width under $\ln(1.25) = 0.223$ would require $N > 50$ pairs. For the preflight pilot calibration on tasks disjoint from the calibration set (`grep` and `list-ops` with $k=7$ repeats, $N=14$ paired observations, $df=13, t_{0.90}=1.771$):
   * Under $(N-1)s^2/\sigma^2 \sim \chi^2_{13}$, $N=14$ achieves an exact **80.0% power** ($P(\chi^2_{13} < 16.974) = 0.7994$) to contain the sample 90% CI within the pre-registered equivalence band $[-0.405, +0.405]$ on log scale ($[0.67, 1.50]$ on ratio scale) for true dispersion $\sigma \le 0.75$ ($s_{\text{crit}} = 0.8566$).
   * **Pooled Token Ratio Margin**: Across all pilot pairs, $\frac{\sum \text{Tokens}_A}{\sum \text{Tokens}_B} \in [0.80, 1.25]$.
   * **TOST 90% CI Equivalence Margin**: The paired log-ratio 90% CI must be entirely contained within $[0.67, 1.50]$.
5. **Pre-Registration Boundary**: Exactly **ONE** calibration round is permitted. The effort matrix and pilot power bounds are frozen prior to the confirmatory pilot run. No post-hoc re-tuning of the effort matrix is permitted; if the preflight parity TOST gate fails, the run is terminated.
### Independent Variable (Harness Orchestration vs. CLI Chaining)

1. **Handoff Substrate**:
   * **Arm A (OMP)**: Internal multi-agent session state, in-memory tool coordination, continuous context, and hash-anchored (`hashline`) surgical edits.
   * **Arm B (Multi-CLI)**: Disaggregated process boundaries, serialized disk handoffs (`01_PLAN.md`, `02_REVIEW.md`), and raw vendor tool loops (`apply_patch` in Codex, Antigravity bash tools).
2. **Review-and-Refine Loop Dynamics**:
   * How effectively does the Worker absorb the Reviewer's critique when mediated by a unified harness vs. serialized disk files?
---

## 3. Statistical Methodology (Pre-Registered)

### Sample Size & Power Calculation
* **Design:** Paired-sample comparative evaluation across **25 frozen benchmark tasks**.
* **Primary Test:** **Two-sided Paired Wilcoxon Signed-Rank Test** on:
  1. Oracle Pass Ratio ($R_A$ vs $R_B$)
  2. Total Cost ($C_A$ vs $C_B$)
  3. Wall-Clock Latency ($T_A$ vs $T_B$)
  4. Token Overhead ($\text{Tokens}_A$ vs $\text{Tokens}_B$)
* **Power:** For continuous and ordinal scores ($N=25$), Wilcoxon signed-rank achieves **$>82\%$ power** at $\alpha = 0.05$ to detect a moderate-to-large effect size ($d \ge 0.60$).
* **Discrete Success:** Two-sided exact **McNemar's Test** reported for binary resolution ($R = 1.0$), with Wilson 95% confidence intervals.

### Zero-Drop / Pre-Registration Rule
* Every one of the 25 pre-registered tasks MUST run to completion or failure.
* No post-hoc task dropping, filtering, or retrying based on unfavorable diffs.
* Timeouts or CLI crashes are recorded as $R = 0.0$ with full consumed resources logged.

---

## 4. Execution Budget & Circuit Breakers

To avoid infinite loops (such as the 599-turn `wasmi` failure from model bench):

1. **Strict Stage Turn Caps**:
   * Stage 1 (Recon): Max 3 turns.
   * Stage 2 (Plan): Max 2 turns.
   * Stage 3 (Implement): Max 6 turns.
   * Stage 4 (Verify): Max 3 turns.
   * **Hard Task Cap**: 14 turns total per arm.
2. **Identical Tool Call Circuit Breaker**:
   * If any tool is invoked with identical parameters 3 times consecutively, the stage is aborted and state is handed off.
3. **Wall-Clock Timeout**:
   * 5 minutes per stage; 15 minutes max per task.
4. **Offline Isolation**:
   * Web search tools disabled.
   * Network commands in bash (`curl`, `wget`, `git clone`) blocked and audited.

---

## 5. Normalized Pricing Reference Card

Token usage across both arms is converted to canonical USD costs to prevent subscription vs API billing distortions:

| Model Role | Provider SKU | Input / 1M | Cache Read / 1M | Output / 1M | Reasoning / 1M |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Grok 4.6** | `xai/grok-4.6` | $3.00 | $0.30 | $15.00 | $15.00 |
| **Claude 3.7 Sonnet**| `anthropic/claude-3-7-sonnet` | $3.00 | $0.30 | $15.00 | $15.00 |
| **GPT-5.6 / Codex** | `openai/gpt-5.6-luna` | $2.50 | $0.25 | $10.00 | $10.00 |
| **Gemini 3.8 Flash** | `google/gemini-3.8-flash` | $0.50 | $0.05 | $2.00 | $2.00 |

---

## 6. Telemetry Normalization & Fair Accounting Specification

To ensure exact comparability between the unified harness (Arm A) and standalone CLIs (Arm B), all executions must capture granular token telemetry and normalize it through a uniform accounting contract.

### 6.1 Telemetry Extraction Contracts

1. **Arm A: Unified OMP (`--mode json -p`)**:
   * Parses NDJSON stream emitted to stdout.
   * Reads `turn_end` and `message_end` event usage objects:
     * `input`: Prompt tokens.
     * `cacheRead`: Prompt tokens served from provider cache.
     * `output`: Generated completion tokens.
     * `reasoningTokens`: Thinking/scratchpad tokens.
   * Aggregates across all turns within each stage.

2. **Arm B: Disaggregated Multi-CLI**:
   * **Planner (`grok --output-format json -p`)**:
     * Extracts `usage.input_tokens`, `usage.cache_read_input_tokens`, `usage.output_tokens`, `usage.reasoning_tokens`, and `num_turns`.
   * **Worker (`codex exec --json`)**:
     * Parses JSONL event stream from stdout.
     * Aggregates across all `turn.completed` events:
       * `input_tokens`: Base prompt tokens.
       * `cached_input_tokens`: Cached prompt tokens.
       * `output_tokens`: Generated tokens.
       * `reasoning_output_tokens`: High-effort reasoning tokens.
   * **Reviewer (`agy -p --output-format json`)**:
     * Extracts `usage.input_tokens`, `usage.cache_read_tokens`, `usage.output_tokens`, `usage.thinking_tokens`, and `num_turns`.

### 6.2 Standardized Cost & Token Formula

For every stage $s$ with model $M$:

$$\text{Uncached Input} = \max(0, \text{Total Input} - \text{Cache Read})$$

$$\text{Cost}_s = \frac{\text{Uncached Input} \times P_{\text{in}} + \text{Cache Read} \times P_{\text{cache}} + \text{Output} \times P_{\text{out}} + \text{Reasoning} \times P_{\text{reasoning}}}{1,000,000}$$

Where $P_{\text{in}}, P_{\text{cache}}, P_{\text{out}}, P_{\text{reasoning}}$ are fixed by the pre-registered Reference Rate Card (Section 5), preventing subscription vs. pay-per-token pricing distortions.

### 6.3 Controlled Variables (Held Strictly Constant)

| Variable | Control Mechanism | Parity Check |
| :--- | :--- | :--- |
| **Model Family & Generation** | Pinned frontier models per stage | Identical models used in Arm A and Arm B at each stage |
| **Reasoning Depth** | Pre-registered matched-compute effort matrix | Planner: `high`/`high`<br>Worker: `max`/`max`<br>Reviewer: `high`/`medium` (calibrated to ~13k tokens) |
| **Tool Surface** | Identical primitive capabilities | File read, file write, file edit, bash unit test runner |
| **Network Isolation** | Strict offline execution | Web search disabled; external network calls blocked and audited |
| **Stage Prompts** | Verbatim identical instructions | Identical role descriptions, constraints, and instructions |
| **Evaluation Sandbox** | Anti-cheating rings 1–5 | Quarantined oracle test suite; clean ephemeral single-commit git repo; external test execution |
| **Verification Oracle** | Quarantined Exercism test suite | Independent test runner parsing assertions; zero reliance on agent self-reports |

### 6.4 The Sole Independent Variable

The **only variable permitted to differ** between Arm A and Arm B is the **orchestration and handoff substrate**:
* **Arm A**: An integrated harness (`omp`) maintaining continuous session memory (`--continue`), unified tool coordination, and hash-anchored edits.
* **Arm B**: Disaggregated standalone vendor CLIs (`grok`, `codex`, `agy`) communicating strictly across process boundaries through serialized markdown files on disk (`01_PLAN.md`, `02_REVIEW.md`).
