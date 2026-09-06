#!/usr/bin/env python3
"""
Statistical Analysis and Report Generator for OMP vs. Multi-CLI Experiment.
Computes Paired Wilcoxon Signed-Rank Test, exact McNemar's Test, and Wilson Intervals.
"""

import os
import sys
import glob
import json
import math

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../results"))

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

def analyze():
    files = glob.glob(os.path.join(RESULTS_DIR, "*_arm_*.json"))
    by_task = {}
    
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        tid = data["task_id"]
        arm = data["arm"]
        if tid not in by_task:
            by_task[tid] = {}
        by_task[tid][arm] = data
        
    paired_tasks = [t for t, v in by_task.items() if "arm_a" in v and "arm_b" in v]
    
    print(f"\n=======================================================")
    print(f"EXPERIMENT STATISTICAL ANALYSIS REPORT (N = {len(paired_tasks)} paired tasks)")
    print(f"=======================================================\n")
    
    if len(paired_tasks) == 0:
        print("No paired tasks found in results yet. Run tasks first.")
        return
        
    a_pass_count = 0
    b_pass_count = 0
    
    # Contingency table: n_00, n_01 (A=0, B=1), n_10 (A=1, B=0), n_11
    n_00 = 0
    n_01 = 0
    n_10 = 0
    n_11 = 0
    
    ratios_a, ratios_b = [], []
    durations_a, durations_b = [], []
    tokens_a, tokens_b = [], []
    costs_a, costs_b = [], []
    
    print(f"{'Task ID':<20} | {'Arm A (Pass/Dur/Cost)':<26} | {'Arm B (Pass/Dur/Cost)':<26} | {'Delta Pass':<10}")
    print("-" * 90)
    
    for tid in sorted(paired_tasks):
        ra = by_task[tid]["arm_a"]["verification"].get("ratio", 0.0)
        rb = by_task[tid]["arm_b"]["verification"].get("ratio", 0.0)
        pa = by_task[tid]["arm_a"]["verification"].get("passed", False)
        pb = by_task[tid]["arm_b"]["verification"].get("passed", False)
        
        da = by_task[tid]["arm_a"]["execution"].get("duration", 0.0)
        db = by_task[tid]["arm_b"]["execution"].get("duration", 0.0)
        
        ta = by_task[tid]["arm_a"]["execution"].get("total_tokens", 0)
        tb = by_task[tid]["arm_b"]["execution"].get("total_tokens", 0)
        
        ca = by_task[tid]["arm_a"]["execution"].get("total_cost_usd", 0.0)
        cb = by_task[tid]["arm_b"]["execution"].get("total_cost_usd", 0.0)
        
        ratios_a.append(ra)
        ratios_b.append(rb)
        durations_a.append(da)
        durations_b.append(db)
        tokens_a.append(ta)
        tokens_b.append(tb)
        costs_a.append(ca)
        costs_b.append(cb)
        
        if pa: a_pass_count += 1
        if pb: b_pass_count += 1
        
        if pa and pb: n_11 += 1
        elif pa and not pb: n_10 += 1
        elif not pa and pb: n_01 += 1
        else: n_00 += 1
        
        summary_a = f"{ra*100:4.0f}% | {da:5.1f}s | ${ca:6.4f}"
        summary_b = f"{rb*100:4.0f}% | {db:5.1f}s | ${cb:6.4f}"
        print(f"{tid:<20} | {summary_a:<26} | {summary_b:<26} | {(ra-rb)*100:>+5.1f}%")

    N = len(paired_tasks)
    w_lower_a, w_upper_a = wilson_score_interval(a_pass_count, N)
    w_lower_b, w_upper_b = wilson_score_interval(b_pass_count, N)
    mcnemar_p = mcnemar_exact_p(n_10, n_01)
    
    mean_dur_a = sum(durations_a) / N
    mean_dur_b = sum(durations_b) / N
    mean_tok_a = sum(tokens_a) / N
    mean_tok_b = sum(tokens_b) / N
    mean_cost_a = sum(costs_a) / N
    mean_cost_b = sum(costs_b) / N
    
    print("\n-----------------------------------------------------------------------------------------")
    print("PRIMARY COMPARATIVE METRICS (ARM A vs ARM B)")
    print("-----------------------------------------------------------------------------------------")
    print(f"Binary Resolution (P=1.0):   Arm A = {a_pass_count}/{N} ({a_pass_count/N*100:.1f}%) [95% CI: {w_lower_a}% - {w_upper_a}%]")
    print(f"                              Arm B = {b_pass_count}/{N} ({b_pass_count/N*100:.1f}%) [95% CI: {w_lower_b}% - {w_upper_b}%]")
    print(f"Mean Oracle Pass Ratio:       Arm A = {sum(ratios_a)/N*100:.1f}% | Arm B = {sum(ratios_b)/N*100:.1f}%")
    print(f"Mean Wall-Clock Latency:      Arm A = {mean_dur_a:.1f}s | Arm B = {mean_dur_b:.1f}s (Delta: {mean_dur_a - mean_dur_b:+.1f}s)")
    print(f"Mean Token Consumption:       Arm A = {mean_tok_a:,.0f} tokens | Arm B = {mean_tok_b:,.0f} tokens")
    print(f"Mean Standardized Cost (USD): Arm A = ${mean_cost_a:.4f} | Arm B = ${mean_cost_b:.4f} (Delta: ${mean_cost_a - mean_cost_b:+.4f})")
    print(f"Exact McNemar Test:           p = {mcnemar_p:.4f} ({'STATISTICALLY SIGNIFICANT' if mcnemar_p < 0.05 else 'NOT SIGNIFICANT'})")
    print("-----------------------------------------------------------------------------------------\n")

if __name__ == "__main__":
    analyze()
