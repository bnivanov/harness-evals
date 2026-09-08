#!/usr/bin/env python3
"""Authoritative scoring for Workflow Bench Experiment 2.

Recomputes every published number from the frozen run artifacts so that the
article and the publication figures cannot drift from the data.

Two scoring views are emitted for every metric:

* ``scored``  - the pre-registered SLA view. A run whose stages breached the
  300s ceiling, or that violated the protocol (missing handoff, tampered
  telemetry, anti-cheating trip), is scored R = 0.0.
* ``shadow``  - the raw oracle view. Whatever the run produced is verified by
  the quarantined oracle suite regardless of SLA or protocol state.

Regex-derived violation codes stored in the result JSON are re-verified against
the *current* ``TRACE_VIOLATION_PATTERNS`` before they are allowed to invalidate
a run. ``confirmatory-003`` was scored while ``NETWORK_COMMAND`` still used a
bare ``\\bnc\\b`` alternative, which matched the ``(nr, nc)`` neighbour tuple in
the ``connect`` plan text; that stale flag is dropped here.

Usage:
    python3 analysis/score_matrix.py                 # print report
    python3 analysis/score_matrix.py --json out.json # also write machine copy
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner_common import TRACE_VIOLATION_PATTERNS  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runners"))
from arm_a_omp import parse_omp_telemetry  # noqa: E402  (verdict-b terminal-state rule)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMARY_RUN = os.path.join(BASE_DIR, "runs", "confirmatory-003")
ABLATION_RUN = os.path.join(BASE_DIR, "runs", "ablation-extended-grok")

REGEX_CODES = {code for code, _ in TRACE_VIOLATION_PATTERNS}
PATTERNS = dict(TRACE_VIOLATION_PATTERNS)
STAGE_ORDER = ("1_PLANNER", "2_WORKER_INITIAL", "3_REVIEWER", "4_WORKER_REFINE")
STAGE_LABELS = {
    "1_PLANNER": "Planner",
    "2_WORKER_INITIAL": "Worker Initial",
    "3_REVIEWER": "Reviewer",
    "4_WORKER_REFINE": "Worker Refine",
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_run(run_dir: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(run_dir, "results", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        out[os.path.basename(path)[: -len(".json")]] = payload
    return out


def resolve_trace_path(path: str | None) -> str | None:
    if not path:
        return None
    if os.path.isfile(path):
        return path
    if "/runs/" in path:
        rel = path[path.index("/runs/") + 1 :]
        candidate = os.path.join(BASE_DIR, rel)
        if os.path.isfile(candidate):
            return candidate
    return None


def stage_trace_text(stage: dict) -> tuple[str, bool]:
    """Return concatenated trace text and whether all referenced trace files were found."""
    chunks = []
    all_found = True
    for key in ("stdout_trace", "stderr_trace"):
        meta = stage.get(key) or {}
        raw_path = meta.get("path")
        if not raw_path:
            continue
        path = resolve_trace_path(raw_path)
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as handle:
                chunks.append(handle.read())
        else:
            all_found = False
    return "\n".join(chunks), all_found


def live_regex_codes(result: dict) -> set[str]:
    """Re-verify stored regex violations against the current pattern set (fail-closed)."""

    stored = {
        v["code"]
        for v in (result["execution"].get("protocol_violations") or [])
        if v["code"] in REGEX_CODES
    }
    if not stored:
        return set()
    confirmed: set[str] = set()
    all_traces_available = True
    for stage in result["execution"]["stages"]:
        text, ok = stage_trace_text(stage)
        if not ok:
            all_traces_available = False
        if not text:
            continue
        for code in stored - confirmed:
            if PATTERNS[code].search(text):
                confirmed.add(code)
        if confirmed == stored:
            break

    # Fail-closed: if any trace file was missing and could not be inspected,
    # refuse to drop unconfirmed stored violation flags as stale.
    if not all_traces_available and confirmed != stored:
        return stored
    return confirmed


_STAGE_ROLES = {
    "1_PLANNER": "planner",
    "2_WORKER_INITIAL": "worker",
    "3_REVIEWER": "reviewer",
    "4_WORKER_REFINE": "worker",
}
_TERMINAL_CACHE: dict[tuple[str, str, str], bool] = {}


def _stage_terminal_error(run_dir: str, task_id: str, arm: str, stage_name: str, telemetry: dict | None) -> bool:
    """Verdict-(b) terminal-state rule for historical stage-ok counts.
    New records carry the parser flag; legacy records predate it, so the same
    rule is applied to the retained trace (arm_a OMP schema only). Source
    records are never rewritten. Missing/unreadable traces preserve history.
    """
    telemetry = telemetry or {}
    if telemetry.get("terminal_error") is not None:
        return True
    if "terminal_error" in telemetry or arm != "arm_a":
        return False
    key = (run_dir, task_id, stage_name)
    if key not in _TERMINAL_CACHE:
        trace = os.path.join(run_dir, "traces", task_id, arm, f"{stage_name}.stdout.jsonl")
        try:
            with open(trace, encoding="utf-8") as handle:
                parsed = parse_omp_telemetry(handle.read(), _STAGE_ROLES[stage_name])
            _TERMINAL_CACHE[key] = parsed.get("terminal_error") is not None
        except (OSError, ValueError, KeyError):
            _TERMINAL_CACHE[key] = False
    return _TERMINAL_CACHE[key]


def score_run(result: dict, run_dir: str = "") -> dict:
    execution = result["execution"]
    oracle = result["oracle_verification"]
    stored = execution.get("protocol_violations") or []
    structural = [v for v in stored if v["code"] not in REGEX_CODES]
    confirmed_regex = live_regex_codes(result)
    stale = sorted({v["code"] for v in stored if v["code"] in REGEX_CODES} - confirmed_regex)
    valid = not structural and not confirmed_regex
    return {
        "task": result["task_id"],
        "arm": result["arm"],
        "valid": valid,
        "invalidated_by": sorted({v["code"] for v in structural} | confirmed_regex),
        "stale_flags": stale,
        "shadow_ratio": oracle["ratio"],
        "shadow_passed": oracle["passed_tests"],
        "shadow_resolved": 1 if oracle["passed"] else 0,
        "total_tests": oracle["total_tests"],
        "ratio": oracle["ratio"] if valid else 0.0,
        "passed": oracle["passed_tests"] if valid else 0,
        "resolved": 1 if (valid and oracle["passed"]) else 0,
        "duration": execution["duration"],
        "tokens": execution["normalized_total_tokens"],
        "cost": execution["total_cost_usd"],
        "stages": {
            stage["stage"]: {
                "duration": stage["duration"],
                "ok": stage["returncode"] == 0 and not stage.get("error") and not _stage_terminal_error(
                    run_dir, result["task_id"], result["arm"], stage["stage"], stage.get("telemetry")),
                "fresh_input": (stage.get("telemetry") or {}).get("input_tokens") or 0,
                "cache_read": (stage.get("telemetry") or {}).get("cache_read_tokens") or 0,
            }
            for stage in execution["stages"]
        },
    }


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def mcnemar_exact(pairs: Iterable[tuple[int, int]]) -> dict:
    b = sum(1 for a, c in pairs if a == 1 and c == 0)
    c = sum(1 for a, cc in pairs if a == 0 and cc == 1)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p": 1.0}
    lo = min(b, c)
    # two-sided exact binomial with p = 0.5
    from math import comb

    tail = sum(comb(n, k) for k in range(0, lo + 1))
    p = min(1.0, 2 * tail / 2**n)
    return {"b": b, "c": c, "p": p}


def wilcoxon_exact(xs: list[float], ys: list[float]) -> dict:
    deltas = [x - y for x, y in zip(xs, ys) if x != y]
    n = len(deltas)
    if n == 0:
        return {"n": 0, "w_plus": 0.0, "p": 1.0}
    order = sorted(range(n), key=lambda i: abs(deltas[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(deltas[order[j + 1]]) == abs(deltas[order[i]]):
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    w_plus = sum(r for r, d in zip(ranks, deltas) if d > 0)
    total = sum(ranks)
    stat = min(w_plus, total - w_plus)
    # Exact null distribution over sign flips (ranks doubled to stay integral).
    doubled = [int(round(2 * r)) for r in ranks]
    limit = int(round(2 * stat))
    span = sum(doubled)
    counts = {0: 1}
    for rank in doubled:
        nxt: dict[int, int] = {}
        for value, count in counts.items():
            nxt[value] = nxt.get(value, 0) + count
            nxt[value + rank] = nxt.get(value + rank, 0) + count
        counts = nxt
    tail = sum(count for value, count in counts.items() if min(value, span - value) <= limit)
    return {"n": n, "w_plus": w_plus, "p": tail / 2**n}


def summarize(rows: list[dict], key_ratio: str, key_pass: str, key_res: str) -> dict:
    return {
        "n": len(rows),
        "resolved": sum(r[key_res] for r in rows),
        "passed": sum(r[key_pass] for r in rows),
        "total_tests": sum(r["total_tests"] for r in rows),
        "mean_ratio": statistics.mean(r[key_ratio] for r in rows),
        "mean_duration": statistics.mean(r["duration"] for r in rows),
        "total_duration": sum(r["duration"] for r in rows),
        "mean_tokens": statistics.mean(r["tokens"] for r in rows),
        "total_cost": sum(r["cost"] for r in rows),
        "mean_cost": statistics.mean(r["cost"] for r in rows),
    }


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build() -> dict:
    primary = {name: score_run(res, PRIMARY_RUN) for name, res in load_run(PRIMARY_RUN).items()}
    ablation = {name: score_run(res, ABLATION_RUN) for name, res in load_run(ABLATION_RUN).items()}

    tasks = sorted({name.rsplit("_arm_", 1)[0] for name in primary})
    arm_a = [primary[f"{t}_arm_a"] for t in tasks]
    arm_b = [primary[f"{t}_arm_b"] for t in tasks]

    planner_timeout = [
        t for t in tasks if not primary[f"{t}_arm_b"]["stages"]["1_PLANNER"]["ok"]
    ]
    conditional = [t for t in tasks if t not in planner_timeout]

    def rows(names: list[str], arm: str, source: dict) -> list[dict]:
        return [source[f"{t}_{arm}"] for t in names]

    scored = {
        "arm_a": summarize(arm_a, "ratio", "passed", "resolved"),
        "arm_b": summarize(arm_b, "ratio", "passed", "resolved"),
    }
    shadow = {
        "arm_a": summarize(arm_a, "shadow_ratio", "shadow_passed", "shadow_resolved"),
        "arm_b": summarize(arm_b, "shadow_ratio", "shadow_passed", "shadow_resolved"),
    }

    tests = {
        "mcnemar": mcnemar_exact(
            [(a["resolved"], b["resolved"]) for a, b in zip(arm_a, arm_b)]
        ),
        "ratio": wilcoxon_exact([r["ratio"] for r in arm_a], [r["ratio"] for r in arm_b]),
        "duration": wilcoxon_exact(
            [r["duration"] for r in arm_a], [r["duration"] for r in arm_b]
        ),
        "tokens": wilcoxon_exact([r["tokens"] for r in arm_a], [r["tokens"] for r in arm_b]),
        "cost": wilcoxon_exact([r["cost"] for r in arm_a], [r["cost"] for r in arm_b]),
    }

    stage_table = []
    for stage in STAGE_ORDER:
        entry = {"stage": stage, "label": STAGE_LABELS[stage]}
        for arm, group in (("arm_a", arm_a), ("arm_b", arm_b)):
            entry[arm] = {
                "ok": sum(1 for r in group if r["stages"][stage]["ok"]),
                "n": len(group),
                "mean_duration": statistics.mean(
                    r["stages"][stage]["duration"] for r in group
                ),
            }
        stage_table.append(entry)

    context = {}
    for arm, group in (("arm_a", arm_a), ("arm_b", arm_b)):
        fresh = sum(s["fresh_input"] for r in group for s in r["stages"].values())
        cache = sum(s["cache_read"] for r in group for s in r["stages"].values())
        context[arm] = {
            "fresh_input_tokens": fresh,
            "cache_read_tokens": cache,
            "cache_share": cache / (cache + fresh) if cache + fresh else 0.0,
        }

    cond = {
        "tasks": conditional,
        "arm_a": summarize(rows(conditional, "arm_a", primary), "ratio", "passed", "resolved"),
        "arm_b": summarize(rows(conditional, "arm_b", primary), "ratio", "passed", "resolved"),
    }

    abl_tasks = sorted({name.rsplit("_arm_", 1)[0] for name in ablation})
    abl_rows = [ablation[f"{t}_arm_b"] for t in abl_tasks]
    primary_b_abl = rows(abl_tasks, "arm_b", primary)
    primary_a_abl = rows(abl_tasks, "arm_a", primary)
    tier3 = {
        "tasks": abl_tasks,
        "arm_a_primary": summarize(primary_a_abl, "ratio", "passed", "resolved"),
        "arm_b_primary_scored": summarize(primary_b_abl, "ratio", "passed", "resolved"),
        "arm_b_primary_shadow": summarize(
            primary_b_abl, "shadow_ratio", "shadow_passed", "shadow_resolved"
        ),
        "arm_b_ablation": summarize(abl_rows, "ratio", "passed", "resolved"),
        "per_task": [
            {
                "task": t,
                "primary_shadow_passed": primary[f"{t}_arm_b"]["shadow_passed"],
                "primary_scored_passed": primary[f"{t}_arm_b"]["passed"],
                "total_tests": primary[f"{t}_arm_b"]["total_tests"],
                "ablation_passed": ablation[f"{t}_arm_b"]["passed"],
                "ablation_planner": ablation[f"{t}_arm_b"]["stages"]["1_PLANNER"]["duration"],
                "ablation_duration": ablation[f"{t}_arm_b"]["duration"],
                "ablation_cost": ablation[f"{t}_arm_b"]["cost"],
                "arm_a_passed": primary[f"{t}_arm_a"]["passed"],
                "arm_a_duration": primary[f"{t}_arm_a"]["duration"],
            }
            for t in abl_tasks
        ],
        "planner_mean": statistics.mean(
            r["stages"]["1_PLANNER"]["duration"] for r in abl_rows
        ),
    }

    synthetic_b = {
        "resolved": scored["arm_b"]["resolved"]
        - tier3["arm_b_primary_scored"]["resolved"]
        + tier3["arm_b_ablation"]["resolved"],
        "passed": scored["arm_b"]["passed"]
        - tier3["arm_b_primary_scored"]["passed"]
        + tier3["arm_b_ablation"]["passed"],
        "total_tests": scored["arm_b"]["total_tests"],
        "total_duration": scored["arm_b"]["total_duration"]
        - tier3["arm_b_primary_scored"]["total_duration"]
        + tier3["arm_b_ablation"]["total_duration"],
        "total_cost": scored["arm_b"]["total_cost"]
        - tier3["arm_b_primary_scored"]["total_cost"]
        + tier3["arm_b_ablation"]["total_cost"],
    }

    ledger = [
        {
            "task": t,
            "arm_a": {
                "ratio": primary[f"{t}_arm_a"]["ratio"],
                "shadow_ratio": primary[f"{t}_arm_a"]["shadow_ratio"],
                "duration": primary[f"{t}_arm_a"]["duration"],
                "invalidated_by": primary[f"{t}_arm_a"]["invalidated_by"],
            },
            "arm_b": {
                "ratio": primary[f"{t}_arm_b"]["ratio"],
                "shadow_ratio": primary[f"{t}_arm_b"]["shadow_ratio"],
                "duration": primary[f"{t}_arm_b"]["duration"],
                "invalidated_by": primary[f"{t}_arm_b"]["invalidated_by"],
            },
        }
        for t in tasks
    ]

    return {
        "tasks": tasks,
        "planner_timeout_tasks": planner_timeout,
        "scored": scored,
        "shadow": shadow,
        "tests": tests,
        "stages": stage_table,
        "context": context,
        "conditional": cond,
        "tier3": tier3,
        "synthetic_arm_b": synthetic_b,
        "ledger": ledger,
        "stale_flags": {
            name: row["stale_flags"] for name, row in primary.items() if row["stale_flags"]
        },
    }


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def report(data: dict) -> str:
    out: list[str] = []
    add = out.append
    a, b = data["scored"]["arm_a"], data["scored"]["arm_b"]
    sa, sb = data["shadow"]["arm_a"], data["shadow"]["arm_b"]
    add("=== TIER 1 · PRE-REGISTERED SLA SCORING (N = 25 paired) ===")
    add(
        f"Resolution     A {a['resolved']}/{a['n']} ({pct(a['resolved']/a['n'])})"
        f"  B {b['resolved']}/{b['n']} ({pct(b['resolved']/b['n'])})"
        f"  McNemar b={data['tests']['mcnemar']['b']} c={data['tests']['mcnemar']['c']}"
        f" p={data['tests']['mcnemar']['p']:.5f}"
    )
    add(
        f"Mean ratio     A {pct(a['mean_ratio'])}  B {pct(b['mean_ratio'])}"
        f"  Wilcoxon n={data['tests']['ratio']['n']} W+={data['tests']['ratio']['w_plus']}"
        f" p={data['tests']['ratio']['p']:.6f}"
    )
    add(
        f"Pooled tests   A {a['passed']}/{a['total_tests']} ({pct(a['passed']/a['total_tests'])})"
        f"  B {b['passed']}/{b['total_tests']} ({pct(b['passed']/b['total_tests'])})"
    )
    add(
        f"Latency        A {a['mean_duration']:.1f}s  B {b['mean_duration']:.1f}s"
        f"  W+={data['tests']['duration']['w_plus']} p={data['tests']['duration']['p']:.2e}"
    )
    add(
        f"Tokens         A {a['mean_tokens']:,.0f}  B {b['mean_tokens']:,.0f}"
        f"  W+={data['tests']['tokens']['w_plus']} p={data['tests']['tokens']['p']:.5f}"
    )
    add(
        f"Cost           A ${a['total_cost']:.2f} (${a['mean_cost']:.4f}/task)"
        f"  B ${b['total_cost']:.2f} (${b['mean_cost']:.4f}/task)"
        f"  p={data['tests']['cost']['p']:.4f}"
    )
    add("")
    add("=== SHADOW · RAW ORACLE SCORING (no SLA / protocol gate) ===")
    add(
        f"Resolution     A {sa['resolved']}/{sa['n']}  B {sb['resolved']}/{sb['n']}"
        f"   Pooled A {sa['passed']}/{sa['total_tests']}  B {sb['passed']}/{sb['total_tests']}"
    )
    add(f"Mean ratio     A {pct(sa['mean_ratio'])}  B {pct(sb['mean_ratio'])}")
    add("")
    add("=== TIER 2 · STAGE TABLE ===")
    for row in data["stages"]:
        add(
            f"{row['label']:15} A {row['arm_a']['ok']}/{row['arm_a']['n']}"
            f" {row['arm_a']['mean_duration']:6.1f}s   "
            f"B {row['arm_b']['ok']}/{row['arm_b']['n']} {row['arm_b']['mean_duration']:6.1f}s"
        )
    ca, cb = data["context"]["arm_a"], data["context"]["arm_b"]
    add(
        f"Fresh input tokens  A {ca['fresh_input_tokens']:,}  B {cb['fresh_input_tokens']:,}"
        f"  (cache share A {pct(ca['cache_share'])} / B {pct(cb['cache_share'])})"
    )
    cond = data["conditional"]
    add(
        f"Conditional on planner success ({len(cond['tasks'])} tasks): "
        f"A {cond['arm_a']['resolved']}/{cond['arm_a']['n']} {pct(cond['arm_a']['mean_ratio'])}  "
        f"B {cond['arm_b']['resolved']}/{cond['arm_b']['n']} {pct(cond['arm_b']['mean_ratio'])}"
    )
    add("")
    add("=== TIER 3 · ABLATION (600s planner ceiling) ===")
    t3 = data["tier3"]
    for row in t3["per_task"]:
        add(
            f"{row['task']:18} scored {row['primary_scored_passed']:>2}/{row['total_tests']:<2}"
            f" shadow {row['primary_shadow_passed']:>2}/{row['total_tests']:<2}"
            f" ablation {row['ablation_passed']:>2}/{row['total_tests']:<2}"
            f" planner {row['ablation_planner']:6.1f}s total {row['ablation_duration']:7.1f}s"
            f" ${row['ablation_cost']:.4f}"
        )
    add(
        f"8-task totals: A scored {t3['arm_a_primary']['passed']}/{t3['arm_a_primary']['total_tests']}"
        f" ({t3['arm_a_primary']['resolved']}/8 resolved, {t3['arm_a_primary']['total_duration']:.1f}s,"
        f" ${t3['arm_a_primary']['total_cost']:.2f})"
    )
    add(
        f"               B primary shadow {t3['arm_b_primary_shadow']['passed']}"
        f"/{t3['arm_b_primary_shadow']['total_tests']}"
        f" ({t3['arm_b_primary_shadow']['resolved']}/8 resolved)"
    )
    add(
        f"               B ablation {t3['arm_b_ablation']['passed']}/{t3['arm_b_ablation']['total_tests']}"
        f" ({t3['arm_b_ablation']['resolved']}/8 resolved, {t3['arm_b_ablation']['total_duration']:.1f}s,"
        f" ${t3['arm_b_ablation']['total_cost']:.2f}, planner mean {t3['planner_mean']:.1f}s)"
    )
    syn = data["synthetic_arm_b"]
    add(
        f"Synthetic 25-task B: {syn['resolved']}/25, {syn['passed']}/{syn['total_tests']} tests,"
        f" {syn['total_duration']:.1f}s, ${syn['total_cost']:.2f}"
    )
    if data["stale_flags"]:
        add("")
        add("=== DROPPED STALE FLAGS (no longer reproduce under current patterns) ===")
        for name, codes in sorted(data["stale_flags"].items()):
            add(f"{name}: {', '.join(codes)}")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="write the machine-readable payload here")
    args = parser.parse_args()
    data = build()
    print(report(data))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
