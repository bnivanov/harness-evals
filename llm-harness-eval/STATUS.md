# Status

**Updated:** 2026-09-06

## Phase

`3 — Benchmark & Ablation Complete` → Full N=25 multi-model SWE lifecycle matrix (50 runs) and 8-task extended-horizon ablation completed with statistical significance testing ($p < 0.05$).

- [x] Create project space (`llm-harness-eval`)
- [x] Continuity files: BRIEF, STATUS, DECISIONS, LEARNINGS, possible-harnesses, evaluation-log
- [x] Ingest tier-list image → `assets/tier-list-source.jpg`
- [x] First-pass harness extraction + broader missing list
- [x] Public GitHub: https://github.com/bnivanov/llm-harness-eval
- [x] Token spend tracker (private/local `TOKEN-SPEND.md` only; weekday snapshots)
- [x] Adversarial review of Wave 1 SUT selection — [`waves/wave-1-adversarial-review.md`](waves/wave-1-adversarial-review.md) (attacks PR #1 / `waves/wave-1-grok-native.md`; no scores)
- [x] Canonical landscape: subscription vs BYOK × surface — [`landscape/agentic-tools-subscription-vs-byok.md`](landscape/agentic-tools-subscription-vs-byok.md)
- [x] Infrastructure milestone: integrated Oh My Pi (`omp`) backend into HarnessRouter ([PR #68](https://github.com/HarnessRouter/harnessrouter/pull/68)) to support headless UHP evaluation across Pi and OMP
- [x] Agree evaluation protocol (tasks + metrics) — Wave 1 Track A frozen in [`waves/wave-1-track-a-protocol.md`](waves/wave-1-track-a-protocol.md) (Grok Build × Pi × OMP, pinned `grok-4.6`/`grok-build-0.1`, 3 tasks from Aider Python benchmark)
- [x] First pilot eval entry in `evaluation-log.md` (3 tasks × 2 arms = 6 runs with full token burn and rate-card cost telemetry)
- [x] Full N=25 Confirmatory Run completed and verified (50 runs recorded under `confirmatory-003`)
- [x] Stage-level fairness and isolation analysis (Tier 2) completed (confirmed 100% downstream parity when plan delivered)
- [x] Extended-horizon Grok ablation (Tier 3, 8 tasks, 600s ceiling) completed (proved 99.3% pass ratio recovery and quantified 20-25% Multi-CLI tax)
## Blockers

- Several image logos still unresolved (hexagon cluster, white K, etc.)
- Wave 1 membership vs thesis: resolved via Track A/B/C split in DECISIONS and `wave-1-track-a-protocol.md`

## Next up
1. Expand Track A execution to 3-SUT matrix (Grok Build × Pi × OMP on wordy, grade-school, list-ops)
2. Spelling/verification pass on unverified names in `possible-harnesses.md` (Soulforge, Aizen, …)
3. Monitor upstream HarnessRouter PR #68
