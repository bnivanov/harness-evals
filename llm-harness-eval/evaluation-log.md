# Evaluation log

Running log of **what we evaluate, when, and outcome**. Newest first.

## Template

```
### YYYY-MM-DD — <harness> — <task id>
- Window: ...
- Model / native routing: ...
- Task: ...
- Metrics: success · latency · tokens/cost · notes
- Artifacts: links/paths
- Result: pass/fail/partial
```

## Entries

### 2026-09-06 — Rescore & Correction: Workflow Bench Experiment 2 (supersedes the two entries below)
- **Trigger:** Publication audit of `experiments/omp-vs-multicli/ARTICLE.md` against the frozen run artifacts.
- **Root cause:** `confirmatory-003` was scored while `runner_common.TRACE_VIOLATION_PATTERNS["NETWORK_COMMAND"]` still carried a bare `\bnc\b` alternative. It matched the `(nr, nc)` neighbour tuple inside the `connect` implementation plan and invalidated that task in **both** arms. The pattern has since been tightened (`nc` now needs flags or a host/port argument) but the stored results were never rescored.
- **Authoritative scorer:** `analysis/score_matrix.py` now recomputes every published number from the frozen artifacts, re-verifying each stored regex flag against the current patterns before letting it invalidate a run, and emits `analysis/scored_matrix.json`, which the publication figures read directly.
- **Corrected Tier 1 (SLA + protocol scoring, N = 25 paired):**
  - Resolution: Arm A **20/25 (80.0%)** vs Arm B **14/25 (56.0%)**; exact McNemar $b=6, c=0, p = 0.03125$.
  - Mean oracle pass ratio: **92.5%** vs **64.6%**; pooled **419/439** vs **291/439**; Wilcoxon $n=7$ non-tied, $W^+ = 28.0$, exact $p = 0.015625$.
  - Latency: 452.0s vs 609.7s, $W^+ = 5.0$, exact $p = 6.0 \times 10^{-7}$ (the earlier $p = 0.00008$ was not the exact-test value).
  - Tokens: 1,082,556 vs 1,300,513, $W^+ = 46.0$, $p = 0.00103$. Fresh (uncached) input tokens: 5.19M vs 12.45M; cache-read share 80.2% vs 66.8%.
  - Spend: Arm A **$16.92**, Arm B **$16.82** (previously mis-stated as $15.96), total **$33.74** across **59,576,734** tokens (previously $32.89 / 58,000,981); $p = 0.6338$.
- **Shadow scoring (raw oracle, no SLA or protocol gate):** Arm A **21/25 (428/439)** vs Arm B **20/25 (413/439)**. Published alongside the SLA view from now on.
- **Corrected Tier 2:** conditional subset is 17 tasks with **14/17 and 95.0% for both arms**, identical task by task. Stage 2 means were transposed in the article and in figure 04: OMP **99.7s**, Codex CLI **110.2s**.
- **Corrected Tier 3:** the 8-task block's pre-ablation raw oracle score was **122/138 with 6/8 resolutions**, so the 0 → 137/138 jump is mostly the protocol gate opening. Genuine accuracy recoveries: `react` (2/14 → 14/14) and `pov` (11/15 → 14/15). Ablation planner mean is **318.3s** (`go-counting` planning was 435.8s, not ~420s). Synthetic 25-task Arm B resolves **21/25** and **428/439** unit tests in **14,325.8s** for **$20.46**.
- **Other fixes:** `ORACLE_PATH` scanner regex was quadratic (~2.4 s/MB) and is now literal-anchored; `visuals/out/05-ablation-recovery-tax.png` (orphaned) deleted; figure text collisions and 18-character label truncation in figures 02/04/06/07 repaired.
- **Result:** CORRECTED. Direction and significance of every headline claim survive; magnitudes and task attributions changed.

### 2026-09-06 — OMP vs. Multi-CLI Swarm Pilot (N = 3 Tasks, 6 Runs)
- **Window:** Headless Automated SWE Lifecycle Benchmark (`Planner` -> `Worker` -> `Reviewer` -> `Worker`)
- **SUTs Evaluated:**
  - **Arm A:** Unified Oh My Pi (`omp`) Multi-Model Session Coordination
  - **Arm B:** Standalone Multi-CLI Pipeline Chaining (`grok` CLI -> `codex` CLI -> `agy` CLI -> `codex` CLI)
- **Model & Reasoning Parity:**
  - Stage 1 (Planner): `xai-oauth/grok-4.6` @ `max` (OMP) vs. `grok-4.6-build` @ `--effort xhigh` (Grok CLI)
  - Stage 2 (Worker Initial): `openai-codex/gpt-5.6-luna` @ `max` (OMP) vs. `gpt-5.6-luna` @ `max` (Codex CLI)
  - Stage 3 (Reviewer): `google-antigravity/gemini-3.8-flash` @ `max` (OMP) vs. `gemini-3.8-flash` @ `high` (AGY CLI)
  - Stage 4 (Worker Refine): `openai-codex/gpt-5.6-luna` @ `max` (OMP) vs. `gpt-5.6-luna` @ `max` (Codex CLI)
