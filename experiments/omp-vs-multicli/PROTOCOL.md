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
     * Stage 1 (Planner): `medium` (OMP) / `medium` (Grok Build CLI)
     * Stage 2 & 4 (Worker): `max` (OMP) / `max` (Codex CLI)
     * Stage 3 (Reviewer): `medium` (OMP) / `medium` (AGY CLI) — calibration-v2 winner per §A.6 (v1 mapping `high`/`medium` superseded).
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
| **1. Planner** | System Architecture | Inspects problem, designs data structures & algorithm | **xAI Grok 4.6** | `omp -p --model=xai-oauth/grok-4.6 --thinking=medium` | `grok -p --effort medium` $\to$ `01_PLAN.md` |
| **3. Reviewer**| Audit & Verification | Runs tests, hunts bugs & edge cases, audits code | **Google Gemini 3.8 Flash** | `omp -p --model=google-antigravity/gemini-3.8-flash --thinking=medium --continue` | `agy -p --effort medium` $\to$ `02_REVIEW.md` |
| **4. Worker** | Refinement & Fixes | Addresses reviewer findings, fixes bugs & verifies | **OpenAI Codex GPT-5.6 Luna** | `omp -p --model=openai-codex/gpt-5.6-luna --thinking=max --continue` | `codex exec -c model_reasoning_effort="max"` |

### Pre-Registered Matched-Compute Design & Effort Calibration

To ensure that differences in pass rate, latency, and cost reflect harness coordination rather than divergent vendor reasoning budgets, model configurations follow a strictly pre-registered **matched-compute** design:
1. **Planner (Grok 4.6)**: Both arms use `medium` effort, matching model architecture and reasoning depth (~700–2,400 tokens; pooled ratio 0.643, 90% CI [0.522, 0.853] recorded in `calibration/planner_effort_calibration.json`) and completing in 62s–107s, eliminating the >300s runs observed under `xhigh` in `runs/variance-probe-001/summary.json`. — SUPERSEDED for 011 by Amendment A.1/A.2: this mapping pooled 0.47 in 010; the planner mapping is re-tested once in calibration v2 and the winner governs 011. Retained as the pre-010 record.
2. **Worker (Codex GPT-5.6 Luna)**: Both arms use `max` effort, producing matched ~2.9k reasoning tokens (<0.5% disparity).
3. **Reviewer (Gemini 3.8 Flash)**: OMP at `high` matches AGY CLI at `medium`. In vendor adapters, AGY's `--effort high` defaults to an uncapped ~32k budget (averaging 26,539 tokens in confirmatory-003), whereas OMP's `high` budgets ~13k tokens. Empirical measurements across 3 strictly disjoint calibration tasks (`affine-cipher`, `book-store`, `proverb` recorded in `calibration/reviewer_effort_calibration.json`) demonstrate a 3-task pooled ratio of 1.067 (17,207 OMP tokens vs. 16,124 AGY medium tokens; mean log-ratio -0.1383, $s=0.8883$, point ratio 0.871, 90% CI [0.195, 3.882]), avoiding the massive 26.5k token compute blowup of AGY `high` (ratio 0.51). — SUPERSEDED for 011 by Amendment A.1/A.2: this mapping pooled 0.6932 in 010; re-tested once in calibration v2 with AGY `high` still forbidden. Retained as the pre-010 record.
4. **Pilot Parity Power Basis (Option A)**: For the preflight pilot calibration on tasks disjoint from the calibration set (`grep` and `list-ops` with $k=7$ repeats, $N=14$ paired observations, $df=13, t_{0.90}=1.771$):
   * **Pooled Token Ratio Margin**: Across all pilot pairs, $\frac{\sum \text{Tokens}_A}{\sum \text{Tokens}_B} \in [0.80, 1.25]$.
   * **TOST 90% CI Equivalence Margin**: The paired log-ratio 90% CI must be entirely contained within $[0.50, 2.00]$ (corresponding to $[-0.693, +0.693]$ on log scale, $2.0\times$ compute parity).
   * **Interval Containment Power**: Under the empirical log standard deviation $\sigma = 0.8883$ measured on the disjoint calibration sample, $N=14$ achieves $P(\text{half-width} \le \ln 2.0) = 99.9\%$ narrowness probability, and Monte Carlo interval containment power $P(|\bar{d}| + t_{0.90} s / \sqrt{N} \le \ln 2.0) = 73.7\%$ under $\mu=0$ ($66.6\%$ under $\mu = -0.1383$; reaching $81.0\%$ if evaluated against $[0.476, 2.10]$).
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

## 4. Execution Budget & Containment Controls

To prevent runaway execution and enforce strict isolation:

