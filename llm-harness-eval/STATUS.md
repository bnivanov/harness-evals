# Status

**Updated:** 2026-09-05

## Phase

`1 — Protocol frozen` → Wave 1 Track A protocol pre-registered; pilot execution ready

## Now

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
- [ ] First pilot eval entry in `evaluation-log.md`

## Blockers

- Several image logos still unresolved (hexagon cluster, white K, etc.)
- Wave 1 membership vs thesis: resolved via Track A/B/C split in DECISIONS and `wave-1-track-a-protocol.md`

## Next up

1. Execute Wave 1 Track A pilot runs (3 tasks × 3 SUTs) and record metrics in `evaluation-log.md`
2. Spelling/verification pass on unverified names in `possible-harnesses.md` (Soulforge, Aizen, …)
3. Monitor upstream HarnessRouter PR #68
