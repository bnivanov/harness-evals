# Wave 1 Track A Protocol: Grok-Native Coding Harnesses

**Status:** Pre-registered Protocol  
**Date:** 2026-09-05  
**Subject:** Comparative Evaluation of Coding Loop & Tooling Architecture Under Pinned Grok  
**SUTs:** Grok Build, Pi, Oh My Pi (`omp`)  
**Target Benchmark:** 3 Pre-Declared Algorithmic Tasks (Aider Python / Exercism Suite)  
**Execution Surface:** Headless / Non-Interactive (HarnessRouter UHP `/turn` & CLI headless flags)

---

## 1. Research Question & Thesis

**Core Question:** Holding the Grok model family roughly fixed, how much does the harness architecture (minimal loop vs. rich tooling vs. lab-native loop) change task success rate, edit reliability, wall-clock latency, and token cost?

This protocol implements the **Track A** split mandated by [`waves/wave-1-adversarial-review.md`](wave-1-adversarial-review.md):
- Separates Grok-fixed harness evaluation (Track A) from cross-lab native stacks (Track B: Codex, Claude Code) and experimental/surface loops (Track C: Prime Agent, FX, Cursor IDE).
- Refuses to publish an uncurated 9-row "Grok-native" table.
- Freezes SUTs, model pins, auth class, tasks, and anti-tamper constraints prior to scoring.

---

## 2. System Under Test (SUT) Matrix

| SUT | Classification | Tooling Profile | Edit Format | Pinned Model Slug | Auth Class | Headless Invocation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Grok Build** | xAI Lab-Native CLI | Lab tool crate (bash, view, edit) | Unified diff / string replace | `grok-build-0.1` *(system row)* | `oauth-supergrok` (`~/.grok/auth.json`) | `grok -p "<prompt>" --always-approve` |
| **Pi** | Minimal BYOK Loop | Minimal 4-tool set (read, write, edit, bash) | Multi-line block replacement | `xai-oauth/grok-4.6` | `oauth-supergrok` | `pi --non-interactive "<prompt>"` / UHP |
| **Oh My Pi (OMP)** | Batteries-Included Pi Fork | ~32 tools + LSP + DAP + persistent kernel | Hash-anchored (`hashline`) edits | `xai-oauth/grok-4.6` | `oauth-supergrok` | `omp --auto-approve "<prompt>"` / UHP |

### Control Rigor Notes
1. **Model Pairing:** Pi and OMP are strictly pinned to identical model slug (`grok-4.6`) and identical auth (`oauth-supergrok`).
2. **Grok Build System Label:** If Grok Build routes to `grok-build-0.1` internally, it is explicitly reported as a labeled system cell `(Grok Build × grok-build-0.1)` and never pooled without attribution into the BYOK contrast.
3. **Excluded Candidates:**
   - **Amp:** Excluded (routing product with dynamic model dial; cannot pin Grok).
   - **Hermes Agent:** Excluded from Track A (personal runtime; prone to nested Grok Build delegation; deferred to Track C).
   - **Codex CLI:** Excluded from Track A (OpenAI-native; assigned to Track B).
   - **FX / Prime Agent / Cursor Grok:** Excluded from Track A (experimental loops / IDE surface confounds; assigned to Track C).

---

## 3. Pre-Declared Benchmark Tasks ($N=3$)

Drawn from the frozen, verified Aider Python / Exercism benchmark suite under `benchmarks/aider-python/`:

| Task ID | Type | File to Implement | Initial State | Oracle Assertions | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`wordy`** | T1: Repair / Logic | `wordy.py` | Stub throwing `ValueError` | 25 unit tests | Parse and evaluate math word problems with operator precedence and syntax validation. |
| **`grade-school`** | T2: Feature / State | `grade_school.py` | Empty class methods | 20 unit tests | Implement student roster tracking with deterministic sorting and duplicate prevention. |
| **`list-ops`** | T3: Refactor / Primitives | `list_ops.py` | Unimplemented stubs | 24 unit tests | Implement functional list primitives (`foldl`, `foldr`, `map`, `filter`, `reverse`) without built-in library functions. |

---

## 4. Anti-Cheating & Quarantine Rigor

To guarantee integrity and eliminate experimenter/agent contamination:

1. **Quarantined Test Suites:**
   - Test suites in the candidate workspace contain only `public_test.py` (smoke/interface check, 1-2 trivial cases).
   - The full evaluation test suite (`oracle/tests/<task>_test.py`) is held in an isolated external directory and never exposed to the agent.
2. **Anti-Tamper Git Verification:**
   - The workspace is initialized with a clean single commit containing the initial stubs and `public_test.py`.
   - Post-execution verification audits `git diff HEAD~1` to ensure only the target implementation file was modified. Any modification to tests or stub signatures fails the run with `tampered = True`.
3. **Hermetic Temporary Verification Sandbox:**
   - Oracle execution runs in a pristine temporary sandbox (`tempfile.TemporaryDirectory()`).
   - Ground truth solutions verified $100\%$ ($69/69$ tests across these 3 tasks).

---

## 5. Execution Budget & Guardrails

1. **Turn Budget:** Maximum 10 turns per task.
2. **Wall-Clock Timeout:** Hard cutoff at 10 minutes (600 seconds) per task.
3. **Repetition Breaker:** 3 consecutive identical tool invocations aborts the run.
4. **Network Policy:** Offline execution. Network access inside tool bash (`curl`, `wget`, `pip install`) is blocked.

---

## 6. Primary Evaluation Metrics

1. **Oracle Pass Ratio ($R$):**
   $$R = \frac{\text{Passed Oracle Assertions}}{\text{Total Oracle Assertions}} \in [0.0, 1.0]$$
2. **Binary Resolution ($P$):** Boolean $1.0$ if and only if $R = 1.00$.
3. **Wall-Clock Duration ($T$):** Total runtime from prompt dispatch to task termination (seconds).
4. **Edit Reliability / Tool Friction:**
   - Count of patch rejections or malformed edits.
   - Count of syntax/runtime errors caught and recovered vs unrecovered.
5. **Standardized Token Cost ($C$):**
   Normalized rate-card conversion ($3.00/1M input, $0.30/1M cache read, $15.00/1M output).

---

## 7. Zero-Drop & Publication Rules

- **Completeness Rule:** Exactly 9 runs (3 SUTs $\times$ 3 tasks) must be completed before any comparative table or ranking is released.
- **Zero-Drop Rule:** All runs are pre-registered. No post-hoc task dropping, filtering, or selective re-running. Crashes, timeouts, or sandbox failures are logged as $R = 0.0$.