1. **Wall-Clock Timeouts**:
   * **Stage Ceiling**: 10 minutes (600 seconds) per stage (`STAGE_TIMEOUT_SECONDS = 600`), enforced via `--max-time` in OMP and subprocess deadlines in Multi-CLI.
   * **Task Ceiling**: 30 minutes (1800 seconds) total per task (`TASK_TIMEOUT_SECONDS = 1800`).
2. **Offline Isolation & Defense Architecture**:
   * **Kernel Seatbelt (Both Arms)**: macOS `sandbox-exec` enforces OS-level isolation. Denies read/write access to the repository root `PROJECT_ROOT` (`EACCES`), allows access strictly to the active `workspace` and attempt-scoped private `scratch_dir`, and denies process-exec of network executables (`curl`, `wget`, `nc`, `ssh`, `rsync`, etc.).
   * **Arm A In-Process Guard (`benchmark_guard.ts`)**: Loaded in OMP via `--hook`. Intercepts all tool calls in-process. Fail-closes on foreign URI schemes (`skill://`, `artifact://`, `history://`), access to quarantined benchmark directories (`/benchmarks/aider-python/(oracle|tasks)/`), out-of-workspace writes/edits, out-of-workspace reads, and network/package commands. Emits audit trail to `benchmark_guard.ndjson`.
   * **Arm B Multi-CLI Containment**: Isolated runtime homes (`grok-home`, `codex-home`, `agy`), kernel seatbelt, and post-hoc regex verification (`trace_violations`) across all stdout/stderr traces.
   * **Private Attempt Scratch (`TMPDIR`)**: Both arms allocate an attempt-scoped private scratch directory exported to `TMPDIR` and `BENCHMARK_SCRATCH_DIR`, cleanly wiped on attempt conclusion to prevent cross-attempt or cross-arm scratch file leakage.
   * **Workspace Lifecycle**: Workspaces are initialized with single-commit git stubs and purged after scoring.

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
| **Reasoning Depth** | Pre-registered matched-compute effort matrix | Planner: `medium`/`medium` (TOST-only per §A.6)<br>Worker: `max`/`max`<br>Reviewer: `medium`/`medium` (v2 winner per §A.6; v1 `high`/`medium` superseded) |
| **Tool Surface** | Identical primitive capabilities | File read, file write, file edit, bash unit test runner |
| **Network Isolation** | Strict offline execution | Web search disabled; external network calls blocked and audited |
| **Stage Prompts** | Verbatim identical instructions | Identical role descriptions, constraints, and instructions |
| **Evaluation Sandbox** | Anti-cheating rings 1–5 | Quarantined oracle test suite; clean ephemeral single-commit git repo; external test execution |
| **Verification Oracle** | Quarantined Exercism test suite | Independent test runner parsing assertions; zero reliance on agent self-reports |

### 6.4 The Sole Independent Variable

The **only variable permitted to differ** between Arm A and Arm B is the **orchestration and handoff substrate**:
* **Arm A**: An integrated harness (`omp`) maintaining continuous session memory (`--continue`), unified tool coordination, and hash-anchored edits.
* **Arm B**: Disaggregated standalone vendor CLIs (`grok`, `codex`, `agy`) communicating strictly across process boundaries through serialized markdown files on disk (`01_PLAN.md`, `02_REVIEW.md`).

---

## Amendment A (post-confirmatory-010, pre-011): parity-gate repair

Status: ADOPTED 2026-09-08 (Opus 5 High sign-off, resubmission PASS-WITH-CHANGES
with both required protocol repairs applied verbatim). Frozen by the commit
carrying this line; composite source hash bound in the confirmatory-011 run
manifest at `preflight.py --prepare` time. It supersedes §2.5 items 1–4 as noted below; §2.5 items
1 and 3 stand only as the superseded pre-010 record (marked inline) — A.1/A.2
govern 011; all other sections stand. Rationale: confirmatory-010 FAILed with 3 dropped pairs (a
`/tmp` guard TP, a zero-reasoning reviewer turn, a missing plan handoff) and
4/4 pooled-ratio misses, two of them also TOST misses (planner 0.47, refine
0.50). The gate below keeps every containment rule fail-closed while making
effort comparison symmetric and the pilot spend-bounded.

### A.1 Matched compute redefined at token level (§2.5 table stands, §2.5 item 1 amended)

