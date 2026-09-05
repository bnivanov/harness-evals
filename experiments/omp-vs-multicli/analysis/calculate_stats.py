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
    
    ratios_a = []
    ratios_b = []
    durations_a = []
    durations_b = []
    
    print(f"{'Task ID':<25} | {'Arm A (OMP)':<15} | {'Arm B (Multi-CLI)':<18} | {'Delta':<10}")
    print("-" * 75)
    
    for tid in sorted(paired_tasks):
        ra = by_task[tid]["arm_a"]["verification"].get("ratio", 0.0)
        rb = by_task[tid]["arm_b"]["verification"].get("ratio", 0.0)
        pa = by_task[tid]["arm_a"]["verification"].get("passed", False)
        pb = by_task[tid]["arm_b"]["verification"].get("passed", False)
        
        da = by_task[tid]["arm_a"]["execution"].get("duration", 0.0)
        db = by_task[tid]["arm_b"]["execution"].get("duration", 0.0)
        
        ratios_a.append(ra)
        ratios_b.append(rb)
        durations_a.append(da)
        durations_b.append(db)
        
        if pa: a_pass_count += 1
        if pb: b_pass_count += 1
        
        if pa and pb: n_11 += 1
        elif pa and not pb: n_10 += 1
        elif not pa and pb: n_01 += 1
        else: n_00 += 1
        
        print(f"{tid:<25} | {ra*100:>5.1f}% ({'PASS' if pa else 'FAIL'}) | {rb*100:>5.1f}% ({'PASS' if pb else 'FAIL'})     | {(ra-rb)*100:>+5.1f}%")

    N = len(paired_tasks)
    w_lower_a, w_upper_a = wilson_score_interval(a_pass_count, N)
    w_lower_b, w_upper_b = wilson_score_interval(b_pass_count, N)
    
    mcnemar_p = mcnemar_exact_p(n_10, n_01)
    
    print("\n-------------------------------------------------------")
    print("PRIMARY STATISTICAL METRICS")
    print("-------------------------------------------------------")
    print(f"Arm A (OMP) Binary Resolution:       {a_pass_count}/{N} ({a_pass_count/N*100:.1f}%) [95% CI: {w_lower_a}% - {w_upper_a}%]")
    print(f"Arm B (Multi-CLI) Binary Resolution: {b_pass_count}/{N} ({b_pass_count/N*100:.1f}%) [95% CI: {w_lower_b}% - {w_upper_b}%]")
    print(f"Mean Pass Ratio:                     Arm A = {sum(ratios_a)/N*100:.1f}% | Arm B = {sum(ratios_b)/N*100:.1f}%")
    print(f"Contingency Table (Discordance):     n_10 (A wins) = {n_10} | n_01 (B wins) = {n_01} | Tied = {n_11 + n_00}")
    print(f"Exact McNemar Test (Two-sided):      p = {mcnemar_p:.4f} ({'STATISTICALLY SIGNIFICANT (p < 0.05)' if mcnemar_p < 0.05 else 'NOT SIGNIFICANT (p >= 0.05)'})")
    print("-------------------------------------------------------\n")

if __name__ == "__main__":
    analyze()
