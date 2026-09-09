# Handoff — confirmatory-017 recovery wave (2026-09-09, ~10:15 UTC)

Continuation of the pilot recovery loop. Commit `1e914f8` holds all run evidence (013–017).

## Where we are
- **confirmatory-017: 3/14 pairs scored, all grep reps** (`pilot_records.ndjson`, `preflight_parity.json`).
- Rep 1, rep 2: both arms protocol-valid, zero violations, zero infra retries.
- Rep 3: Arm A clean (394.6s). Arm B `4_WORKER_REFINE` killed by the Codex
  account 5h usage wall — stdout ends with "You've hit your usage limit...
  try again at 2:55 PM". Runner quarantined it as dropped pair 1.
- **Wave halted**: `codex_5h` 100 >= cap 90. Runner output:
  `Quota-cap stop — no further pairs; fresh run_id required after recovery.`
  CLI reset ≈ 13:55 UTC 2026-09-09. Nothing is watching for it
  (the `c017-recovery` hub process has exited).

## Proven about the quota wall (evidence-backed, not inference)
- Pair-3 stage durations are all normal; the dead refine fast-failed in 4.65s,
  so pair 3's own spend was *lower* than pairs 1–2 while the gauge jumped
  28 → 100. Pair 3 did not cause the spike.
- `codex_5h` comes from `omp usage` = **account-level**. Benchmark-attributable
  across all 3 pairs ≈ <36pts; **≥64pts came from outside the benchmark**
  (same shared ChatGPT account). Keep the account quiet during pairs:
  a quiet account fits ~4–5 pairs per 5h window at ~8–20pts/pair.
- Arm A is flawless across the whole night (014, 016×2, 017×3). No harness,
  model, or protocol problem is indicated. Cloudflare `AuthRequired` lines in
  codex stderr are known tolerated noise (identical string in green stages).

## Open decisions (need the operator)
1. **Rep-3 Arm B: re-run (recommended — external kill, not arm failure) or keep
   scored-invalid?** Scoring a spend-wall as an arm failure poisons parity.
2. **Fresh run_id for pairs 4–14** (runner requires it) — confirm the id.
3. Re-arm a quota watcher to fire when `codex_5h` < 90, or just resume manually
   after ~13:55 UTC.

## Resume commands (from `experiments/omp-vs-multicli/`)
- Health: `python3 -c "import preflight_parity as pp; s=pp.read_usage(); print(s, pp.check_quota(s))"`
- Launch next pair: `python3 preflight_parity.py --run-id <ID> --max-new-pairs 1 --quota-guard`
- Verify scored pair health from `runs/<ID>/pilot_records.ndjson`
  (both arms `protocol_valid`, `violations`, `retries`).

## Model pins (frozen matrix, same model both arms)
Planner grok-4.6 (medium) · worker gpt-5.6-luna (max) · reviewer
gemini-3.8-flash (medium). Arm A = OMP runner, Arm B = vendor CLIs
(grok 1.0.5 / codex-cli 0.153.4 / agy 1.1.28, all pins matched at freeze).

## Caveats for the next session
- ARTICLE.md was untouched (local-only, gitignored). No article claims depend
  on 017 yet (it covers confirmatory-003).
- Task-agent model config was fixed in files (`task: astra:minimal` in both
  `~/.omp/agent/config.yml` and the hermes-jobs profile) but the old session
  still resolved task agents to grok-4.6 across 3 probes. If the new session's
  task badge doesn't show astra, it is a harness-level pin — file it, don't
  re-edit config.
