# Experiment Protocol: Unified OMP vs. Disaggregated Multi-CLI Swarm

**Status:** Pre-registered Protocol  
**Date:** 2026-09-05  
**Subject:** Comparative Efficiency of Multi-Model Coordination in Oh My Pi (`omp`) vs. Cross-CLI Chaining (`claude`, `codex`, `grok`, `gemini`)  
**Target Benchmark:** 25 Curated Algorithmic Tasks (Aider Python / Exercism Suite)  
**Primary Statistical Gate:** Paired Wilcoxon Signed-Rank Test on Partial/Total Pass Rates & Token Efficiency ($N=25, \alpha=0.05, 1-\beta \ge 0.80$)

---

## 1. Research Question & Decision Context

**Question:** When completing an end-to-end software engineering task requiring reconnaissance, architectural planning, code implementation, and verification:
> *Is it more efficient to orchestrate multiple frontier models (Grok, Claude, Codex, Gemini) within a single unified coding harness (OMP) sharing memory, tools, and workspace, or to disaggregate the task across the respective vendor CLI binaries (`grok`, `claude`, `codex`, `gemini`) in a serialized pipeline?*

### The Efficiency Function

$$\text{Efficiency} = \frac{\text{Verification Pass Ratio } R \in [0.0, 1.0]}{\text{Total Cost (USD)} \times \text{Duration (seconds)}}$$

Where:
* $R = \frac{\text{Passed Test Assertions}}{\text{Total Oracle Test Assertions}}$
* **Cost** = Standardized rate-card token cost across all stages.
* **Duration** = Wall-clock runtime including agent reasoning, CLI startup, and handoff overhead.

---

## 2. Experimental Conditions

To prevent the confounding errors observed in `omp-model-bench` (where model capabilities were conflated with harness loops), **the assigned model per stage is held constant across both arms**:

| Stage | Responsibility | Model Family | Arm A: Unified OMP | Arm B: Multi-CLI Swarm |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1: Recon** | Problem inspection & triage | xAI Grok (`grok-4.6`) | `omp --model xai-oauth/grok-4.6` | `grok` CLI binary |
| **Stage 2: Plan** | Architecture & patch design | Anthropic Claude (`claude-3-7-sonnet`) | `omp --model anthropic/claude-3-7-sonnet` | `claude` Code binary |
| **Stage 3: Implement** | Code editing & unit tests | OpenAI Codex (`gpt-5.6-luna` / Codex) | `omp --model openai-codex/gpt-5.6-luna` | `codex` CLI binary |
| **Stage 4: Verify** | Independent red-team review | Google Gemini (`gemini-3.8-flash`) | `omp --model google/gemini-3.8-flash` | `gemini` CLI binary |

### Independent Variable (What Changes)
1. **Tooling & Edit Reliability**:
   * **Arm A**: OMP's uniform toolset (`hashline` hash-anchored edits, LSP, AST grep, persistent kernel).
   * **Arm B**: Heterogeneous vendor tools (`apply_patch` in Codex, Bash/Glob in Claude Code, Grok tool crate, Antigravity tools).
2. **Context & State Handoff**:
   * **Arm A**: In-memory / filesystem object passing (`local://recon.md`, `local://plan.md`), shared working tree, single session context.
   * **Arm B**: Cross-process serial handoff via Git commits and serialized markdown files (`01_RECON.md`, `02_PLAN.md`, `git diff`).

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