Effort labels are vendor-adapter settings, not comparable quantities (precedent:
reviewer OMP `high` ≈ AGY `medium` at ~13k tokens). Matched compute henceforth
means agreement of accounted reasoning-token budgets at the token level, judged
by the split gate in A.2. Exactly ONE additional calibration round is permitted,
covering the planner AND reviewer mappings, on tasks disjoint from
{affine-cipher, book-store, proverb}, PILOT_TASKS {grep, list-ops}, and the
frozen 25-task matrix set (≥4 tasks, per-task ratios reported). Candidates:
Arm A planner `medium` → `high` with grok `--effort medium` fixed; reviewer
re-map within OMP {`medium`, `high`} × AGY {`medium`} (AGY `high` stays
forbidden as the uncapped ~32k path). Success per stage: calibration pooled
ratio in [0.80, 1.25]. Winners freeze in `EFFORT_MATRIX` +
`calibration/planner_effort_calibration.json` /
`calibration/reviewer_effort_calibration.json` before 011. If either stage
cannot enter the band, stop: no third round; pre-register that stage as
TOST-only with the adapter asymmetry recorded as a limitation (sign-off change
1 — 010 reviewer pooled 0.6932 / CI [0.577, 0.871] leaves no permitted remedy
under a frozen mapping, so the mapping itself is re-tested once, not gated blind).

### A.2 Split equivalence gate (§2.5 item 4 amended)

| Stage | Gate for 011 PASS |
| :--- | :--- |
| Planner | TOST 90% CI inside [0.50, 2.00] only — pooled band not applicable (TOST-only per §A.6; v2: OMP `medium` 0.47, OMP `high` 3.22) |
| Reviewer | Pooled ratio in [0.80, 1.25] AND TOST 90% CI inside [0.50, 2.00] under the calibration-v2 winner OMP `medium` / AGY `medium` (pooled 1.15 — contingency not triggered; AGY `high` stays forbidden). |
| Worker, Refine | Input-level parity by construction (same Codex binary, same `max` flag; effort flags frozen). Equivalence NOT gated; output-token divergence is a reported primary IV result. Integrity checks `zero_exclusions == 0` and `token_gaps == 0` still required. |

PASS additionally requires 0 dropped pairs, 0 token gaps, n = 14, retry rate
within A.4, and no fail-fast abort (§A.5).

### A.3 Symmetric temp containment (§4, §6.3)

The fail-closed location rule is unchanged. Containment is symmetric: the shared
seatbelt profile denies file read/write on `/tmp` and `/private/tmp` for BOTH
arms (pilot scratch remains allowed via `$TMPDIR`/workspace). The shared stage
prompts gain one identical sentence (§6.3-compliant): “Write scratch, temp, and
test-helper files only inside the current working directory (or `$TMPDIR` when
set); never write outside it.” Arm B traces are scanned post-hoc for temp-root
write attempts with the same disposition as an Arm A guard true positive
(violation → pair dropped). Residual asymmetry (disclosed): `/var/folders`
writes are not OS-denied because both arms legitimately allocate runtime state
there; only literal shared temp roots are policed.

### A.4 Retry taxonomy (§3 Zero-Drop applies to the matrix, not the pilot sample)

| Code | Class | Retry? | Pilot effect |
| :--- | :--- | :--- | :--- |
| Guard path/network/oracle | containment TP | No | drop → abort |
| `MISSING_HANDOFF` (bare — planner/reviewer ended cleanly without its artifact, e.g. `rest-api`/`two-bucket`) | arm failure | No | drop → abort |
| `NO_REASONING_TOKENS` without thinking text (Arm B: always — no vendor CLI exposes a reasoning-text stream) | arm failure | No | drop → abort |
| `REASONING_TELEMETRY_MISSING` (Arm A only: `thinking`-block chars present, 0 usage tokens) | infra/telemetry | Yes, fresh workdir, ≤ `MAX_INFRA_RETRIES` (2, frozen) | unrecovered → drop → abort |
| Subprocess `Exception` | infra | Yes (as before) | unrecovered → drop → abort |
| `TERMINAL_MODEL_ERROR` (unrecovered vendor stream stall: Arm A OMP `turn_end`/`message_end` `stopReason=error`; Arm B grok top-level `stopReason="error"`; agy top-level `status` ≠ `SUCCESS`) | infra/vendor | Yes, fresh workdir, ≤ `MAX_INFRA_RETRIES` (2, frozen); logged `kind=stream_stall` | unrecovered → drop → abort |

`MISSING_HANDOFF`, `STAGE_FAILED`, `MODEL_ID_UNRECORDED`, and the telemetry
pair are retryable ONLY as companions of `TERMINAL_MODEL_ERROR` (consequences
of the dead stage); any guard, model-mismatch, timeout, or trace-pattern code
alongside blocks retry. Detection scope (disclosed): codex CLI exposes no
terminal stop/status field in any sampled trace, so terminal-state detection
is unavailable for codex stages — failures there surface via returncode.