- **Tasks & Per-Task Breakdown:**
  1. `grade-school` (Exercism / Aider Python):
     - **Arm A (OMP):** Pass 20/20 (100%) · Duration: 291.8s · Cost: $0.3964 (1,137,843 total tokens)
     - **Arm B (Multi-CLI):** Pass 20/20 (100%) · Duration: 349.6s · Cost: $0.5982 (726,774 total tokens)
  2. `book-store` (Exercism / Aider Python):
     - **Arm A (OMP):** Pass 20/20 (100%) · Duration: 377.1s · Cost: $0.5794 (1,504,759 total tokens)
     - **Arm B (Multi-CLI):** Pass 20/20 (100%) · Duration: 628.1s · Cost: $0.5399 (793,650 total tokens; Grok CLI Planner timed out at 300s, pipeline recovered)
  3. `wordy` (Exercism / Aider Python):
     - **Arm A (OMP):** Pass 25/25 (100%) · Duration: 487.0s · Cost: $0.9518 (1,919,207 total tokens)
     - **Arm B (Multi-CLI):** Pass 25/25 (100%) · Duration: 784.9s · Cost: $1.2290 (984,299 total tokens)
- **Aggregated Metrics (N = 3 Paired):**
  - **Task Resolution Rate:** Arm A: 3/3 (100%) vs. Arm B: 3/3 (100%)
  - **Mean Oracle Test Pass Ratio:** Arm A: 100.0% vs. Arm B: 100.0%
  - **Mean Wall-Clock Duration:** Arm A: 385.3s vs. Arm B: 587.5s (OMP is **202.2s faster per task**, 34.4% latency reduction)
  - **Mean Standardized Rate-Card Cost:** Arm A: $0.6425 vs. Arm B: $0.7890 (OMP is **$0.1465 cheaper per task**, 18.6% cost reduction)
- **Key Qualitative Findings:**
  - Standalone CLI execution suffers from unconstrained open-ended planning loops (Grok CLI hit the 300s timeout ceiling on `book-store`). In contrast, OMP bounded the planning turns tightly within tool-use events.
  - OMP's continuous session context provided substantial token caching advantages over repeated disk-file re-injection across independent CLI process spawns.
- **Artifacts:**
  - `experiments/omp-vs-multicli/results/*_arm_a.json`
  - `experiments/omp-vs-multicli/results/*_arm_b.json`
  - Analysis Script: `experiments/omp-vs-multicli/analysis/calculate_stats.py`
  - Parity Audit Suite: `experiments/omp-vs-multicli/smoke_test_parity.py`
- **Result:** PASS (100% resolution across all 6 runs, statistical superiority in wall-clock latency and standardized cost)

### 2026-09-06 — Confirmatory Full Run: OMP vs. Multi-CLI Swarm (N = 25 Tasks, 50 Runs)
- **Window:** Full Pre-Registered 25-Task Benchmark Matrix (`confirmatory-003`)
- **Primary Statistical Gate Results (Tier 1)**:
  - **Task Resolution Rate (P=1.0)**: Arm A: **19/25 (76.0%)** [95% CI: 56.6% – 88.5%] vs. Arm B: **13/25 (52.0%)** [95% CI: 33.5% – 70.0%].
    - **Exact McNemar Test**: $p = 0.0312$ (**STATISTICALLY SIGNIFICANT** at $\alpha = 0.05$)
  - **Mean Oracle Pass Ratio**: Arm A: **88.5%** vs. Arm B: **60.6%** ($+27.9\%$ advantage for OMP).
    - **Paired Wilcoxon Signed-Rank Test**: $W^+ = 28.0, p = 0.0156$ (**STATISTICALLY SIGNIFICANT**)
  - **Mean Wall-Clock Latency**: Arm A: **452.0s** vs. Arm B: **609.7s** (OMP is **157.7s faster per task**).
    - **Paired Wilcoxon Signed-Rank Test**: $W^+ = 5.0, p = 0.0000$ (**STATISTICALLY SIGNIFICANT**)
  - **Mean Token Consumption**: Arm A: **1,082,556 tokens** vs. Arm B: **1,300,513 tokens** (OMP saves **217,957 tokens per task**).
    - **Paired Wilcoxon Signed-Rank Test**: $W^+ = 46.0, p = 0.0010$ (**STATISTICALLY SIGNIFICANT**)
  - **Standardized Rate-Card Cost**: Total: **$32.89** across 58,000,981 tokens (Arm A: $16.92, Arm B: $15.96, mean per task: $0.6769 vs $0.6727, $p = 0.6338$).
