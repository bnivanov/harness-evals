#!/usr/bin/env python3
"""Render publication-grade charts and cover visuals for Workflow Bench Experiment 2.

Clean editorial style matching omp-model-bench:
- Paper background (#FAFAF8), hairline borders (#E2DFD8), crisp data-ink ratio.
- High-contrast typography using Apple Avenir Next and Menlo.
- 1600x640 for 5:2 Cover, 1600x900 for 16:9 analytical figures.
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "visuals" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCORED_PATH = BASE_DIR / "analysis" / "scored_matrix.json"

if not SCORED_PATH.is_file():
    raise SystemExit(
        f"Missing {SCORED_PATH.relative_to(BASE_DIR)}. "
        "Run: python3 analysis/score_matrix.py --json analysis/scored_matrix.json"
    )

with SCORED_PATH.open(encoding="utf-8") as handle:
    DATA = json.load(handle)

SCORED_A = DATA["scored"]["arm_a"]
SCORED_B = DATA["scored"]["arm_b"]
SHADOW_A = DATA["shadow"]["arm_a"]
SHADOW_B = DATA["shadow"]["arm_b"]
TESTS = DATA["tests"]
TIER3 = DATA["tier3"]
SYNTH_B = DATA["synthetic_arm_b"]


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def signif(p: float) -> str:
    if p < 1e-4:
        return "p < 0.0001*"
    return f"p = {p:.5f}*"

# Color Palette
BG = "#FAFAF8"
CARD = "#FFFFFF"
INK = "#16181D"
MUTED = "#5F6570"
FAINT = "#8A9099"
HAIR = "#E2DFD8"
TRACK = "#ECEAE3"
ARM_A_COLOR = "#0E7C72"  # Deep Teal for Unified OMP
ARM_B_COLOR = "#C4502B"  # Terracotta / Rust for Multi-CLI Swarm
ACCENT_BLUE = "#3B5BDB"
ACCENT_AMBER = "#D97706"
SUCCESS_GREEN = "#15803D"

SANS_PATH = "/System/Library/Fonts/Avenir Next.ttc"
MONO_PATH = "/System/Library/Fonts/Menlo.ttc"

def sans(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    weights = {"bold": 0, "demi": 2, "medium": 5, "regular": 7}
    return ImageFont.truetype(SANS_PATH, size, index=weights.get(weight, 7))

def mono(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(MONO_PATH, size, index=1 if bold else 0)

# --------------------------------------------------------------------------
# 1. Cover Image (1600 x 640, 5:2 Aspect Ratio)
# --------------------------------------------------------------------------
def render_cover():
    width, height = 1600, 640
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "WORKFLOW BENCH · EXPERIMENT 2", font=mono(18, True), fill=ARM_A_COLOR)
    draw.text((1520, 50), "N=25 PAIRED TASKS · 50 RUNS + 8-TASK ABLATION", font=mono(16, True), fill=FAINT, anchor="ra")
    draw.line((80, 80, 1520, 80), fill=HAIR, width=2)

    draw.text((80, 110), "Why One Harness, Many Models", font=sans(56, "bold"), fill=INK)
    draw.text((80, 180), "Beats Multiple Orchestrated Ones", font=sans(56, "bold"), fill=INK)

    draw.text((80, 260), "A Head-to-Head Empirical Benchmark of Unified Session Orchestration (OMP)", font=sans(24, "medium"), fill=MUTED)
    draw.text((80, 295), "vs. a Disaggregated Vendor CLI Swarm Across 25 Software Engineering Tasks", font=sans(24, "regular"), fill=MUTED)

    # Stat Card 1
    draw.rounded_rectangle((80, 360, 510, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 385), "PRIMARY MATRIX RESOLUTION", font=mono(14, True), fill=FAINT)
    res_a = SCORED_A["resolved"] / SCORED_A["n"]
    res_b = SCORED_B["resolved"] / SCORED_B["n"]
    draw.text((110, 415), f"{pct(res_a, 0)} vs {pct(res_b, 0)}", font=sans(42, "bold"), fill=ARM_A_COLOR)
    draw.text((110, 480), f"OMP wins +{(res_a - res_b) * 100:.1f} pts ({signif(TESTS['mcnemar']['p'])})", font=sans(16, "medium"), fill=MUTED)
    draw.text((110, 505), "Exact McNemar test under strict 300s SLA", font=sans(14), fill=FAINT)

    # Stat Card 2
    draw.rounded_rectangle((540, 360, 970, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((570, 385), "MEAN WALL-CLOCK LATENCY", font=mono(14, True), fill=FAINT)
    draw.text((570, 415), f"{SCORED_A['mean_duration']:.0f}s vs {SCORED_B['mean_duration']:.0f}s", font=sans(42, "bold"), fill=ACCENT_BLUE)
    draw.text((570, 480), f"OMP is {SCORED_B['mean_duration'] - SCORED_A['mean_duration']:.1f}s faster per task ({signif(TESTS['duration']['p'])})", font=sans(16, "medium"), fill=MUTED)
    draw.text((570, 505), "Paired Wilcoxon signed-rank significance", font=sans(14), fill=FAINT)

    # Stat Card 3
    draw.rounded_rectangle((1000, 360, 1520, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((1030, 385), "THE MULTI-CLI ABLATION TAX", font=mono(14, True), fill=FAINT)
    draw.text((1030, 415), "+28.9% Time, +22.8% Cost", font=sans(34, "bold"), fill=ARM_B_COLOR)
    draw.text((1030, 480), "Multi-CLI recovers to 99.3% pass when unconstrained,", font=sans(15, "medium"), fill=MUTED)
    draw.text((1030, 505), "but pays an ongoing overhead tax to match OMP", font=sans(14), fill=FAINT)

    draw.line((80, 580, 1520, 580), fill=HAIR, width=1)
    draw.text((80, 605), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT)
    draw.text((1520, 605), "Autonomous SWE Lifecycle: Grok 4.6 (Plan) → GPT-5.6 Luna (Code) → Gemini 3.8 Flash (Review)", font=mono(13), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "01-cover.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 2. Architecture Comparison (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_architecture():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "TOPOLOGY ARCHITECTURE · ARMS A & B", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Two Approaches to Multi-Model Software Engineering", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Comparing internal in-process harness handoffs against external shell-piped CLI boundaries", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # Left Column: Arm A
    draw.rounded_rectangle((80, 210, 770, 810), radius=14, fill=CARD, outline=ARM_A_COLOR, width=3)
    draw.rectangle((80, 210, 770, 270), fill=ARM_A_COLOR)
    draw.text((110, 230), "ARM A: UNIFIED OMP HARNESS (IN-PROCESS)", font=mono(18, True), fill="#FFFFFF")

    draw.text((110, 290), "Continuous Execution Session Context", font=sans(24, "bold"), fill=INK)
    draw.text((110, 325), "One process wraps all four frontier model stages seamlessly:", font=sans(16), fill=MUTED)

    stages_a = [
        ("Stage 1: Planner", "xai-oauth/grok-4.6 @ max", "Structural grep/glob inspection; in-process thinking"),
        ("Stage 2: Worker Initial", "openai-codex/gpt-5.6-luna @ max", "Hashline edits; inherited project memory"),
        ("Stage 3: Reviewer", "google-antigravity/gemini-3.8-flash @ max", "In-memory test audit & fix identification"),
        ("Stage 4: Worker Refine", "openai-codex/gpt-5.6-luna @ max", "Targeted delta patch without context re-read")
    ]
    for i, (st, mod, desc) in enumerate(stages_a):
        y = 370 + i * 85
        draw.rounded_rectangle((110, y, 740, y + 70), radius=8, fill="#F0FDF4", outline="#BBF7D0", width=1)
        draw.text((130, y + 12), st, font=sans(17, "bold"), fill=ARM_A_COLOR)
        draw.text((730, y + 14), mod, font=mono(13), fill=MUTED, anchor="ra")
        draw.text((130, y + 40), desc, font=sans(14), fill=INK)

    draw.line((110, 725, 740, 725), fill=HAIR, width=1)
    draw.text((110, 740), "• In-Process Tooling: Native hashline edit & grep tools (no subshell drag)", font=sans(14), fill=MUTED)
    ctx_a = DATA["context"]["arm_a"]
    draw.text((110, 765), f"• Persistent Context: {pct(ctx_a['cache_share'])} of input tokens served from cache", font=sans(14), fill=MUTED)

    # Right Column: Arm B
    draw.rounded_rectangle((830, 210, 1520, 810), radius=14, fill=CARD, outline=ARM_B_COLOR, width=3)
    draw.rectangle((830, 210, 1520, 270), fill=ARM_B_COLOR)
    draw.text((860, 230), "ARM B: MULTI-CLI SWARM (DISAGGREGATED)", font=mono(18, True), fill="#FFFFFF")

    draw.text((860, 290), "Subprocess Chaining Over Disk Artifacts", font=sans(24, "bold"), fill=INK)
    draw.text((860, 325), "Separate standalone CLI binaries spawned per stage:", font=sans(16), fill=MUTED)

    stages_b = [
        ("Stage 1: Planner CLI", "grok 1.0.5 binary (--effort xhigh)", "Spawns subshell; serializes 01_PLAN.md to disk"),
        ("Stage 2: Worker CLI", "codex 0.152.0 binary (@ max)", "Re-reads whole repo + plan; edits source"),
        ("Stage 3: Reviewer CLI", "agy 1.1.27 binary (@ high)", "Independent container; writes 02_REVIEW.md"),
        ("Stage 4: Worker Refine CLI", "codex 0.152.0 binary (@ max)", "Fresh subprocess; re-reads plan + review + repo")
    ]
    for i, (st, mod, desc) in enumerate(stages_b):
        y = 370 + i * 85
        draw.rounded_rectangle((860, y, 1490, y + 70), radius=8, fill="#FEF2F2", outline="#FECACA", width=1)
        draw.text((880, y + 12), st, font=sans(17, "bold"), fill=ARM_B_COLOR)
        draw.text((1480, y + 14), mod, font=mono(13), fill=MUTED, anchor="ra")
        draw.text((880, y + 40), desc, font=sans(14), fill=INK)

    draw.line((860, 725, 1490, 725), fill=HAIR, width=1)
    draw.text((860, 740), "• Process Boundary Hops: 4 independent binary boots, node/pty startup tax", font=sans(14), fill=MUTED)
    ctx_b = DATA["context"]["arm_b"]
    fresh_ratio = ctx_b["fresh_input_tokens"] / ctx_a["fresh_input_tokens"]
    draw.text((860, 765), f"• Context Re-Inflation: {ctx_b['fresh_input_tokens'] / 1e6:.2f}M fresh input tokens ({fresh_ratio:.1f}x Arm A)", font=sans(14), fill=MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Workflow Bench · Experiment 2", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "02-architecture-topologies.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 3. Primary Benchmark Results (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_primary_results():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "PRIMARY STATISTICAL GATE · PRE-REGISTERED N=25 MATRIX", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Head-to-Head Performance Under Production SLAs", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "300s Stage SLA Ceiling, Zero-Drop Pre-Registered Protocol, 50 Total Runs", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    res_a = SCORED_A["resolved"] / SCORED_A["n"]
    res_b = SCORED_B["resolved"] / SCORED_B["n"]
    metrics = [
        (
            "Binary Resolution (R=1.0)",
            pct(res_a),
            pct(res_b),
            f"Exact McNemar: p = {TESTS['mcnemar']['p']:.5f}*",
            f"Arm A resolves {SCORED_A['resolved']}/{SCORED_A['n']} tasks vs {SCORED_B['resolved']}/{SCORED_B['n']}"
            f" in Arm B (+{(res_a - res_b) * 100:.1f} pts)",
        ),
        (
            "Oracle Pass Ratio (R)",
            pct(SCORED_A["mean_ratio"]),
            pct(SCORED_B["mean_ratio"]),
            f"Paired Wilcoxon: p = {TESTS['ratio']['p']:.6f}*",
            f"Arm A passes {SCORED_A['passed']}/{SCORED_A['total_tests']} unit tests vs"
            f" {SCORED_B['passed']}/{SCORED_B['total_tests']} ({TESTS['ratio']['n']} non-tied pairs)",
        ),
        (
            "Mean Wall-Clock Latency",
            f"{SCORED_A['mean_duration']:.1f}s",
            f"{SCORED_B['mean_duration']:.1f}s",
            f"Paired Wilcoxon: {signif(TESTS['duration']['p'])}",
            f"Arm A is {SCORED_B['mean_duration'] - SCORED_A['mean_duration']:.1f}s faster per task"
            f" (saves {(SCORED_B['total_duration'] - SCORED_A['total_duration']) / 3600:.1f} hours across 25 tasks)",
        ),
        (
            "Mean Token Consumption",
            f"{SCORED_A['mean_tokens'] / 1e6:.2f}M",
            f"{SCORED_B['mean_tokens'] / 1e6:.2f}M",
            f"Paired Wilcoxon: p = {TESTS['tokens']['p']:.5f}*",
            f"Arm B feeds {DATA['context']['arm_b']['fresh_input_tokens'] / 1e6:.2f}M fresh input tokens"
            f" vs Arm A's {DATA['context']['arm_a']['fresh_input_tokens'] / 1e6:.2f}M",
        ),
    ]

    for i, (title, val_a, val_b, stat, desc) in enumerate(metrics):
        col = i % 2
        row = i // 2
        x = 80 + col * 730
        y = 210 + row * 300

        draw.rounded_rectangle((x, y, x + 710, y + 270), radius=12, fill=CARD, outline=HAIR, width=2)
        draw.text((x + 30, y + 25), title.upper(), font=mono(15, True), fill=FAINT)

        draw.text((x + 30, y + 65), "Arm A (OMP)", font=sans(16, "bold"), fill=ARM_A_COLOR)
        draw.text((x + 220, y + 60), val_a, font=sans(28, "bold"), fill=ARM_A_COLOR)

        draw.text((x + 30, y + 115), "Arm B (Multi-CLI)", font=sans(16, "bold"), fill=ARM_B_COLOR)
        draw.text((x + 220, y + 110), val_b, font=sans(28, "bold"), fill=ARM_B_COLOR)

        draw.line((x + 30, y + 160, x + 680, y + 160), fill=HAIR, width=1)
        draw.text((x + 30, y + 180), stat, font=mono(15, True), fill=SUCCESS_GREEN if "*" in stat else MUTED)
        draw.text((x + 30, y + 215), desc, font=sans(14), fill=MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), f"Raw-oracle shadow view (no SLA / protocol gate): Arm A {SHADOW_A['resolved']}/{SHADOW_A['n']} tasks, {SHADOW_A['passed']}/{SHADOW_A['total_tests']} tests  ·  Arm B {SHADOW_B['resolved']}/{SHADOW_B['n']}, {SHADOW_B['passed']}/{SHADOW_B['total_tests']}", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "03-primary-benchmark-results.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 4. Stage Breakdown & Parity Audit (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_stage_parity():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "TIER 2 ANALYSIS · MODEL BEHAVIOR & STAGE ISOLATION", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Is Standalone CLI Inferior, or Did Grok Just Timeout?", font=sans(40, "bold"), fill=INK)
    cond = DATA["conditional"]
    cond_a = cond["arm_a"]
    draw.text((80, 140), f"Auditing stage-by-stage model resolution and the exact {pct(cond_a['mean_ratio'])} downstream parity it exposes", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    draw.rounded_rectangle((80, 210, 1520, 310), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((110, 230), f"THE CONDITIONAL PARITY FINDING ({cond_a['n']} MATCHED TASKS)", font=mono(16, True), fill=SUCCESS_GREEN)
    draw.text((110, 260), f"When Grok Stage 1 delivered a plan, both arms scored {pct(cond_a['mean_ratio'])} - identically, task by task ({cond_a['resolved']}/{cond_a['n']} resolutions each).", font=sans(20, "bold"), fill=INK)
    draw.text((110, 285), "Codex Luna (Worker) and Gemini Flash (Reviewer) performed identically across both harness substrates.", font=sans(16), fill=MUTED)

    y_table = 340
    headers = [("STAGE", 80), ("MODEL ROLE", 320), ("ARM A (OMP)", 680), ("ARM B (MULTI-CLI)", 980), ("VERDICT", 1300)]
    for h, x in headers:
        draw.text((x, y_table), h, font=mono(15, True), fill=FAINT)
    draw.line((80, y_table + 25, 1520, y_table + 25), fill=HAIR, width=2)

    stage_verdicts = {
        "1_PLANNER": "Grok CLI: 8 timeouts",
        "2_WORKER_INITIAL": "Full code parity",
        "3_REVIEWER": "Full audit parity",
        "4_WORKER_REFINE": "Parity when planned",
    }
    stage_models = {
        "1_PLANNER": "Grok 4.6",
        "2_WORKER_INITIAL": "GPT-5.6 Luna @ max",
        "3_REVIEWER": "Gemini 3.8 Flash",
        "4_WORKER_REFINE": "GPT-5.6 Luna @ max",
    }
    rows = [
        (
            f"Stage {idx + 1}: {row['label']}",
            stage_models[row["stage"]],
            f"{row['arm_a']['ok']}/{row['arm_a']['n']} ({pct(row['arm_a']['ok'] / row['arm_a']['n'], 0)}) · {row['arm_a']['mean_duration']:.1f}s",
            f"{row['arm_b']['ok']}/{row['arm_b']['n']} ({pct(row['arm_b']['ok'] / row['arm_b']['n'], 0)}) · {row['arm_b']['mean_duration']:.1f}s",
            stage_verdicts[row["stage"]],
        )
        for idx, row in enumerate(DATA["stages"])
    ]

    for idx, (st, mod, res_a, res_b, verd) in enumerate(rows):
        y = y_table + 45 + idx * 80
        draw.rounded_rectangle((80, y - 10, 1520, y + 55), radius=8, fill=CARD, outline=HAIR, width=1)
        draw.text((100, y + 12), st, font=sans(17, "bold"), fill=INK)
        draw.text((320, y + 12), mod, font=mono(14), fill=MUTED)
        draw.text((680, y + 12), res_a, font=sans(16, "bold"), fill=ARM_A_COLOR)
        draw.text((980, y + 12), res_b, font=sans(16, "bold"), fill=ARM_B_COLOR)
        draw.text((1300, y + 12), verd, font=mono(14, True), fill=ARM_B_COLOR if "timeouts" in verd else SUCCESS_GREEN)

    draw.text((80, 720), "Why did Grok CLI timeout in Standalone mode?", font=sans(22, "bold"), fill=INK)
    draw.text((80, 755), f"In OMP, Grok operated with direct in-process tool bindings, completing plans in {DATA['stages'][0]['arm_a']['mean_duration']:.1f}s on average.", font=sans(16), fill=MUTED)
    draw.text((80, 780), "In standalone CLI mode, Grok spawned subshells per tool turn, accumulating latency until it breached the 300s ceiling on 8 tasks.", font=sans(16), fill=MUTED)
    draw.text((80, 805), f"Plan-less downstream stages were resilient: they still passed {TIER3['arm_b_primary_shadow']['passed']}/{TIER3['arm_b_primary_shadow']['total_tests']} oracle tests on those 8 tasks, but every run scored 0 under the SLA.", font=sans(16), fill=MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Stage telemetry verified via native turn.completed and usage payloads", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "04-stage-parity-breakdown.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 5. Ablation Task Breakdown (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_ablation_tasks():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "TIER 3 ABLATION · 8 TIMED-OUT TASKS EVALUATED WITH 600s CEILING", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "What the Extended Runway Actually Recovered", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "SLA-scored zeros next to the raw oracle score each run had already earned before it missed the deadline", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    y_table = 210
    headers = [
        ("TASK ID", 100),
        ("SLA SCORED", 300),
        ("RAW ORACLE", 430),
        ("600s ABLATION", 580),
        ("PLAN DUR", 800),
        ("TOTAL DUR", 950),
        ("COST", 1100),
        ("WHAT CHANGED", 1250),
    ]
    for h, x in headers:
        draw.text((x, y_table), h, font=mono(13, True), fill=FAINT)
    draw.line((80, y_table + 25, 1520, y_table + 25), fill=HAIR, width=2)

    for idx, row in enumerate(TIER3["per_task"]):
        y = y_table + 45 + idx * 58
        total = row["total_tests"]
        gained = row["ablation_passed"] - row["primary_shadow_passed"]
        verdict = "Accuracy gain" if gained > 0 else "SLA gate only"
        draw.rounded_rectangle((80, y - 8, 1520, y + 42), radius=6, fill=CARD, outline=HAIR, width=1)
        draw.text((100, y + 8), row["task"], font=mono(15, True), fill=INK)
        draw.text((300, y + 8), f"0 / {total}", font=sans(16, "bold"), fill=ARM_B_COLOR)
        draw.text((430, y + 8), f"{row['primary_shadow_passed']} / {total}", font=sans(16), fill=FAINT)
        draw.text(
            (580, y + 8),
            f"{row['ablation_passed']} / {total} ({row['ablation_passed'] / total * 100:.1f}%)",
            font=sans(16, "bold"),
            fill=SUCCESS_GREEN,
        )
        draw.text((800, y + 8), f"{row['ablation_planner']:.1f}s", font=mono(15), fill=MUTED)
        draw.text((950, y + 8), f"{row['ablation_duration']:.1f}s", font=mono(15), fill=MUTED)
        draw.text((1100, y + 8), f"${row['ablation_cost']:.4f}", font=mono(15), fill=MUTED)
        draw.text((1250, y + 8), verdict, font=sans(15, "bold"), fill=SUCCESS_GREEN if gained > 0 else FAINT)

    # Summary bar at bottom
    scored_b = TIER3["arm_b_primary_scored"]
    shadow_b = TIER3["arm_b_primary_shadow"]
    abl_b = TIER3["arm_b_ablation"]
    y_sum = y_table + 45 + 8 * 58 + 15
    draw.rounded_rectangle((80, y_sum, 1520, y_sum + 70), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((100, y_sum + 25), "TOTALS", font=mono(16, True), fill=INK)
    draw.text((300, y_sum + 22), f"0 / {scored_b['total_tests']}", font=sans(19, "bold"), fill=ARM_B_COLOR)
    draw.text((430, y_sum + 22), f"{shadow_b['passed']} / {shadow_b['total_tests']}", font=sans(19), fill=FAINT)
    draw.text(
        (580, y_sum + 20),
        f"{abl_b['passed']} / {abl_b['total_tests']} ({abl_b['passed'] / abl_b['total_tests'] * 100:.1f}%)",
        font=sans(21, "bold"),
        fill=SUCCESS_GREEN,
    )
    draw.text((800, y_sum + 25), f"mean {TIER3['planner_mean']:.1f}s", font=mono(14), fill=MUTED)
    draw.text((950, y_sum + 25), f"{abl_b['total_duration']:.1f}s", font=mono(14), fill=MUTED)
    draw.text((1100, y_sum + 25), f"${abl_b['total_cost']:.2f}", font=mono(14), fill=MUTED)
    draw.text((1250, y_sum + 25), f"{abl_b['resolved']} / 8 resolved", font=sans(15, "bold"), fill=SUCCESS_GREEN)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Ablation run recorded under runs/ablation-extended-grok/", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "05-ablation-task-breakdown.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 6. Ablation Head-to-Head & The Multi-CLI Tax (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_ablation_tax():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 50), "TIER 3 ABLATION · EXTENDED HORIZON (600s CEILING)", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "The Multi-CLI Tax: What Accuracy Parity Actually Costs", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Comparing Unified OMP against Multi-CLI across the 8 tasks and the full synthetic 25-task matrix", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # Card 1: 8-Task Direct Comparison
    draw.rounded_rectangle((80, 210, 770, 505), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 235), "1. 8-TASK HEAD-TO-HEAD (ABLATION SUBSET)", font=mono(15, True), fill=ARM_A_COLOR)

    a8 = TIER3["arm_a_primary"]
    b8 = TIER3["arm_b_ablation"]
    lat_delta = b8["total_duration"] - a8["total_duration"]
    cost_delta = b8["total_cost"] - a8["total_cost"]
    h2h = [
        (
            "Oracle Test Pass Ratio",
            f"{a8['passed']} / {a8['total_tests']} ({a8['passed'] / a8['total_tests'] * 100:.1f}%)",
            f"{b8['passed']} / {b8['total_tests']} ({b8['passed'] / b8['total_tests'] * 100:.1f}%)",
            f"Multi-CLI +{(b8['passed'] - a8['passed']) / a8['total_tests'] * 100:.1f} pts",
        ),
        (
            "Binary Task Resolution",
            f"{a8['resolved']} / 8 ({a8['resolved'] / 8 * 100:.1f}%)",
            f"{b8['resolved']} / 8 ({b8['resolved'] / 8 * 100:.1f}%)",
            f"Multi-CLI +{b8['resolved'] - a8['resolved']} task",
        ),
        (
            "Cumulative Wall Latency",
            f"{a8['total_duration']:,.1f}s ({a8['total_duration'] / 60:.1f}m)",
            f"{b8['total_duration']:,.1f}s ({b8['total_duration'] / 60:.1f}m)",
            f"Multi-CLI +{lat_delta / 60:.1f}m (+{lat_delta / a8['total_duration'] * 100:.1f}%)",
        ),
        (
            "Cumulative Dollar Spend",
            f"${a8['total_cost']:.2f}",
            f"${b8['total_cost']:.2f}",
            f"Multi-CLI +${cost_delta:.2f} (+{cost_delta / a8['total_cost'] * 100:.1f}%)",
        ),
    ]
    for i, (m, a, b, pen) in enumerate(h2h):
        y = 275 + i * 56
        draw.text((110, y), m, font=sans(15, "bold"), fill=INK)
        draw.text((740, y + 2), pen, font=sans(12, "bold"), fill=MUTED, anchor="ra")
        draw.text((110, y + 24), f"OMP {a}", font=mono(12), fill=ARM_A_COLOR)
        draw.text((400, y + 24), f"Multi-CLI {b}", font=mono(12), fill=ARM_B_COLOR)

    # Card 2: Key Finding
    draw.rounded_rectangle((830, 210, 1520, 505), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((860, 235), "2. THE ARCHITECTURAL TAX DEFINED", font=mono(15, True), fill=ARM_B_COLOR)
    draw.text((860, 275), f"Why does Multi-CLI pay {lat_delta / a8['total_duration'] * 100:.1f}% more latency and {cost_delta / a8['total_cost'] * 100:.1f}% more cost?", font=sans(16, "bold"), fill=INK)
    draw.text((860, 310), "• Subprocess Boot Overhead: 4 separate runtime initializations per task.", font=sans(14), fill=MUTED)
    draw.text((860, 340), "• Cold Context Reads: Intermediate markdown handoffs force cold token reads.", font=sans(14), fill=MUTED)
    draw.text((860, 370), "• Subshell Churn: Standalone CLI tool turns spawn nested child shells.", font=sans(14), fill=MUTED)
    draw.text((860, 410), "In Unified OMP, shared session context and native tools bypass these costs.", font=sans(14, "medium"), fill=ARM_A_COLOR)

    # Bottom Synthesis Table: All 25 Tasks Synthetic Comparison
    draw.rounded_rectangle((80, 510, 1520, 800), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 535), "SYNTHETIC N=25 MATRIX (OMP vs UNCONSTRAINED MULTI-CLI ACROSS ALL 25 TASKS)", font=mono(15, True), fill=FAINT)

    cols_syn = [
        ("METRIC", 110),
        ("ARM A (UNIFIED OMP)", 480),
        ("ARM B (EXTENDED CLI)", 880),
        ("ARCHITECTURAL DELTA", 1220)
    ]
    for c, x in cols_syn:
        draw.text((x, 570), c, font=mono(14, True), fill=FAINT)
    draw.line((110, 595, 1490, 595), fill=HAIR, width=1)

    syn_a_res = SCORED_A["resolved"]
    syn_lat_delta = SYNTH_B["total_duration"] - SCORED_A["total_duration"]
    syn_cost_delta = SYNTH_B["total_cost"] - SCORED_A["total_cost"]
    syn_rows = [
        (
            "Binary Task Resolution (R=1.0)",
            f"{syn_a_res} / 25 ({syn_a_res / 25 * 100:.1f}%)",
            f"{SYNTH_B['resolved']} / 25 ({SYNTH_B['resolved'] / 25 * 100:.1f}%)",
            f"Parity (Delta = {SYNTH_B['resolved'] - syn_a_res} task)",
        ),
        (
            "Oracle Test Pass Ratio",
            f"{SCORED_A['passed']} / {SCORED_A['total_tests']} ({SCORED_A['passed'] / SCORED_A['total_tests'] * 100:.1f}%)",
            f"{SYNTH_B['passed']} / {SYNTH_B['total_tests']} ({SYNTH_B['passed'] / SYNTH_B['total_tests'] * 100:.1f}%)",
            f"Parity (Delta = {SYNTH_B['passed'] - SCORED_A['passed']} unit tests)",
        ),
        (
            "Total Benchmark Wall Latency",
            f"{SCORED_A['total_duration']:,.1f}s ({SCORED_A['total_duration'] / 60:.1f} min)",
            f"{SYNTH_B['total_duration']:,.1f}s ({SYNTH_B['total_duration'] / 60:.1f} min)",
            f"OMP is {syn_lat_delta / 60:.1f} min FASTER (-{syn_lat_delta / SYNTH_B['total_duration'] * 100:.1f}%)",
        ),
        (
            "Total Standardized Spend",
            f"${SCORED_A['total_cost']:.2f}",
            f"${SYNTH_B['total_cost']:.2f}",
            f"OMP is ${syn_cost_delta:.2f} CHEAPER (-{syn_cost_delta / SYNTH_B['total_cost'] * 100:.1f}%)",
        ),
    ]
    for idx, (m, a, b, d) in enumerate(syn_rows):
        y = 615 + idx * 42
        draw.text((110, y), m, font=sans(16, "bold"), fill=INK)
        draw.text((480, y), a, font=mono(15), fill=ARM_A_COLOR)
        draw.text((880, y), b, font=mono(15), fill=ARM_B_COLOR)
        draw.text((1220, y), d, font=sans(15, "bold"), fill=ARM_A_COLOR if "OMP is" in d else MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 820), f"Baseline for the 8-task block under the 300s regime: Multi-CLI's raw oracle score was already {TIER3['arm_b_primary_shadow']['passed']}/{TIER3['arm_b_primary_shadow']['total_tests']} before the SLA zeroed it.", font=sans(13), fill=MUTED)
    draw.text((80, 865), "Workflow Bench · Experiment 2  ·  Ablation Study", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "06-ablation-head-to-head-tax.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 7. Complete 25-Task Ledger (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_full_ledger():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    draw.text((80, 45), "PRIMARY BENCHMARK MATRIX · FULL 25-TASK PAIRED LEDGER", font=mono(15, True), fill=FAINT)
    draw.text((80, 75), "Per-Task Outcome Ledger Under 300s SLA", font=sans(36, "bold"), fill=INK)
    draw.line((80, 125, 1520, 125), fill=HAIR, width=2)
    ledger = DATA["ledger"]

    def cells(entry: dict) -> tuple[str, str, str]:
        a, b = entry["arm_a"], entry["arm_b"]
        label_a = f"{a['ratio'] * 100:.0f}% ({a['duration']:.1f}s)"
        label_b = f"{b['ratio'] * 100:.0f}% ({b['duration']:.1f}s)"
        if a["ratio"] == b["ratio"]:
            outcome = "Both invalidated" if a["invalidated_by"] and b["invalidated_by"] else "Parity"
        elif a["ratio"] > b["ratio"]:
            outcome = "OMP win (CLI timeout)" if b["invalidated_by"] else "OMP win"
        else:
            outcome = "Multi-CLI win"
        return label_a, label_b, outcome

    split = 13
    columns = ((80, 760, ledger[:split], 90), (800, 1520, ledger[split:], 810))
    for left, right, group, x0 in columns:
        draw.text((x0, 140), "TASK ID", font=mono(12, True), fill=FAINT)
        draw.text((x0 + 190, 140), "ARM A (OMP)", font=mono(12, True), fill=ARM_A_COLOR)
        draw.text((x0 + 360, 140), "ARM B (CLI)", font=mono(12, True), fill=ARM_B_COLOR)
        draw.text((x0 + 520, 140), "OUTCOME", font=mono(12, True), fill=FAINT)
        for i, entry in enumerate(group):
            y = 175 + i * 47
            label_a, label_b, outcome = cells(entry)
            draw.rounded_rectangle((left, y - 6, right, y + 36), radius=5, fill=CARD, outline=HAIR, width=1)
            draw.text((x0 + 10, y + 8), entry["task"], font=mono(12, True), fill=INK)
            draw.text(
                (x0 + 190, y + 8),
                label_a,
                font=sans(12, "bold"),
                fill=ARM_A_COLOR if entry["arm_a"]["ratio"] == 1.0 else MUTED,
            )
            draw.text(
                (x0 + 360, y + 8),
                label_b,
                font=sans(12, "bold"),
                fill=ARM_B_COLOR if entry["arm_b"]["ratio"] == 1.0 else FAINT,
            )
            draw.text(
                (x0 + 520, y + 8),
                outcome,
                font=sans(11, "bold"),
                fill=ARM_A_COLOR if "OMP win" in outcome else MUTED,
            )

    draw.line((80, 812, 1520, 812), fill=HAIR, width=1)
    draw.text(
        (80, 826),
        "0% cells are Zero-Drop scores, not failed test runs: Multi-CLI zeros are 300s planner-SLA breaches"
        " (raw oracle still passed 122/138 of those tests), and rest-api scored 0 in both arms on a missing 01_PLAN.md handoff.",
        font=sans(13),
        fill=MUTED,
    )
    draw.text((80, 865), "Primary Confirmatory Matrix recorded under runs/confirmatory-003/, rescored by analysis/score_matrix.py", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "07-full-25-task-ledger.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

def main():
    print("Rendering publication figures...")
    render_cover()
    render_architecture()
    render_primary_results()
    render_stage_parity()
    render_ablation_tasks()
    render_ablation_tax()
    render_full_ledger()
    print("All figures successfully rendered to visuals/out/")

if __name__ == "__main__":
    main()
