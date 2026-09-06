#!/usr/bin/env python3
"""
Statistical Analysis and Report Generator for OMP vs. Multi-CLI Experiment.
Computes Paired Wilcoxon Signed-Rank Test, exact McNemar's Test, and Wilson Intervals.
"""

import argparse
import json
import math
import os
import sys

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../results"))
DEFAULT_MANIFEST_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../benchmarks/aider-python/manifest.json")
)
ALPHA = 0.05


class CompletenessError(Exception):
    """Strict N=manifest completeness gate failed (missing, extra, or unpaired tasks)."""

    def __init__(self, missing, extra, unpaired, expected_ids):
        self.missing = list(missing)
        self.extra = list(extra)
        self.unpaired = list(unpaired)
        self.expected_ids = list(expected_ids)
        parts = []
        if self.missing:
            parts.append(f"missing={self.missing}")
        if self.extra:
            parts.append(f"extra={self.extra}")
        if self.unpaired:
            parts.append(f"unpaired={self.unpaired}")
        detail = "; ".join(parts) if parts else "incomplete results"
        super().__init__(
            f"Strict completeness gate failed (expected {len(self.expected_ids)} manifest tasks): {detail}"
        )


def wilson_score_interval(k: int, n: int, confidence: float = 0.95):
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95%
    p = k / n
    denominator = 1 + z**2 / n
    centre_adjusted = p + z**2 / (2 * n)
    adjusted_std = math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    lower = max(0.0, (centre_adjusted - z * adjusted_std) / denominator)
    upper = min(1.0, (centre_adjusted + z * adjusted_std) / denominator)
    return round(lower * 100, 1), round(upper * 100, 1)


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exact two-sided McNemar test via binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # Sum binomial probabilities for x <= k with p=0.5
    prob_one_tail = 0.0
    for x in range(k + 1):
        prob_one_tail += math.comb(n, x) * (0.5**n)
    return min(1.0, 2 * prob_one_tail)


def _average_ranks(values):
    """1-based midranks; ties share the mean rank. Deterministic by (value, index)."""
    n = len(values)
    order = sorted(range(n), key=lambda i: (values[i], i))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _exact_signed_rank_p(ranks, w_plus):
    """Two-sided exact p-value of W+ under independent fair signs, via DP."""
    n = len(ranks)
    if n == 0:
        return 1.0
    scaled = [int(round(r * 2)) for r in ranks]
    w_scaled = int(round(w_plus * 2))
    max_sum = sum(scaled)
    counts = [0] * (max_sum + 1)
    counts[0] = 1
    running = 0
    for r in scaled:
        for s in range(running, -1, -1):
            counts[s + r] += counts[s]
        running += r
    total = 1 << n
    cdf = sum(counts[: w_scaled + 1])
    tail_right = sum(counts[w_scaled:])
    return min(1.0, 2.0 * min(cdf, tail_right) / total)


def wilcoxon_signed_rank(diffs):
    """
    Exact two-sided Wilcoxon signed-rank on paired differences.

    Zeros are dropped (Wilcoxon zero method). Tied |diff| values receive average
    ranks. The null distribution of W+ is enumerated by dynamic programming
    over the 2^n sign assignments.

    Returns dict with statistic (W+), p_value, n (nonzero), n_zeros.
    """
    diffs = list(diffs)
    zeros = [d for d in diffs if d == 0]
    nonzero = [d for d in diffs if d != 0]
    n_zeros = len(zeros)
    if not nonzero:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "n": 0,
            "n_zeros": n_zeros,
        }
    ranks = _average_ranks([abs(d) for d in nonzero])
    w_plus = sum(r for d, r in zip(nonzero, ranks) if d > 0)
    p_value = _exact_signed_rank_p(ranks, w_plus)
    return {
        "statistic": w_plus,
        "p_value": p_value,
        "n": len(nonzero),
        "n_zeros": n_zeros,
    }