Heuristic token synthesis from thinking chars stays removed. Per-arm/per-stage
retry counts persist in `pilot_records.ndjson`; retry re-attempts above 10% of
arm executions in either arm FAILs the gate (instrumentation-unfit). Expected
abort mode (pre-registered): an Arm B turn with no accounted reasoning tokens
(e.g. a missing `turn.completed` event — 4/50 codex refine stages in 003,
alongside upstream cascade failures) is an arm failure with no retry path and
aborts 011 via first-drop; such an abort is an instrumentation event, not an
Arm B capability result.

### A.5 Fail-fast pilot mechanics (pilot only; §3 matrix Zero-Drop unchanged)

First dropped pair aborts the pilot (FAIL, `abort_reason`, marker
`pilot_aborted.json`; a fresh `run_id` is required — same-id resume is
refused). Any vendor throttle signal (429/529, `RESOURCE_EXHAUSTED`,
rate-limit/quota/overloaded text) in an arm result or exception aborts the
whole pilot immediately with NO retry (`RATE_LIMITED:<task>:rep<n>:<arm>`,
2026-09-08 — retrying a throttled endpoint turns a brush with quota into a
lockout; applies even under `--continue-diagnostics`). The second arm of a
dead pair is not launched. A missing plan handoff stops later stages within
that pair (pilot-only flag; the matrix path still runs every stage so a
README-only implementation can score). After each valid pair,
running pooled ratios print; at n ≥ 5 a pooled-gated stage whose running 90% CI
lies entirely outside [0.50, 2.00] aborts unrecoverably. The watch is a
rare-catastrophe backstop validated on synthetic pairs only: replaying 010's 11
valid pairs never leaves the band, so first-drop remains the expected trigger.
`--continue-diagnostics` resumes remaining pairs for diagnosis only: its output is marked
`diagnostic_only` and `run_matrix.require_parity_preflight` rejects any report
carrying `diagnostic_only` or `abort_reason`, independently of the verdict.
Sequential operation (2026-09-08): the pilot runs `--max-new-pairs 1` with
`--quota-guard`, one pair per invocation with health/usage review between
invocations (resume: same `run_id`). Pre-pair `omp usage` snapshots gate on
caps (Google weekly 97%, xAI weekly 90%, Codex 5h 90%/7d 50%); breach stops
before spending (`QUOTA_CAP`, same stranding semantics as a throttle abort).
Caps are account-protection, not science — they keep headroom for other work
rather than riding a window to 100%. Post-pair snapshots record per-pair burn.

### A.6 Calibration v2 outcome (2026-09-08; the single permitted round)

Run `run_calibration_v2.py` on grade-school, variable-length-quantity,
pig-latin, transpose (all configs success, zero violations; grade-school's
first OMP planner turn returned an empty zero-token response and was rerun
clean — recorded in the JSON). Confound disclosed: grok read Arm A's
`01_PLAN.md` on grade-school and variable-length-quantity before writing its
own plan. Planner disposition is robust to it: doubling grok's tokens on those
two tasks still pools 2.28 (out of band); only a 4x+ inflation — implausible
from reading a plan — could enter the band, and 010's clean OMP-medium 0.47
independently keeps planner TOST-only. No grok rerun: nothing depends on it.
Method deviation (unavoidable, disclosed): A.1 asked for tasks disjoint from
the 25-task matrix set, but the manifest holds exactly 25 tasks, so none
exist; v2 used fresh tasks outside the v1 set and the pilot set, preserving
gate-sample integrity.

| Stage | v2 pooled ratio | Verdict |
| Planner OMP `high` / grok `medium` | 3.22 (per-task 2.83–3.53) | MISS — with 010's OMP `medium` at 0.47, neither mapping enters the band |
| Reviewer OMP `medium` / AGY `medium` | 1.15 (per-task 0.40–3.08) | IN BAND — FROZEN winner (clean: ran first, fresh files; v2.1 confirms) |
| Reviewer OMP `high` / AGY `medium` | 3.96 clean (v2.1 isolated rerun; per-task 2.37–5.83, all out of band, consistent direction; the v2 1.71 was pure contamination artifact) | MISS — confounded v2 cell retained on disk as `reviewer_omp_high_confounded/` for audit, supports no claim |
TOST-only (`STAGE_POOLED_REQUIRED["1_PLANNER"] = False`) with the adapter
asymmetry recorded as a limitation — OMP thinking levels are too coarse to
match grok `medium` at token level (medium undershoots, high overshoots).
Reviewer gates pooled+TOST under OMP `medium` / AGY `medium`
(`EFFORT_MATRIX` updated; AGY `high` stays forbidden). Winners frozen in
`EFFORT_MATRIX` + `calibration/planner_effort_calibration.json` /
`calibration/reviewer_effort_calibration.json` by the close-out commit
carrying this section, before confirmatory-011.
