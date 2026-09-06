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
    draw.text((1520, 50), "N=25 PAIRED TASKS · 58 RUNS", font=mono(16, True), fill=FAINT, anchor="ra")
    draw.line((80, 80, 1520, 80), fill=HAIR, width=2)

    draw.text((80, 110), "Why One Harness, Many Models", font=sans(56, "bold"), fill=INK)
    draw.text((80, 180), "Beats Multiple Orchestrated Ones", font=sans(56, "bold"), fill=INK)

    draw.text((80, 260), "A Head-to-Head Empirical Benchmark of Unified Session Orchestration (OMP)", font=sans(24, "medium"), fill=MUTED)
    draw.text((80, 295), "vs. a Disaggregated Vendor CLI Swarm Across 25 Software Engineering Tasks", font=sans(24, "regular"), fill=MUTED)

    # Stat Card 1
    draw.rounded_rectangle((80, 360, 510, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 385), "PRIMARY MATRIX RESOLUTION", font=mono(14, True), fill=FAINT)
    draw.text((110, 415), "76% vs 52%", font=sans(42, "bold"), fill=ARM_A_COLOR)
    draw.text((110, 480), "OMP wins +24.0% resolution (p = 0.031*)", font=sans(16, "medium"), fill=MUTED)
    draw.text((110, 505), "Exact McNemar test under strict 300s SLA", font=sans(14), fill=FAINT)

    # Stat Card 2
    draw.rounded_rectangle((540, 360, 970, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((570, 385), "MEAN WALL-CLOCK LATENCY", font=mono(14, True), fill=FAINT)
    draw.text((570, 415), "452s vs 610s", font=sans(42, "bold"), fill=ACCENT_BLUE)
    draw.text((570, 480), "OMP is 157.7s faster per task (p < 0.0001*)", font=sans(16, "medium"), fill=MUTED)
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
        ("Stage 1: Planner", "xai-oauth/grok-4.6 @ max", "Direct AST inspection & internal thinking"),
        ("Stage 2: Worker Initial", "openai-codex/gpt-5.6-luna @ max", "Hashline edits; inherited project memory"),
        ("Stage 3: Reviewer", "google-antigravity/gemini-3.8-flash @ max", "In-memory test audit & fix identification"),
        ("Stage 4: Worker Refine", "openai-codex/gpt-5.6-luna @ max", "Targeted delta patch without context re-read")
    ]
    for i, (st, mod, desc) in enumerate(stages_a):
        y = 370 + i * 85
        draw.rounded_rectangle((110, y, 740, y + 70), radius=8, fill="#F0FDF4", outline="#BBF7D0", width=1)
        draw.text((130, y + 12), st, font=sans(17, "bold"), fill=ARM_A_COLOR)
        draw.text((330, y + 12), mod, font=mono(13), fill=MUTED)
        draw.text((130, y + 40), desc, font=sans(14), fill=INK)

    draw.line((110, 725, 740, 725), fill=HAIR, width=1)
    draw.text((110, 740), "• In-Process Tooling: Native hashline edit & grep tools (no subshell drag)", font=sans(14), fill=MUTED)
    draw.text((110, 765), "• Persistent Context: KV cache hits across turns (70%+ cache read ratio)", font=sans(14), fill=MUTED)

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
        draw.text((1080, y + 12), mod, font=mono(13), fill=MUTED)
        draw.text((880, y + 40), desc, font=sans(14), fill=INK)

    draw.line((860, 725, 1490, 725), fill=HAIR, width=1)
    draw.text((860, 740), "• Process Boundary Hops: 4 independent binary boots, node/pty startup tax", font=sans(14), fill=MUTED)
    draw.text((860, 765), "• Context Re-Inflation: Each stage reads full context cold from filesystem", font=sans(14), fill=MUTED)

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

    metrics = [
        ("Binary Resolution (R=1.0)", "76.0%", "52.0%", "Exact McNemar: p = 0.03125*", "Arm A resolves 19/25 tasks vs 13/25 in Arm B (+24.0% advantage)"),
        ("Oracle Pass Ratio (R)", "88.5%", "60.6%", "Paired Wilcoxon: p = 0.01560*", "Arm A passes 389/439 unit tests vs 266/439 in Arm B (+27.9% delta)"),
        ("Mean Wall-Clock Latency", "452.0s", "609.7s", "Paired Wilcoxon: p = 0.00008*", "Arm A is 157.7s faster per task (saves 1.1 hours across 25 tasks)"),
        ("Mean Token Consumption", "1.08M", "1.30M", "Paired Wilcoxon: p = 0.00100*", "Arm A saves 217,957 tokens per task due to session prompt caching")
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
    draw.text((80, 865), "Statistical Battery: McNemar exact test + Paired Wilcoxon signed-rank test (alpha = 0.05)", font=mono(14), fill=FAINT)
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
    draw.text((80, 140), "Auditing stage-by-stage model resolution and proving exact 89.2% downstream parity", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    draw.rounded_rectangle((80, 210, 1520, 310), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((110, 230), "THE CONDITIONAL PARITY THEOREM (17 MATCHED TASKS)", font=mono(16, True), fill=SUCCESS_GREEN)
    draw.text((110, 260), "When Grok Stage 1 delivered a plan, Arm A and Arm B scored EXACT 89.2% PARITY (13/17 full resolutions each).", font=sans(20, "bold"), fill=INK)
    draw.text((110, 285), "Codex Luna (Worker) and Gemini Flash (Reviewer) performed identically across both harness substrates.", font=sans(16), fill=MUTED)

    y_table = 340
    headers = [("STAGE", 80), ("MODEL ROLE", 320), ("ARM A (OMP)", 680), ("ARM B (MULTI-CLI)", 980), ("VERDICT", 1300)]
    for h, x in headers:
        draw.text((x, y_table), h, font=mono(15, True), fill=FAINT)
    draw.line((80, y_table + 25, 1520, y_table + 25), fill=HAIR, width=2)

    rows = [
        ("Stage 1: Planner", "Grok 4.6 @ xhigh", "25/25 (100%) · 147.5s", "17/25 (68%) · 239.8s", "Grok CLI 8 timeouts"),
        ("Stage 2: Worker Initial", "GPT-5.6 Luna @ max", "25/25 (100%) · 110.2s", "25/25 (100%) · 99.7s", "100% Code Parity"),
        ("Stage 3: Reviewer", "Gemini 3.8 Flash @ high", "25/25 (100%) · 100.1s", "25/25 (100%) · 151.6s", "100% Audit Parity (OMP +51s fast)"),
        ("Stage 4: Worker Refine", "GPT-5.6 Luna @ max", "25/25 (100%) · 66.6s", "21/25 (84%) · 108.1s", "Parity on planned tasks")
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
    draw.text((80, 755), "In OMP, Grok operated with direct in-process tool bindings, completing plans in 147.5s on average.", font=sans(16), fill=MUTED)
    draw.text((80, 780), "In standalone CLI mode, Grok spawned subshells per tool turn, accumulating latency until it breached the 300s ceiling on 8 tasks.", font=sans(16), fill=MUTED)

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
    draw.text((80, 85), "Recovery of the 8 Timed-Out Tasks Under Extended Runway", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Proving that granting Grok CLI sufficient planning time restores downstream accuracy to 99.3%", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    y_table = 210
    headers = [("TASK ID", 100), ("300s SLA (PRIMARY)", 380), ("600s CEILING (ABLATION)", 680), ("GROK PLAN DUR", 1020), ("TOTAL DUR", 1220), ("TOTAL COST", 1380)]
    for h, x in headers:
        draw.text((x, y_table), h, font=mono(14, True), fill=FAINT)
    draw.line((80, y_table + 25, 1520, y_table + 25), fill=HAIR, width=2)

    ablation_rows = [
        ("scale-generator", "0 / 17 (0.0%)", "17 / 17 (100.0%) PERFECT", "454.0s", "679.8s", "$1.0251"),
        ("sgf-parsing", "0 / 23 (0.0%)", "23 / 23 (100.0%) PERFECT", "328.9s", "678.5s", "$0.9937"),
        ("react", "0 / 14 (0.0%)", "14 / 14 (100.0%) PERFECT", "342.2s", "1015.0s", "$1.2210"),
        ("rest-api", "0 / 9 (0.0%)", "9 / 9 (100.0%) PERFECT", "215.3s", "795.8s", "$1.0112"),
        ("pov", "0 / 15 (0.0%)", "14 / 15 (93.3%)", "408.4s", "796.2s", "$1.0929"),
        ("list-ops", "0 / 24 (0.0%)", "24 / 24 (100.0%) PERFECT", "205.7s", "531.7s", "$0.7336"),
        ("grep", "0 / 25 (0.0%)", "25 / 25 (100.0%) PERFECT", "155.9s", "484.3s", "$0.7034"),
        ("go-counting", "0 / 11 (0.0%)", "11 / 11 (100.0%) PERFECT", "420.0s", "769.8s", "$1.1016")
    ]

    for idx, (tid, pri, abl, gd, td, tc) in enumerate(ablation_rows):
        y = y_table + 45 + idx * 58
        draw.rounded_rectangle((80, y - 8, 1520, y + 42), radius=6, fill=CARD, outline=HAIR, width=1)
        draw.text((100, y + 8), tid, font=mono(15, True), fill=INK)
        draw.text((380, y + 8), pri, font=sans(16, "bold"), fill=ARM_B_COLOR)
        draw.text((680, y + 8), abl, font=sans(16, "bold"), fill=SUCCESS_GREEN)
        draw.text((1020, y + 8), gd, font=mono(15), fill=MUTED)
        draw.text((1220, y + 8), td, font=mono(15), fill=MUTED)
        draw.text((1380, y + 8), tc, font=mono(15), fill=MUTED)

    # Summary bar at bottom
    y_sum = y_table + 45 + 8 * 58 + 15
    draw.rounded_rectangle((80, y_sum, 1520, y_sum + 70), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((100, y_sum + 22), "TOTALS / PASS RATIO:", font=mono(16, True), fill=INK)
    draw.text((380, y_sum + 20), "0 / 138 (0.0%)", font=sans(20, "bold"), fill=ARM_B_COLOR)
    draw.text((680, y_sum + 18), "137 / 138 (99.3%)", font=sans(22, "bold"), fill=SUCCESS_GREEN)
    draw.text((1020, y_sum + 22), "Mean: 316.3s", font=mono(15), fill=MUTED)
    draw.text((1220, y_sum + 22), "Total: 5751.1s", font=mono(15), fill=MUTED)
    draw.text((1380, y_sum + 22), "Total: $7.8826", font=mono(15), fill=MUTED)

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
    draw.rounded_rectangle((80, 210, 770, 480), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 235), "1. 8-TASK HEAD-TO-HEAD (ABLATION SUBSET)", font=mono(15, True), fill=ARM_A_COLOR)

    h2h = [
        ("Oracle Test Pass Ratio", "128 / 138 (92.8%)", "137 / 138 (99.3%)", "Multi-CLI +6.5%"),
        ("Binary Task Resolution", "6 / 8 (75.0%)", "7 / 8 (87.5%)", "Multi-CLI +1 task"),
        ("Cumulative Wall Latency", "4,462.7s (~74.4m)", "5,751.1s (~95.9m)", "Multi-CLI takes +21.5m (+28.9%)"),
        ("Cumulative Dollar Spend", "$6.42", "$7.88", "Multi-CLI costs +$1.46 (+22.8%)")
    ]
    for i, (m, a, b, pen) in enumerate(h2h):
        y = 275 + i * 48
        draw.text((110, y), m, font=sans(15, "bold"), fill=INK)
        draw.text((360, y), a, font=mono(13), fill=ARM_A_COLOR)
        draw.text((500, y), b, font=mono(13), fill=ARM_B_COLOR)
        draw.text((640, y), pen, font=sans(12, "bold"), fill=ARM_B_COLOR if "+" in pen and "task" not in pen else MUTED)

    # Card 2: Key Finding
    draw.rounded_rectangle((830, 210, 1520, 480), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((860, 235), "2. THE ARCHITECTURAL TAX DEFINED", font=mono(15, True), fill=ARM_B_COLOR)
    draw.text((860, 275), "Why does Multi-CLI pay 28.9% more latency and 22.8% more cost?", font=sans(16, "bold"), fill=INK)
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

    syn_rows = [
        ("Binary Task Resolution (R=1.0)", "19 / 25 (76.0%)", "20 / 25 (80.0%)", "Parity (Delta = 1 task)"),
        ("Oracle Test Pass Ratio", "409 / 439 (93.2%)", "418 / 439 (95.2%)", "Parity (Delta = 9 unit tests)"),
        ("Total Benchmark Wall Latency", "11,299.7s (188.3 min)", "14,325.8s (238.8 min)", "OMP is 50.4 min FASTER (-21.1%)"),
        ("Total Standardized Spend", "$16.92", "$20.46", "OMP is $3.54 CHEAPER (-17.3%)")
    ]
    for idx, (m, a, b, d) in enumerate(syn_rows):
        y = 615 + idx * 42
        draw.text((110, y), m, font=sans(16, "bold"), fill=INK)
        draw.text((480, y), a, font=mono(15), fill=ARM_A_COLOR)
        draw.text((880, y), b, font=mono(15), fill=ARM_B_COLOR)
        draw.text((1220, y), d, font=sans(15, "bold"), fill=ARM_A_COLOR if "OMP is" in d else MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
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

    # 2-column layout for the 25 tasks
    # Left column: tasks 1-13; Right column: tasks 14-25
    tasks_left = [
        ("affine-cipher", "100%", "319.8s", "100%", "508.9s", "Parity"),
        ("book-store", "100%", "385.4s", "100%", "605.4s", "Parity"),
        ("bowling", "100%", "571.9s", "100%", "709.6s", "Parity"),
        ("connect", "0%", "305.2s", "0%", "568.2s", "Both failed"),
        ("go-counting", "100%", "416.2s", "0%", "731.9s", "OMP win (Grok timeout)"),
        ("grade-school", "100%", "235.6s", "100%", "351.9s", "Parity"),
        ("grep", "100%", "520.7s", "0%", "828.9s", "OMP win (Grok timeout)"),
        ("hangman", "71%", "440.0s", "71%", "557.0s", "Parity"),
        ("list-ops", "100%", "471.9s", "0%", "799.0s", "OMP win (Grok timeout)"),
        ("phone-number", "90%", "411.3s", "90%", "431.4s", "Parity"),
        ("pig-latin", "100%", "323.0s", "100%", "503.1s", "Parity"),
        ("poker", "100%", "475.0s", "100%", "597.2s", "Parity"),
        ("pov", "100%", "606.4s", "0%", "900.2s", "OMP win (Grok timeout)")
    ]

    tasks_right = [
        ("proverb", "100%", "161.4s", "100%", "260.4s", "Parity"),
        ("react", "100%", "625.3s", "0%", "900.0s", "OMP win (Grok timeout)"),
        ("rest-api", "0%", "569.5s", "0%", "900.1s", "Both failed"),
        ("robot-name", "100%", "599.5s", "100%", "657.1s", "Parity"),
        ("scale-generator", "100%", "563.2s", "0%", "726.9s", "OMP win (Grok timeout)"),
        ("sgf-parsing", "96%", "689.4s", "0%", "900.1s", "OMP win (Grok timeout)"),
        ("simple-linked-list", "100%", "421.1s", "100%", "456.6s", "Parity"),
        ("transpose", "100%", "467.4s", "100%", "442.7s", "Parity"),
        ("tree-building", "54%", "419.2s", "54%", "436.6s", "Parity"),
        ("two-bucket", "100%", "489.2s", "100%", "489.0s", "Parity"),
        ("variable-length-qty", "100%", "243.9s", "100%", "389.1s", "Parity"),
        ("wordy", "100%", "567.7s", "100%", "610.4s", "Parity")
    ]

    # Header for left
    draw.text((90, 140), "TASK ID", font=mono(12, True), fill=FAINT)
    draw.text((250, 140), "ARM A (OMP)", font=mono(12, True), fill=ARM_A_COLOR)
    draw.text((430, 140), "ARM B (CLI)", font=mono(12, True), fill=ARM_B_COLOR)
    draw.text((610, 140), "OUTCOME", font=mono(12, True), fill=FAINT)

    # Header for right
    draw.text((810, 140), "TASK ID", font=mono(12, True), fill=FAINT)
    draw.text((970, 140), "ARM A (OMP)", font=mono(12, True), fill=ARM_A_COLOR)
    draw.text((1150, 140), "ARM B (CLI)", font=mono(12, True), fill=ARM_B_COLOR)
    draw.text((1330, 140), "OUTCOME", font=mono(12, True), fill=FAINT)

    draw.line((80, 160, 1520, 160), fill=HAIR, width=1)

    for i, (tid, pa, da, pb, db, outc) in enumerate(tasks_left):
        y = 175 + i * 47
        draw.rounded_rectangle((80, y - 6, 760, y + 36), radius=5, fill=CARD, outline=HAIR, width=1)
        draw.text((90, y + 8), tid[:18], font=mono(12, True), fill=INK)
        draw.text((250, y + 8), f"{pa} ({da})", font=sans(12, "bold"), fill=ARM_A_COLOR if pa == "100%" else MUTED)
        draw.text((430, y + 8), f"{pb} ({db})", font=sans(12, "bold"), fill=ARM_B_COLOR if pb == "100%" else FAINT)
        draw.text((610, y + 8), outc[:18], font=sans(11, "bold"), fill=ARM_A_COLOR if "OMP win" in outc else MUTED)

    for i, (tid, pa, da, pb, db, outc) in enumerate(tasks_right):
        y = 175 + i * 47
        draw.rounded_rectangle((800, y - 6, 1520, y + 36), radius=5, fill=CARD, outline=HAIR, width=1)
        draw.text((810, y + 8), tid[:18], font=mono(12, True), fill=INK)
        draw.text((970, y + 8), f"{pa} ({da})", font=sans(12, "bold"), fill=ARM_A_COLOR if pa == "100%" else MUTED)
        draw.text((1150, y + 8), f"{pb} ({db})", font=sans(12, "bold"), fill=ARM_B_COLOR if pb == "100%" else FAINT)
        draw.text((1330, y + 8), outc[:18], font=sans(11, "bold"), fill=ARM_A_COLOR if "OMP win" in outc else MUTED)

    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Primary Confirmatory Matrix recorded under runs/confirmatory-003/", font=mono(14), fill=FAINT)
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