def execution_token_count(execution):
    """Prefer execution.normalized_total_tokens; fall back to total_tokens."""
    if not isinstance(execution, dict):
        return 0
    tokens = execution.get("normalized_total_tokens")
    if tokens is not None:
        return tokens
    return execution.get("total_tokens", 0)


def load_manifest_task_ids(manifest_path):
    with open(manifest_path) as fh:
        manifest = json.load(fh)
    if not isinstance(manifest, list):
        raise ValueError(f"Manifest at {manifest_path} must be a list of task objects")
    return [item["task_id"] for item in manifest]


def _iter_result_paths(results_dir):
    for name in sorted(os.listdir(results_dir)):
        if name.endswith("_arm_a.json") or name.endswith("_arm_b.json"):
            yield os.path.join(results_dir, name)


def load_results_by_task(results_dir):
    by_task = {}
    if not os.path.isdir(results_dir):
        return by_task
    for path in _iter_result_paths(results_dir):
        with open(path) as fh:
            data = json.load(fh)
        tid = data["task_id"]
        arm = data["arm"]
        if tid not in by_task:
            by_task[tid] = {}
        by_task[tid][arm] = data
    return by_task


def completeness_issues(by_task, expected_ids):
    expected = set(expected_ids)
    present = set(by_task)
    unpaired = sorted(
        tid for tid, arms in by_task.items() if "arm_a" not in arms or "arm_b" not in arms
    )
    complete = {
        tid
        for tid, arms in by_task.items()
        if "arm_a" in arms and "arm_b" in arms
    }
    missing = sorted(expected - complete)
    extra = sorted(present - expected)
    return missing, extra, unpaired


def _metric_pair(by_task, tid, getter):
    return getter(by_task[tid]["arm_a"]), getter(by_task[tid]["arm_b"])


def _ratio(record):
    return record.get("verification", {}).get("ratio", 0.0)


def _passed(record):
    return bool(record.get("verification", {}).get("passed", False))


def _duration(record):
    return record.get("execution", {}).get("duration", 0.0)


def _tokens(record):
    return execution_token_count(record.get("execution", {}))


def _cost(record):
    return record.get("execution", {}).get("total_cost_usd", 0.0)


def _sig_label(p_value):
    return "STATISTICALLY SIGNIFICANT" if p_value < ALPHA else "NOT SIGNIFICANT"


