#!/usr/bin/env python3
"""Quota-aware auto-pilot loop for the confirmatory pilot (14 pairs).

Owns the wait-retry-continue cycle so no human babysits quota windows:
- Polls `omp usage` via preflight_parity.read_usage/check_quota every WAIT_S.
- When clear, prepares a FRESH run-id (aborted ids are never resumed) unless
  the latest id is healthy-but-incomplete (no abort marker, hash current),
  then launches ONE pair with --quota-guard (sequential stepping).
- After each pair, post-run checks decide: healthy -> next pair (same id);
  doubt -> stop LOUD for a reviewer agent (exit 5); matrix complete -> stop.

Exit codes: 0 matrix complete (publish review needed) | 1 prepare failed |
2 gave up waiting | 3 mid-run quota hit (possible strand) | 4 throttled |
5 doubt (needs reviewer agent + human).
"""

import json
import os
import re
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from preflight_parity import check_quota, read_usage  # noqa: E402

LOG_PATH = os.path.join(BASE_DIR, "runs", "pilot_loop.log")
RUNS_DIR = os.path.join(BASE_DIR, "runs")
WAIT_S = 3600
MAX_WAITS = 12


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def run_ids() -> list[str]:
    ids = []
    for name in os.listdir(RUNS_DIR):
        if re.fullmatch(r"confirmatory-\d+", name):
            ids.append(name)
    return sorted(ids, key=lambda n: int(n.split("-")[1]))


def report(run_id: str) -> dict | None:
    path = os.path.join(RUNS_DIR, run_id, "preflight_parity.json")
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def pick_run_id() -> tuple[str, bool]:
    """(run_id, needs_prepare). Resumes the latest healthy-but-incomplete id;
    otherwise mints fresh (aborted ids are stranded by protocol)."""
    for run_id in reversed(run_ids()):
        rundir = os.path.join(RUNS_DIR, run_id)
        if os.path.exists(os.path.join(rundir, "pilot_aborted.json")):
            continue
        rep = report(run_id)
        if rep is None:
            continue
        try:
            from preflight_parity import compute_composite_source_sha256
            current, _ = compute_composite_source_sha256()
            if rep.get("composite_source_sha256") != current:
                continue  # stale source binding; do not resume
        except Exception:  # noqa: BLE001 - fail safe to a fresh id
            continue
        expected = rep.get("expected_pairs", 14)
        if rep.get("total_pairs_evaluated", 0) < expected:
            return run_id, False
    top = max([int(n.split("-")[1]) for n in run_ids()], default=11)
    return f"confirmatory-{top + 1:03d}", True


def pair_records(run_id: str) -> list[dict] | None:
    """Pair records in order, or None when unreadable (itself a doubt)."""
    path = os.path.join(RUNS_DIR, run_id, "pilot_records.ndjson")
    try:
        with open(path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except (OSError, ValueError):
        return None


def post_pair_checks(run_id: str, before_recs: int, before_dropped: int,
                     before_evaluated: int) -> str:
    """'healthy' | 'complete' | doubt-reason. Pair records (not results/,
    which materializes only at completion) are the per-pair evidence.
    Scientific failure is scored later from retained attempts; only
    protocol-level anomalies doubt."""
    rep = report(run_id)
    if rep is None:
        return "report unreadable"
    if rep.get("dropped_pairs_count", 0) > before_dropped:
        return (f"dropped_pairs grew "
                f"({before_dropped} -> {rep.get('dropped_pairs_count')})")
    recs = pair_records(run_id)
    if recs is None:
        return "pilot_records.ndjson unreadable"
    evaluated = rep.get("total_pairs_evaluated", 0)
    new_recs = recs[before_recs:]
    if not new_recs and evaluated <= before_evaluated:
        return "no new pair records and evaluated count stalled"
    for rec in new_recs:
        arms = rec.get("arms", {})
        if not arms:
            return f"{rec.get('task_id')}:rep{rec.get('repeat')} has no arms"
        for arm_name, arm in arms.items():
            if not isinstance(arm, dict):
                continue
            for entry in arm.get("attempt_dirs", []):
                if isinstance(entry, str) and entry.startswith("RETENTION_FAILED"):
                    return f"{rec.get('task_id')}/{arm_name} evidence retention failed"
            if not arm.get("protocol_valid", False):
                return f"{rec.get('task_id')}/{arm_name} protocol_valid false"
            if arm.get("protocol_violations") or arm.get("violations"):
                return f"{rec.get('task_id')}/{arm_name} carries violations"
            if not arm.get("stages"):
                return f"{rec.get('task_id')}/{arm_name} missing stage evidence"
    if evaluated >= rep.get("expected_pairs", 14):
        return "complete"
    return "healthy"


def main() -> int:
    waits = 0
    while True:
        breach = check_quota(read_usage())
        if breach is not None:
            waits += 1
            if waits > MAX_WAITS:
                log(f"GAVE-UP after {MAX_WAITS}h waiting (last: {breach}). Human needed.")
                return 2
            log(f"quota blocked ({breach}); sleeping {WAIT_S}s ({waits}/{MAX_WAITS})")
            time.sleep(WAIT_S)
            continue
        run_id, needs_prepare = pick_run_id()
        if needs_prepare:
            log(f"quota clear; preparing {run_id}")
            prepared = subprocess.run(
                [sys.executable, "preflight.py", "--prepare", "--run-id", run_id],
                cwd=BASE_DIR,
            )
            if prepared.returncode != 0:
                log(f"prepare for {run_id} failed rc={prepared.returncode}; stopping for human.")
                return 1
        else:
            log(f"quota clear; resuming healthy {run_id}")
        rep = report(run_id) or {}
        before_recs = len(pair_records(run_id) or [])
        before_dropped = rep.get("dropped_pairs_count", 0)
        before_evaluated = rep.get("total_pairs_evaluated", 0)
        log(f"launching one pair on {run_id} "
            f"(evaluated {before_evaluated}/{rep.get('expected_pairs', 14)})")
        launched = subprocess.run(
            [sys.executable, "preflight_parity.py", "--run-id", run_id,
             "--max-new-pairs", "1", "--quota-guard"],
            cwd=BASE_DIR, capture_output=True, text=True,
        )
        output = (launched.stdout or "") + (launched.stderr or "")
        with open(os.path.join(RUNS_DIR, f"pilot_loop_{run_id}.out"),
                  "w", encoding="utf-8") as handle:
            handle.write(output)
        if "QUOTA_CAP:post" in output:
            log(f"{run_id} hit quota MID-RUN (possible stranded pair); NOT auto-redoing. Human needed.")
            return 3
        if "QUOTA_CAP:pre" in output:
            log(f"{run_id} refused pre-spend (race); back to waiting.")
            continue
        if "RATE_LIMITED" in output:
            log(f"{run_id} throttled; recovery timing needs human judgment. Stopping.")
            return 4
        verdict = post_pair_checks(run_id, before_recs, before_dropped, before_evaluated)
        if verdict == "complete":
            log(f"{run_id}: all pairs evaluated, no anomalies. MATRIX COMPLETE — publish review needed. Stopping.")
            return 0
        if verdict == "healthy":
            log(f"{run_id}: pair healthy, continuing to next pair.")
            continue
        log(f"{run_id}: DOUBT ({verdict}). Stopping for reviewer agent + human. rc={launched.returncode}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