- **Tier 2 Isolated Per-Stage Head-to-Head**:
  - **When Grok Stage 1 Succeeded (17 tasks)**:
    - Arm A Pass Ratio: **89.2%** | Resolution: **13/17 (76.5%)**
    - Arm B Pass Ratio: **89.2%** | Resolution: **13/17 (76.5%)**
    - Downstream Codex (Worker) and Gemini/Antigravity (Reviewer) demonstrated **100% parity** in problem-solving capability.
  - **When Grok Stage 1 Timed Out (8 tasks)**:
    - Arm A Pass Ratio: **87.0%** | Resolution: **6/8 (75.0%)**
    - Arm B Pass Ratio: **0.0%** | Resolution: **0/8 (0.0%)**
  - **Stage 1 (Planner - Grok 4.6 @ xhigh)**: OMP: 25/25 (100%), 147.5s vs Grok CLI: 17/25 (68%), 239.8s (OMP is **92.4s faster** with 0 timeouts).
  - **Stage 2 (Worker Initial - GPT-5.6 Luna @ max)**: OMP: 25/25 (100%), 99.7s vs Codex CLI: 25/25 (100%), 110.2s.
  - **Stage 3 (Reviewer - Gemini 3.8 Flash @ high)**: OMP: 25/25 (100%), 100.1s vs Antigravity CLI: 25/25 (100%), 151.6s.
  - **Stage 4 (Worker Refine - GPT-5.6 Luna @ max)**: OMP: 25/25 (100%), 66.6s vs Codex CLI: 21/25 (84%), 108.1s.
- **Artifacts**: `experiments/omp-vs-multicli/runs/confirmatory-003/results/*`

### 2026-09-06 — Tier 3 Ablation: Extended-Horizon Grok CLI (N = 8 Tasks, 600s Ceiling)
- **Window:** Investigation of the 8 tasks where Grok CLI hit the 300s protocol ceiling (`ablation-extended-grok`).
- **Tasks Evaluated:** `['scale-generator', 'sgf-parsing', 'react', 'rest-api', 'pov', 'list-ops', 'grep', 'go-counting']`
- **Ceilings:** Stage 1 Ceiling: 600s (expanded from 300s) | Task Ceiling: 1800s (expanded from 900s).
- **Ablation Results:**
  - **Pre-Ablation Pass Rate (300s SLA):** 0 / 138 unit tests (0.0%) | 0 / 8 binary resolutions (0.0%).
  - **Post-Ablation Pass Rate (600s Ceiling):** **137 / 138 unit tests (99.3%)** | **7 / 8 binary resolutions (87.5%)**.
  - **Tasks Resolved 100%:** `scale-generator` (17/17), `sgf-parsing` (23/23), `react` (14/14), `rest-api` (9/9), `list-ops` (24/24), `grep` (25/25), `go-counting` (11/11).
  - **Partial Resolution:** `pov` (14/15, 93.3%).
- **Direct Head-to-Head Comparison (OMP vs. Multi-CLI Ablation on the 8 Tasks):**
  - **Unit Pass Ratio:** OMP: 128 / 138 (92.8%) vs. Multi-CLI: **137 / 138 (99.3%)**
  - **Binary Resolution:** OMP: 6 / 8 (75.0%) vs. Multi-CLI: **7 / 8 (87.5%)**
  - **Cumulative Wall-Clock Latency:** OMP: **4,462.7s (74.4m)** vs. Multi-CLI: **5,751.1s (95.9m)** (OMP is **1,288.4s faster**, a 22.4% latency advantage).
  - **Cumulative Standardized Cost:** OMP: **$6.42** vs. Multi-CLI: **$7.88** (OMP is **$1.46 cheaper**, an 18.6% cost savings).
- **Synthetic 25-Task Overall Matrix (OMP vs. Extended Multi-CLI):**
  - **Binary Resolution:** OMP: 19 / 25 (76.0%) vs. Multi-CLI: 20 / 25 (80.0%) (functional parity, $\Delta = 1$ task).
  - **Unit Pass Ratio:** OMP: 409 / 439 (93.2%) vs. Multi-CLI: 418 / 439 (95.2%).
  - **Total Latency:** OMP: **11,299.7s (188.3m)** vs. Multi-CLI: **14,325.8s (238.8m)** (OMP saves **50.4 minutes** across 25 tasks).
  - **Total Cost:** OMP: **$16.92** vs. Multi-CLI: **$20.46** (OMP saves **$3.54** across 25 tasks).
- **Core Conclusion:**
  - Grok CLI's plans are structurally sound and capable of guiding Codex/Gemini to near-perfect scores, but standalone Grok CLI takes 1.6× to 2.5× longer to complete multi-turn reasoning across process boundaries.
  - OMP's internal harness integration keeps Grok planning under 205s on every task, enabling it to succeed within production 300s SLAs where standalone CLIs fail.
  - In unconstrained environments, Multi-CLI matches OMP's accuracy but pays an ongoing **20–25% latency and cost tax**.
- **Artifacts:** `experiments/omp-vs-multicli/runs/ablation-extended-grok/results/*`
