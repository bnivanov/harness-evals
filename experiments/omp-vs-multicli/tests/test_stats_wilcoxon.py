#!/usr/bin/env python3
"""Behavior tests for exact Wilcoxon signed-rank, McNemar, and Wilson helpers."""

import math
import os
import sys
import unittest

ANALYSIS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../analysis"))
sys.path.insert(0, ANALYSIS_DIR)

from calculate_stats import (  # noqa: E402
    mcnemar_exact_p,
    wilcoxon_signed_rank,
    wilson_score_interval,
)


def brute_force_wilcoxon(diffs):
    """Independent 2^n enumeration of the two-sided signed-rank p-value."""
    nonzero = [d for d in diffs if d != 0]
    n = len(nonzero)
    if n == 0:
        return 0.0, 1.0
    abs_vals = [abs(d) for d in nonzero]
    order = sorted(range(n), key=lambda i: (abs_vals[i], i))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs_vals[order[j + 1]] == abs_vals[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    w_obs = sum(r for d, r in zip(nonzero, ranks) if d > 0)
    total = 1 << n
    le = 0
    ge = 0
    for mask in range(total):
        w = 0.0
        for bit, r in enumerate(ranks):
            if mask & (1 << bit):
                w += r
        if w <= w_obs:
            le += 1
        if w >= w_obs:
            ge += 1
    p = min(1.0, 2.0 * min(le, ge) / total)
    return w_obs, p


class WilcoxonExactTests(unittest.TestCase):
    def test_all_zero_differences_yield_p_one(self):
        result = wilcoxon_signed_rank([0, 0, 0, 0])
        self.assertEqual(result["n"], 0)
        self.assertEqual(result["n_zeros"], 4)
        self.assertEqual(result["statistic"], 0.0)
        self.assertEqual(result["p_value"], 1.0)

    def test_empty_differences_yield_p_one(self):
        result = wilcoxon_signed_rank([])
        self.assertEqual(result["n"], 0)
        self.assertEqual(result["p_value"], 1.0)

    def test_known_small_exact_distribution_n3_all_positive(self):
        # n=3 distinct |d|, all positive: W+ = 6, only 1 of 8 signings, p = 2/8 = 0.25
        result = wilcoxon_signed_rank([1.0, 2.0, 4.0])
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["statistic"], 6.0)
        self.assertAlmostEqual(result["p_value"], 0.25)
        w_bf, p_bf = brute_force_wilcoxon([1.0, 2.0, 4.0])
        self.assertEqual(result["statistic"], w_bf)
        self.assertAlmostEqual(result["p_value"], p_bf)

    def test_known_small_exact_distribution_n3_balanced(self):
        # W+ = 3 for diffs (+1,+2,-4): ranks 1+2=3; two-sided p clips to 1.0
        result = wilcoxon_signed_rank([1.0, 2.0, -4.0])
        self.assertEqual(result["statistic"], 3.0)
        self.assertAlmostEqual(result["p_value"], 1.0)

    def test_known_small_exact_distribution_n4_all_positive(self):
        # n=4, W+=10, p = 2/16 = 0.125
        result = wilcoxon_signed_rank([1, 2, 3, 4])
        self.assertEqual(result["statistic"], 10.0)
        self.assertAlmostEqual(result["p_value"], 0.125)
        _, p_bf = brute_force_wilcoxon([1, 2, 3, 4])
        self.assertAlmostEqual(result["p_value"], p_bf)

    def test_tied_ranks_match_brute_force_enumeration(self):
        diffs = [1.0, 1.0, -2.0]
        result = wilcoxon_signed_rank(diffs)
        w_bf, p_bf = brute_force_wilcoxon(diffs)
        self.assertAlmostEqual(result["statistic"], w_bf)
        self.assertAlmostEqual(result["p_value"], p_bf)
        # midranks 1.5, 1.5, 3; two positives → W+ = 3.0
        self.assertAlmostEqual(result["statistic"], 3.0)

    def test_tied_ranks_all_positive_still_extreme(self):
        diffs = [5.0, 5.0, 5.0]
        result = wilcoxon_signed_rank(diffs)
        _, p_bf = brute_force_wilcoxon(diffs)
        self.assertAlmostEqual(result["p_value"], p_bf)
        self.assertAlmostEqual(result["p_value"], 0.25)
        self.assertAlmostEqual(result["statistic"], 6.0)

    def test_zeros_dropped_before_ranking(self):
        # Leading zeros must not consume ranks 1,2
        with_zeros = wilcoxon_signed_rank([0, 0, 1.0, 2.0, 4.0])
        without = wilcoxon_signed_rank([1.0, 2.0, 4.0])
        self.assertEqual(with_zeros["n_zeros"], 2)
        self.assertEqual(with_zeros["n"], without["n"])
        self.assertEqual(with_zeros["statistic"], without["statistic"])
        self.assertAlmostEqual(with_zeros["p_value"], without["p_value"])

    def test_two_sided_sign_flip_preserves_p(self):
        pos = wilcoxon_signed_rank([1.0, 3.0, 8.0, 2.0])
        neg = wilcoxon_signed_rank([-1.0, -3.0, -8.0, -2.0])
        self.assertAlmostEqual(pos["p_value"], neg["p_value"])
        self.assertGreater(pos["statistic"], 0.0)
        self.assertEqual(neg["statistic"], 0.0)


class McNemarWilsonTests(unittest.TestCase):
    def test_mcnemar_no_discordant_pairs(self):
        self.assertEqual(mcnemar_exact_p(0, 0), 1.0)

    def test_mcnemar_known_small_binomial(self):
        # b=3, c=0 → P(X<=0)=1/8, two-sided min(1, 2/8)=0.25
        self.assertAlmostEqual(mcnemar_exact_p(3, 0), 0.25)
        self.assertAlmostEqual(mcnemar_exact_p(0, 3), 0.25)

    def test_wilson_interval_bounds_unit_interval(self):
        lo, hi = wilson_score_interval(3, 3)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 100.0)
        self.assertLess(lo, hi)
        empty = wilson_score_interval(0, 0)
        self.assertEqual(empty, (0.0, 0.0))

    def test_wilson_known_k_n(self):
        # 3/3 should be a high interval that still leaves room below 100
        lo, hi = wilson_score_interval(3, 3)
        self.assertGreater(lo, 40.0)
        self.assertEqual(hi, 100.0)
        z = 1.95996
        p = 1.0
        n = 3
        denom = 1 + z**2 / n
        centre = p + z**2 / (2 * n)
        adj = math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
        expected_lo = max(0.0, (centre - z * adj) / denom)
        self.assertAlmostEqual(lo, round(expected_lo * 100, 1))


if __name__ == "__main__":
    unittest.main()
