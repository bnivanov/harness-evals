#!/usr/bin/env python3
"""Render publication-grade charts and cover visuals for Workflow Bench Experiment 2.

Clean editorial style matching omp-model-bench:
- Paper background (#FAFAF8), hairline borders (#E2DFD8), crisp data-ink ratio.
- High-contrast typography using Apple Avenir Next and Menlo.
- 1600x640 for 5:2 Cover, 1600x900 for 16:9 analytical figures.
"""

import os
import math
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

    # Header Eyebrow
    draw.text((80, 50), "WORKFLOW BENCH · EXPERIMENT 2", font=mono(18, True), fill=ARM_A_COLOR)
    draw.text((1520, 50), "N=25 PAIRED TASKS · 58 RUNS", font=mono(16, True), fill=FAINT, anchor="ra")
    draw.line((80, 80, 1520, 80), fill=HAIR, width=2)

    # Main Title
    draw.text((80, 110), "Why One Harness, Many Models", font=sans(56, "bold"), fill=INK)
    draw.text((80, 180), "Beats Multiple Orchestrated Ones", font=sans(56, "bold"), fill=INK)

    # Subtitle
    draw.text((80, 260), "A Head-to-Head Empirical Benchmark of Unified Session Orchestration (OMP)", font=sans(24, "medium"), fill=MUTED)
    draw.text((80, 295), "vs. a Disaggregated Vendor CLI Swarm Across 25 Software Engineering Tasks", font=sans(24, "regular"), fill=MUTED)

    # Stat Cards on the right / bottom band
    # Card 1: Primary Resolution Advantage
    draw.rounded_rectangle((80, 360, 510, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 385), "PRIMARY MATRIX RESOLUTION", font=mono(14, True), fill=FAINT)
    draw.text((110, 415), "76% vs 52%", font=sans(42, "bold"), fill=ARM_A_COLOR)
    draw.text((110, 480), "OMP wins +24.0% resolution (p = 0.031*)", font=sans(16, "medium"), fill=MUTED)
    draw.text((110, 505), "Exact McNemar test under strict 300s SLA", font=sans(14), fill=FAINT)

    # Card 2: Latency & Speed Advantage
    draw.rounded_rectangle((540, 360, 970, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((570, 385), "MEAN WALL-CLOCK LATENCY", font=mono(14, True), fill=FAINT)
    draw.text((570, 415), "452s vs 610s", font=sans(42, "bold"), fill=ACCENT_BLUE)
    draw.text((570, 480), "OMP is 157.7s faster per task (p < 0.0001*)", font=sans(16, "medium"), fill=MUTED)
    draw.text((570, 505), "Paired Wilcoxon signed-rank significance", font=sans(14), fill=FAINT)

    # Card 3: The Multi-CLI Tax
    draw.rounded_rectangle((1000, 360, 1520, 540), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((1030, 385), "THE MULTI-CLI ABLATION TAX", font=mono(14, True), fill=FAINT)
    draw.text((1030, 415), "+28.9% Time, +22.8% Cost", font=sans(34, "bold"), fill=ARM_B_COLOR)
    draw.text((1030, 480), "Multi-CLI recovers to 99.3% pass when unconstrained,", font=sans(15, "medium"), fill=MUTED)
    draw.text((1030, 505), "but pays an ongoing overhead tax to match OMP", font=sans(14), fill=FAINT)

    # Footer
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

    # Eyebrow and Title
    draw.text((80, 50), "TOPOLOGY ARCHITECTURE · ARMS A & B", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Two Approaches to Multi-Model Software Engineering", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Comparing internal in-process harness handoffs against external shell-piped CLI boundaries", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # Left Column: Arm A (Unified OMP)
    draw.rounded_rectangle((80, 210, 770, 810), radius=14, fill=CARD, outline=ARM_A_COLOR, width=3)
    draw.rectangle((80, 210, 770, 270), fill=ARM_A_COLOR)
    draw.text((110, 230), "ARM A: UNIFIED OMP HARNESS (IN-PROCESS)", font=mono(18, True), fill="#FFFFFF")

    draw.text((110, 290), "Continuous Execution Session Context", font=sans(24, "bold"), fill=INK)
    draw.text((110, 325), "One process wraps all four frontier model stages seamlessly:", font=sans(16), fill=MUTED)

    # Stages in Arm A
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

    # Key Properties Arm A
    draw.line((110, 725, 740, 725), fill=HAIR, width=1)
    draw.text((110, 740), "• In-Process Tooling: Native hashline edit & grep tools (no subshell drag)", font=sans(14), fill=MUTED)
    draw.text((110, 765), "• Persistent Context: KV cache hits across turns (70%+ cache read ratio)", font=sans(14), fill=MUTED)

    # Right Column: Arm B (Multi-CLI Swarm)
    draw.rounded_rectangle((830, 210, 1520, 810), radius=14, fill=CARD, outline=ARM_B_COLOR, width=3)
    draw.rectangle((830, 210, 1520, 270), fill=ARM_B_COLOR)
    draw.text((860, 230), "ARM B: MULTI-CLI SWARM (DISAGGREGATED)", font=mono(18, True), fill="#FFFFFF")

    draw.text((860, 290), "Subprocess Chaining Over Disk Artifacts", font=sans(24, "bold"), fill=INK)
    draw.text((860, 325), "Separate standalone CLI binaries spawned per stage:", font=sans(16), fill=MUTED)

    # Stages in Arm B
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

    # Key Properties Arm B
    draw.line((860, 725, 1490, 725), fill=HAIR, width=1)
    draw.text((860, 740), "• Process Boundary Hops: 4 independent binary boots, node/pty startup tax", font=sans(14), fill=MUTED)
    draw.text((860, 765), "• Context Re-Inflation: Each stage reads full context cold from filesystem", font=sans(14), fill=MUTED)

    # Footer
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

    # Header
    draw.text((80, 50), "PRIMARY STATISTICAL GATE · PRE-REGISTERED N=25 MATRIX", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Head-to-Head Performance Under Production SLAs", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "300s Stage SLA Ceiling, Zero-Drop Pre-Registered Protocol, 50 Total Runs", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # 4 Main Metrics Comparison Cards
    metrics = [
        ("Binary Resolution (R=1.0)", "76.0%", "52.0%", "Exact McNemar: p = 0.03125*", "Arm A resolves 19/25 tasks vs 13/25 in Arm B (+24.0% advantage)"),
        ("Oracle Pass Ratio (R)", "88.5%", "60.6%", "Paired Wilcoxon: p = 0.01560*", "Arm A passes 389/439 unit tests vs 266/439 in Arm B (+27.9% delta)"),
        ("Mean Wall-Clock Latency", "452.0s", "609.7s", "Paired Wilcoxon: p = 0.00008*", "Arm A is 157.7s faster per task (saves 1.1 hours across 25 tasks)"),
        ("Mean Token Consumption", "1.08M", "1.30M", "Paired Wilcoxon: p = 0.00100*", "Arm A saves 217,957 tokens per task due to session KV-caching")
    ]

    for i, (title, val_a, val_b, stat, desc) in enumerate(metrics):
        col = i % 2
        row = i // 2
        x = 80 + col * 730
        y = 210 + row * 300

        draw.rounded_rectangle((x, y, x + 710, y + 270), radius=12, fill=CARD, outline=HAIR, width=2)
        draw.text((x + 30, y + 25), title.upper(), font=mono(15, True), fill=FAINT)

        # Bar chart comparison
        draw.text((x + 30, y + 65), "Arm A (OMP)", font=sans(16, "bold"), fill=ARM_A_COLOR)
        draw.text((x + 220, y + 60), val_a, font=sans(28, "bold"), fill=ARM_A_COLOR)

        draw.text((x + 30, y + 115), "Arm B (Multi-CLI)", font=sans(16, "bold"), fill=ARM_B_COLOR)
        draw.text((x + 220, y + 110), val_b, font=sans(28, "bold"), fill=ARM_B_COLOR)

        draw.line((x + 30, y + 160, x + 680, y + 160), fill=HAIR, width=1)
        draw.text((x + 30, y + 180), stat, font=mono(15, True), fill=SUCCESS_GREEN if "*" in stat else MUTED)
        draw.text((x + 30, y + 215), desc, font=sans(14), fill=MUTED)

    # Footer
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

    # Header
    draw.text((80, 50), "TIER 2 ANALYSIS · MODEL BEHAVIOR & STAGE ISOLATION", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Is Standalone CLI Inferior, or Did Grok Just Timeout?", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Auditing stage-by-stage model resolution and proving exact 89.2% downstream parity", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # Banner: The Conditional Parity Theorem
    draw.rounded_rectangle((80, 210, 1520, 310), radius=10, fill="#F0FDF4", outline="#86EFAC", width=2)
    draw.text((110, 230), "THE CONDITIONAL PARITY THEOREM (17 MATCHED TASKS)", font=mono(16, True), fill=SUCCESS_GREEN)
    draw.text((110, 260), "When Grok Stage 1 delivered a plan, Arm A and Arm B scored EXACT 89.2% PARITY (13/17 full resolutions each).", font=sans(20, "bold"), fill=INK)
    draw.text((110, 285), "Codex Luna (Worker) and Gemini Flash (Reviewer) performed identically across both harness substrates.", font=sans(16), fill=MUTED)

    # Stage Table
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

    # Explanation text below
    draw.text((80, 720), "Why did Grok CLI timeout in Standalone mode?", font=sans(22, "bold"), fill=INK)
    draw.text((80, 755), "In OMP, Grok operated with direct in-process tool bindings, completing plans in 147.5s on average.", font=sans(16), fill=MUTED)
    draw.text((80, 780), "In standalone CLI mode, Grok spawned subshells per tool turn, accumulating latency until it breached the 300s ceiling on 8 tasks.", font=sans(16), fill=MUTED)

    # Footer
    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Stage telemetry verified via native turn.completed and usage payloads", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "04-stage-parity-breakdown.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

# --------------------------------------------------------------------------
# 5. Extended Ablation & The Multi-CLI Tax (1600 x 900, 16:9)
# --------------------------------------------------------------------------
def render_ablation_tax():
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # Header
    draw.text((80, 50), "TIER 3 ABLATION · EXTENDED HORIZON (600s CEILING)", font=mono(16, True), fill=FAINT)
    draw.text((80, 85), "Proving Pipeline Recovery & Quantifying the Multi-CLI Tax", font=sans(40, "bold"), fill=INK)
    draw.text((80, 140), "Re-running the 8 timed-out Arm B tasks with 600s planning runway confirms accuracy at latency/cost cost", font=sans(20), fill=MUTED)
    draw.line((80, 180, 1520, 180), fill=HAIR, width=2)

    # Card 1: Pipeline Recovery Proof
    draw.rounded_rectangle((80, 210, 770, 500), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 235), "1. THE TIMEOUT HYPOTHESIS CONFIRMED", font=mono(16, True), fill=ARM_A_COLOR)
    draw.text((110, 275), "Unit Pass Ratio on the 8 Timed-Out Tasks:", font=sans(18, "bold"), fill=INK)

    # Before / After Stats
    draw.text((110, 315), "Under Strict 300s SLA:", font=sans(16), fill=MUTED)
    draw.text((360, 310), "0 / 138 (0.0%)", font=sans(24, "bold"), fill=ARM_B_COLOR)
    draw.text((110, 360), "Under 600s Ceiling:", font=sans(16), fill=MUTED)
    draw.text((360, 355), "137 / 138 (99.3%)", font=sans(26, "bold"), fill=SUCCESS_GREEN)
    draw.text((110, 405), "Binary Task Resolutions:", font=sans(16), fill=MUTED)
    draw.text((360, 400), "7 / 8 tasks (87.5%) resolved", font=sans(22, "bold"), fill=SUCCESS_GREEN)

    draw.text((110, 450), "Conclusion: Standalone CLI downstream agents are not broken.", font=sans(15, "medium"), fill=INK)
    draw.text((110, 470), "Grok CLI simply needs 328s–454s to finish planning across CLI boundaries.", font=sans(14), fill=MUTED)

    # Card 2: The Multi-CLI Overhead Tax
    draw.rounded_rectangle((830, 210, 1520, 500), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((860, 235), "2. THE MULTI-CLI EFFICIENCY TAX", font=mono(16, True), fill=ARM_B_COLOR)
    draw.text((860, 275), "Cumulative Cost & Latency to Reach Accuracy Parity:", font=sans(18, "bold"), fill=INK)

    draw.text((860, 315), "Cumulative Latency (8 Tasks):", font=sans(16), fill=MUTED)
    draw.text((1180, 310), "4,463s (OMP) vs 5,751s (CLI)", font=sans(20, "bold"), fill=ARM_B_COLOR)
    draw.text((860, 345), "Latency Penalty for Multi-CLI:", font=sans(16), fill=MUTED)
    draw.text((1180, 345), "+28.9% Slower (+21.5 minutes)", font=sans(18, "bold"), fill=ARM_B_COLOR)

    draw.text((860, 390), "Cumulative Spend (8 Tasks):", font=sans(16), fill=MUTED)
    draw.text((1180, 385), "$6.42 (OMP) vs $7.88 (CLI)", font=sans(20, "bold"), fill=ARM_B_COLOR)
    draw.text((860, 420), "Cost Penalty for Multi-CLI:", font=sans(16), fill=MUTED)
    draw.text((1180, 420), "+22.8% More Expensive (+$1.46)", font=sans(18, "bold"), fill=ARM_B_COLOR)

    draw.text((860, 465), "Conclusion: Parity is achievable, but requires paying a permanent tax.", font=sans(15, "medium"), fill=INK)

    # Bottom Synthesis Table: All 25 Tasks Synthetic Comparison
    draw.rounded_rectangle((80, 530, 1520, 800), radius=12, fill=CARD, outline=HAIR, width=2)
    draw.text((110, 555), "SYNTHETIC N=25 MATRIX (OMP vs UNCONSTRAINED MULTI-CLI)", font=mono(16, True), fill=FAINT)

    cols_syn = [
        ("METRIC", 110),
        ("ARM A (UNIFIED OMP)", 480),
        ("ARM B (EXTENDED CLI)", 880),
        ("ARCHITECTURAL DELTA", 1220)
    ]
    for c, x in cols_syn:
        draw.text((x, 590), c, font=mono(14, True), fill=FAINT)
    draw.line((110, 615, 1490, 615), fill=HAIR, width=1)

    syn_rows = [
        ("Binary Task Resolution (R=1.0)", "19 / 25 (76.0%)", "20 / 25 (80.0%)", "Parity (Delta = 1 task)"),
        ("Oracle Test Pass Ratio", "409 / 439 (93.2%)", "418 / 439 (95.2%)", "Parity (Delta = 9 unit tests)"),
        ("Total Benchmark Wall Latency", "11,299.7s (188.3 min)", "14,325.8s (238.8 min)", "OMP is 50.4 min FASTER (-21.1%)"),
        ("Total Standardized Spend", "$16.92", "$20.46", "OMP is $3.54 CHEAPER (-17.3%)")
    ]
    for idx, (m, a, b, d) in enumerate(syn_rows):
        y = 635 + idx * 38
        draw.text((110, y), m, font=sans(16, "bold"), fill=INK)
        draw.text((480, y), a, font=mono(15), fill=ARM_A_COLOR)
        draw.text((880, y), b, font=mono(15), fill=ARM_B_COLOR)
        draw.text((1220, y), d, font=sans(15, "bold"), fill=ARM_A_COLOR if "OMP is" in d else MUTED)

    # Footer
    draw.line((80, 840, 1520, 840), fill=HAIR, width=1)
    draw.text((80, 865), "Workflow Bench · Experiment 2  ·  Ablation Study", font=mono(14), fill=FAINT)
    draw.text((1520, 865), "github.com/bnivanov/harness-evals", font=mono(14), fill=FAINT, anchor="ra")

    out_file = OUT_DIR / "05-ablation-recovery-tax.png"
    img.save(out_file, optimize=True)
    print(f"Saved: {out_file}")

def main():
    print("Rendering 5 publication-grade figures...")
    render_cover()
    render_architecture()
    render_primary_results()
    render_stage_parity()
    render_ablation_tax()
    print("All figures successfully rendered to visuals/out/")

if __name__ == "__main__":
    main()