def analyze(results_dir=None, manifest_path=None, require_complete=False, report=True):
    """
    Pairwise Arm A vs Arm B analysis.

    Cumulative mode (require_complete=False) scores whatever complete pairs exist.
    Strict final mode requires every manifest task_id to be present, paired, and
    exclusive of extras.

    Returns a structured dict. Prints the human report when report=True.
    """
    results_dir = os.path.abspath(results_dir or RESULTS_DIR)
    manifest_path = os.path.abspath(manifest_path or DEFAULT_MANIFEST_PATH)
    by_task = load_results_by_task(results_dir)

    expected_ids = None
    if require_complete:
        expected_ids = load_manifest_task_ids(manifest_path)
        missing, extra, unpaired = completeness_issues(by_task, expected_ids)
        if missing or extra or unpaired:
            raise CompletenessError(missing, extra, unpaired, expected_ids)

    paired_tasks = sorted(
        t for t, v in by_task.items() if "arm_a" in v and "arm_b" in v
    )

    if report:
        print("\n=======================================================")
        print(f"EXPERIMENT STATISTICAL ANALYSIS REPORT (N = {len(paired_tasks)} paired tasks)")
        print("=======================================================\n")

    if len(paired_tasks) == 0:
        if report:
            print("No paired tasks found in results yet. Run tasks first.")
        return {
            "n": 0,
            "paired_tasks": [],
            "results_dir": results_dir,
            "manifest_path": manifest_path,
            "require_complete": require_complete,
            "wilcoxon": {
                "ratio": wilcoxon_signed_rank([]),
                "duration": wilcoxon_signed_rank([]),
                "tokens": wilcoxon_signed_rank([]),
                "cost": wilcoxon_signed_rank([]),
            },
            "mcnemar": {"n_10": 0, "n_01": 0, "n_00": 0, "n_11": 0, "p_value": 1.0},
            "wilson": {
                "arm_a": {"k": 0, "n": 0, "lower": 0.0, "upper": 0.0},
                "arm_b": {"k": 0, "n": 0, "lower": 0.0, "upper": 0.0},
            },
            "means": {
                "ratio_a": 0.0,
                "ratio_b": 0.0,
                "duration_a": 0.0,
                "duration_b": 0.0,
                "tokens_a": 0.0,
                "tokens_b": 0.0,
                "cost_a": 0.0,
                "cost_b": 0.0,
            },
        }

    a_pass_count = 0
    b_pass_count = 0
    n_00 = 0
    n_01 = 0
    n_10 = 0
    n_11 = 0

    ratios_a, ratios_b = [], []
    durations_a, durations_b = [], []
    tokens_a, tokens_b = [], []
    costs_a, costs_b = [], []

    if report:
        print(f"{'Task ID':<20} | {'Arm A (Pass/Dur/Cost)':<26} | {'Arm B (Pass/Dur/Cost)':<26} | {'Delta Pass':<10}")
        print("-" * 90)

    for tid in paired_tasks:
        ra, rb = _metric_pair(by_task, tid, _ratio)
        pa, pb = _metric_pair(by_task, tid, _passed)
        da, db = _metric_pair(by_task, tid, _duration)
        ta, tb = _metric_pair(by_task, tid, _tokens)
        ca, cb = _metric_pair(by_task, tid, _cost)

        ratios_a.append(ra)
        ratios_b.append(rb)
        durations_a.append(da)
        durations_b.append(db)
        tokens_a.append(ta)
        tokens_b.append(tb)
        costs_a.append(ca)
        costs_b.append(cb)

        if pa:
            a_pass_count += 1
        if pb:
            b_pass_count += 1

        if pa and pb:
            n_11 += 1
        elif pa and not pb:
            n_10 += 1
        elif (not pa) and pb:
            n_01 += 1
        else:
            n_00 += 1

        if report:
            summary_a = f"{ra*100:4.0f}% | {da:5.1f}s | ${ca:6.4f}"
            summary_b = f"{rb*100:4.0f}% | {db:5.1f}s | ${cb:6.4f}"
            print(f"{tid:<20} | {summary_a:<26} | {summary_b:<26} | {(ra-rb)*100:>+5.1f}%")

    N = len(paired_tasks)
    w_lower_a, w_upper_a = wilson_score_interval(a_pass_count, N)
    w_lower_b, w_upper_b = wilson_score_interval(b_pass_count, N)
    mcnemar_p = mcnemar_exact_p(n_10, n_01)

    wilcoxon = {
        "ratio": wilcoxon_signed_rank([a - b for a, b in zip(ratios_a, ratios_b)]),
        "duration": wilcoxon_signed_rank([a - b for a, b in zip(durations_a, durations_b)]),
        "tokens": wilcoxon_signed_rank([a - b for a, b in zip(tokens_a, tokens_b)]),
        "cost": wilcoxon_signed_rank([a - b for a, b in zip(costs_a, costs_b)]),
    }

    mean_dur_a = sum(durations_a) / N
    mean_dur_b = sum(durations_b) / N
    mean_tok_a = sum(tokens_a) / N
    mean_tok_b = sum(tokens_b) / N
    mean_cost_a = sum(costs_a) / N
    mean_cost_b = sum(costs_b) / N
    mean_ratio_a = sum(ratios_a) / N
    mean_ratio_b = sum(ratios_b) / N

    if report:
        print("\n-----------------------------------------------------------------------------------------")
        print("PRIMARY COMPARATIVE METRICS (ARM A vs ARM B)")
        print("-----------------------------------------------------------------------------------------")
        print(
            f"Binary Resolution (P=1.0):   Arm A = {a_pass_count}/{N} ({a_pass_count/N*100:.1f}%) "
            f"[95% CI: {w_lower_a}% - {w_upper_a}%]"
        )
        print(
            f"                              Arm B = {b_pass_count}/{N} ({b_pass_count/N*100:.1f}%) "
            f"[95% CI: {w_lower_b}% - {w_upper_b}%]"
        )
        print(f"Mean Oracle Pass Ratio:       Arm A = {mean_ratio_a*100:.1f}% | Arm B = {mean_ratio_b*100:.1f}%")
        print(
            f"Mean Wall-Clock Latency:      Arm A = {mean_dur_a:.1f}s | Arm B = {mean_dur_b:.1f}s "
            f"(Delta: {mean_dur_a - mean_dur_b:+.1f}s)"
        )
        print(f"Mean Token Consumption:       Arm A = {mean_tok_a:,.0f} tokens | Arm B = {mean_tok_b:,.0f} tokens")
        print(
            f"Mean Standardized Cost (USD): Arm A = ${mean_cost_a:.4f} | Arm B = ${mean_cost_b:.4f} "
            f"(Delta: ${mean_cost_a - mean_cost_b:+.4f})"
        )
        print(f"Exact McNemar Test:           p = {mcnemar_p:.4f} ({_sig_label(mcnemar_p)})")
        print(
            f"Wilcoxon signed-rank (ratio): W+ = {wilcoxon['ratio']['statistic']:.1f}  "
            f"p = {wilcoxon['ratio']['p_value']:.4f} ({_sig_label(wilcoxon['ratio']['p_value'])})"
        )
        print(
            f"Wilcoxon signed-rank (duration): W+ = {wilcoxon['duration']['statistic']:.1f}  "
            f"p = {wilcoxon['duration']['p_value']:.4f} ({_sig_label(wilcoxon['duration']['p_value'])})"
        )
        print(
            f"Wilcoxon signed-rank (tokens): W+ = {wilcoxon['tokens']['statistic']:.1f}  "
            f"p = {wilcoxon['tokens']['p_value']:.4f} ({_sig_label(wilcoxon['tokens']['p_value'])})"
        )
        print(
            f"Wilcoxon signed-rank (cost):  W+ = {wilcoxon['cost']['statistic']:.1f}  "
            f"p = {wilcoxon['cost']['p_value']:.4f} ({_sig_label(wilcoxon['cost']['p_value'])})"
        )
        print("-----------------------------------------------------------------------------------------\n")

    return {
        "n": N,
        "paired_tasks": list(paired_tasks),
        "results_dir": results_dir,
        "manifest_path": manifest_path,
        "require_complete": require_complete,
        "wilcoxon": wilcoxon,
        "mcnemar": {
            "n_10": n_10,
            "n_01": n_01,
            "n_00": n_00,
            "n_11": n_11,
            "p_value": mcnemar_p,
        },
        "wilson": {
            "arm_a": {"k": a_pass_count, "n": N, "lower": w_lower_a, "upper": w_upper_a},
            "arm_b": {"k": b_pass_count, "n": N, "lower": w_lower_b, "upper": w_upper_b},
        },
        "means": {
            "ratio_a": mean_ratio_a,
            "ratio_b": mean_ratio_b,
            "duration_a": mean_dur_a,
            "duration_b": mean_dur_b,
            "tokens_a": mean_tok_a,
            "tokens_b": mean_tok_b,
            "cost_a": mean_cost_a,
            "cost_b": mean_cost_b,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="OMP vs Multi-CLI paired statistical analysis (Wilcoxon, McNemar, Wilson)"
    )
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Directory of *_arm_a.json / *_arm_b.json result files",
    )
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Path to the pre-registered task manifest JSON",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail unless every manifest task_id is present, paired, and exclusive of extras",
    )
    args = parser.parse_args(argv)
    try:
        analyze(
            results_dir=args.results_dir,
            manifest_path=args.manifest_path,
            require_complete=args.require_complete,
        )
    except CompletenessError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
