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
     * `omp` (v18.1.10)
     * `grok` (xAI Grok Build CLI)
     * `codex` (OpenAI Codex CLI)
     * `agy` (Google Antigravity CLI)

2. **Highest Possible Reasoning Effort**:
   * All models across all stages in both arms run with the **maximum available reasoning/thinking effort**:
     * `omp`: `--thinking=max`
     * `codex`: `-c model_reasoning_effort="high"`
     * `agy`: `--effort high`
     * `grok`: Native full reasoning depth enabled

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
| **1. Planner** | System Architecture | Inspects problem, designs data structures & algorithm | **xAI Grok 4.6** | `omp -p --model=xai-oauth/grok-4.6 --thinking=max` | `grok -p` $\to$ `01_PLAN.md` |
| **2. Worker** | Implementation | Implements full code from plan & README | **OpenAI Codex GPT-5.6 Luna** | `omp -p --model=openai-codex/gpt-5.6-luna --thinking=max --continue` | `codex exec -c model_reasoning_effort="high"` |
| **3. Reviewer**| Audit & Verification | Runs tests, hunts bugs & edge cases, audits code | **Google Gemini 3.8 Flash** | `omp -p --model=google-antigravity/gemini-3.8-flash --thinking=max --continue` | `agy -p --effort high` $\to$ `02_REVIEW.md` |
| **4. Worker** | Refinement & Fixes | Addresses reviewer findings, fixes bugs & verifies | **OpenAI Codex GPT-5.6 Luna** | `omp -p --model=openai-codex/gpt-5.6-luna --thinking=max --continue` | `codex exec -c model_reasoning_effort="high"` |

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
