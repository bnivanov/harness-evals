# Status

**Updated:** 2026-09-05

## Phase

`0 — Project bootstrap` → protocol design, with Wave 1 SUT set under adversarial review

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
- [ ] Agree evaluation protocol (tasks + metrics) — review says **do not score Wave 1 until Track A is frozen** (Grok Build × Pi × OMP, pinned slug/auth, 3 tasks)
- [ ] First pilot eval entry in `evaluation-log.md`

## Blockers

- Several image logos still unresolved (hexagon cluster, white K, etc.)
- Wave 1 membership vs thesis: nine-SUT “Grok-native + matrix” set is not a hold-Grok-fixed design (see adversarial review)

## Next up

1. Decide keep/cut/split from [`waves/wave-1-adversarial-review.md`](waves/wave-1-adversarial-review.md) before more installs become “the eval”
2. Draft v0 evaluation protocol for **Track A only** (pinned Grok slug + auth, 3 pre-declared tasks, headless)
3. Spelling/verification pass on unverified names (Soulforge, Aizen, …)
