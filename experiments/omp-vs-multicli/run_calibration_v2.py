#!/usr/bin/env python3
"""Calibration v2 (Amendment A.1, ADOPTED 2026-09-08): one bounded round.

Re-tests the planner and reviewer effort mappings on tasks disjoint from the
v1 calibration set {affine-cipher, book-store, proverb} and PILOT_TASKS
{grep, list-ops}. Per-task token ratios are reported; per-stage success is a
calibration pooled ratio in [0.80, 1.25]. Winners freeze in EFFORT_MATRIX +
calibration/*.json before confirmatory-011. If either stage cannot enter the
band: stop, no third round, pre-register TOST-only (A.1 stop rule).

DEVIATION (recorded, unavoidable): A.1 also asks for tasks disjoint from the
frozen 25-task matrix set, but the benchmark manifest holds exactly 25 tasks,
so no such task exists. v2 uses 4 fresh matrix tasks (clean both-arms-valid
003 histories, mid-range durations). Gate-sample integrity is preserved: none
is a pilot task, so the 011 TOST gate cannot be tuned on its own sample. v1
itself was tuned on matrix tasks (precedent).

Method per task (single-threaded, same ceilings/prompts/isolation as matrix):
  planner A@high (fresh OMP session) vs planner B grok-medium  -> planner ratio
  worker A@max on plan A (session continue)                     -> fixed reviewer input
  reviewer A@medium (session fork 1, continue) vs
  reviewer A@high   (session fork 2, continue from same state) vs
  reviewer B agy-medium (disk state)                            -> reviewer ratios
Stage 4 (refine) is not run: worker/refine are input-matched, not gated.
Reviewer input (plan A + Arm A worker output) is fixed across reviewer
configs, so the comparison is relative even if planner v2 keeps medium.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import uuid

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "runners"))

from experiment_config import (  # noqa: E402
    AGY_BIN,
    EFFORT_MATRIX,
    GROK_BIN,
    MODEL_PINS,
    PROMPTS,
    TASK_TIMEOUT_SECONDS,
)
from run_task import setup_workspace  # noqa: E402
from runner_common import (  # noqa: E402
    copy_runtime_file,
    prepare_isolated_agy_home,
    prepare_isolated_grok_home,
    prepare_isolated_omp_agent_dir,
    read_guard_events,
)
from runners.arm_a_omp import (  # noqa: E402
    CONFIG_OVERLAY,
    GUARD_EXTENSION,
    run_omp_stage,
)
from runners.arm_b_multicli import run_cli_stage  # noqa: E402

V2_TASKS = ["grade-school", "variable-length-quantity", "pig-latin", "transpose"]
OUT_DIR = os.path.join(BASE_DIR, "runs", "calibration-v2")
BAND = (0.80, 1.25)


def load_meta(task_id):
    with open(os.path.join(BASE_DIR, "../../benchmarks/aider-python/manifest.json")) as handle:
        manifest = json.load(handle)
    return next(item for item in manifest if item["task_id"] == task_id)


def sub(art, tag):
    path = os.path.join(art, tag)
    os.makedirs(path, exist_ok=True)
    return path


def omp_runtime(artifact_dir, tag):
    runtime = tempfile.mkdtemp(prefix=f"calibv2_{tag}_")
    agent_dir = prepare_isolated_omp_agent_dir(runtime)
    config = copy_runtime_file(CONFIG_OVERLAY, runtime)
    guard = copy_runtime_file(GUARD_EXTENSION, runtime)
    os.makedirs(os.path.join(runtime, "sessions"), exist_ok=True)
    log = os.path.join(artifact_dir, f"guard_{tag}.ndjson")
    return runtime, agent_dir, config, guard, log


def fork_runtime(src_runtime, artifact_dir, tag):
    runtime, agent_dir, config, guard, log = omp_runtime(artifact_dir, tag)
    src_sessions = os.path.join(src_runtime, "sessions")
    if os.path.isdir(src_sessions):
        for name in os.listdir(src_sessions):
            src = os.path.join(src_sessions, name)
            dst = os.path.join(runtime, "sessions", name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    return runtime, agent_dir, config, guard, log


def cli_env(home, scratch):
    env = os.environ.copy()
    env["HOME"] = home
    env["BENCHMARK_SCRATCH_DIR"] = os.path.realpath(scratch)
    env["TMPDIR"] = os.path.realpath(scratch)
    return env


def grok_command(meta):
    return [
        GROK_BIN, "-p", PROMPTS["1_PLANNER"].format(impl_file=meta["impl_file"]),
        "--model", MODEL_PINS["planner"]["arm_b"],
        "--effort", EFFORT_MATRIX["planner"]["arm_b"],
        "--always-approve", "--disable-web-search",
        "--session-id", str(uuid.uuid4()), "--output-format", "json",
    ]


def agy_command(meta):
    return [
        AGY_BIN, "-p", PROMPTS["3_REVIEWER"].format(impl_file=meta["impl_file"]),
        "--model", MODEL_PINS["reviewer"]["arm_b"],
        "--effort", EFFORT_MATRIX["reviewer"]["arm_b"],
        "--sandbox", "--new-project", "--dangerously-skip-permissions",
        "--output-format", "json",
    ]


def summarize(stage):
    tel = stage.get("telemetry", {})
    return {
        "success": stage.get("success"),
        "returncode": stage.get("returncode"),
        "duration": stage.get("duration"),
        "reasoning_tokens": tel.get("reasoning_tokens"),
        "effort": stage.get("configured_effort"),
        "violations": [v.get("code") for v in stage.get("protocol_violations", [])],
    }


def copy_if_present(src, dst):
    if os.path.isfile(src):
        shutil.copy2(src, dst)


def calibrate_task(meta):
    task_id = meta["task_id"]
    art = os.path.join(OUT_DIR, task_id)
    os.makedirs(art, exist_ok=True)
    rec = {"task_id": task_id, "configs": {}}
    deadline = time.monotonic() + TASK_TIMEOUT_SECONDS
    workspace = setup_workspace(meta, "calib-v2")
    scratch = tempfile.mkdtemp(prefix=f"calibv2_scratch_{task_id}_")
    runtimes = []
    try:
        # --- planner pair: OMP high (candidate) vs grok medium (fixed) ---
        EFFORT_MATRIX["planner"]["arm_a"] = "high"
        rt, ad, cfg, gd, log = omp_runtime(art, "arm_a")
        runtimes.append(rt)
        plan_a = run_omp_stage(
            "1_PLANNER", "planner",
            PROMPTS["1_PLANNER"].format(impl_file=meta["impl_file"]),
            workspace, sub(art, "planner_omp_high"), rt, ad, cfg, gd, log,
            deadline, continue_session=False, scratch_dir=scratch)
        rec["configs"]["planner_omp_high"] = summarize(plan_a)
        copy_if_present(os.path.join(workspace, "01_PLAN.md"),
                        os.path.join(art, "01_PLAN.arm_a_high.md"))

        grok_rt = tempfile.mkdtemp(prefix=f"calibv2_{task_id}_grok_")
        runtimes.append(grok_rt)
        grok_home = prepare_isolated_grok_home(grok_rt)
        plan_b = run_cli_stage(
            "1_PLANNER", "planner", "grok", grok_command(meta),
            workspace, sub(art, "planner_grok_medium"), deadline,
            cli_env(grok_home, scratch), scratch_dir=scratch)
        rec["configs"]["planner_grok_medium"] = summarize(plan_b)
        # Restore plan A: reviewer input lives in the candidate world.
        shutil.copy2(os.path.join(art, "01_PLAN.arm_a_high.md"),
                     os.path.join(workspace, "01_PLAN.md"))

        # --- worker (Arm A max, session continue): fixed reviewer input ---
        worker = run_omp_stage(
            "2_WORKER_INITIAL", "worker",
            PROMPTS["2_WORKER_INITIAL"].format(impl_file=meta["impl_file"]),
            workspace, sub(art, "worker_omp_max"), rt, ad, cfg, gd, log,
            deadline, continue_session=True, scratch_dir=scratch)
        rec["configs"]["worker_omp_max"] = summarize(worker)

        # --- reviewer triple on identical state (forked sessions) ---
        EFFORT_MATRIX["reviewer"]["arm_a"] = "medium"
        rt_med, ad_med, cfg_med, gd_med, log_med = fork_runtime(rt, art, "rev_med")
        runtimes.append(rt_med)
        rev_med = run_omp_stage(
            "3_REVIEWER", "reviewer",
            PROMPTS["3_REVIEWER"].format(impl_file=meta["impl_file"]),
            workspace, sub(art, "reviewer_omp_medium"),
            rt_med, ad_med, cfg_med, gd_med, log_med,
            deadline, continue_session=True, scratch_dir=scratch)
        rec["configs"]["reviewer_omp_medium"] = summarize(rev_med)
        copy_if_present(os.path.join(workspace, "02_REVIEW.md"),
                        os.path.join(art, "02_REVIEW.omp_medium.md"))

        EFFORT_MATRIX["reviewer"]["arm_a"] = "high"
        rt_high, ad_high, cfg_high, gd_high, log_high = fork_runtime(rt, art, "rev_high")
        runtimes.append(rt_high)
        rev_high = run_omp_stage(
            "3_REVIEWER", "reviewer",
            PROMPTS["3_REVIEWER"].format(impl_file=meta["impl_file"]),
            workspace, sub(art, "reviewer_omp_high"),
            rt_high, ad_high, cfg_high, gd_high, log_high,
            deadline, continue_session=True, scratch_dir=scratch)
        rec["configs"]["reviewer_omp_high"] = summarize(rev_high)
        copy_if_present(os.path.join(workspace, "02_REVIEW.md"),
                        os.path.join(art, "02_REVIEW.omp_high.md"))

        agy_rt = tempfile.mkdtemp(prefix=f"calibv2_{task_id}_agy_")
        runtimes.append(agy_rt)
        agy_home = prepare_isolated_agy_home(agy_rt)
        rev_b = run_cli_stage(
            "3_REVIEWER", "reviewer", "agy", agy_command(meta),
            workspace, sub(art, "reviewer_agy_medium"), deadline,
            cli_env(agy_home, scratch), scratch_dir=scratch)
        rec["configs"]["reviewer_agy_medium"] = summarize(rev_b)
        copy_if_present(os.path.join(workspace, "02_REVIEW.md"),
                        os.path.join(art, "02_REVIEW.agy_medium.md"))

        with open(os.path.join(art, "summary.json"), "w") as handle:
            json.dump(rec, handle, indent=2, sort_keys=True)
        return rec
    finally:
        for path in runtimes:
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    if "--rerun-high" in sys.argv:
        rerun_high_confounded()
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    records = []
    for task_id in V2_TASKS:
        print(f"=== calibration v2: {task_id} ===", flush=True)
        try:
            records.append(calibrate_task(load_meta(task_id)))
        except Exception as error:  # noqa: BLE001 - record and continue
            records.append({"task_id": task_id, "error": str(error)})
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as handle:
        json.dump(records, handle, indent=2, sort_keys=True)
    print(f"wrote {OUT_DIR}/summary.json")




def check_integrity(stage, workspace, required_artifact, guard_log):
    """Arm-level integrity the primitive stage helpers omit (reviewer finding
    2): guard-log aggregation + fresh-handoff validation. Returns a violation
    list; a non-empty list taints the config's measurement."""
    violations = [v.get("code") for v in stage.get("protocol_violations", [])]
    for event in read_guard_events(guard_log):
        violations.append("guard:" + event.get("code", event.get("reason", "?")))
    if required_artifact:
        path = os.path.join(workspace, required_artifact)
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            violations.append("MISSING_HANDOFF:" + required_artifact)
    return violations


def isolated_reviewer_baseline(meta, orig_workspace, tag):
    """Pristine post-worker baseline for one reviewer candidate (reviewer
    finding 1): fresh workspace + plan A + worker outputs, WITHOUT any prior
    candidate's 02_REVIEW.md, plus a private scratch dir."""
    workspace = setup_workspace(meta, tag)
    for name in os.listdir(orig_workspace):
        if name in (".git", "02_REVIEW.md", "__pycache__"):
            continue
        src = os.path.join(orig_workspace, name)
        dst = os.path.join(workspace, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    plan = os.path.join(workspace, "01_PLAN.md")
    if not os.path.isfile(plan) or os.path.getsize(plan) == 0:
        raise RuntimeError(f"baseline missing plan A for {meta['task_id']}")
    scratch = tempfile.mkdtemp(prefix=f"calibv2_{tag}_scratch_")
    return workspace, scratch


def rerun_high_confounded():
    """v2.1 confound repair: OMP-high reviewers read the medium candidate's
    02_REVIEW.md in the shared workspace (all 4 tasks; pig-latin edited it),
    so the v2 high cell supports no claim. Re-measures high on isolated
    baselines with fresh sessions (worker sessions are unrecoverable — the
    session asymmetry vs continued medium is disclosed, not hidden)."""
    import glob as globmod

    for task_id in V2_TASKS:
        print(f"=== calibration v2.1 (high rerun): {task_id} ===", flush=True)
        meta = load_meta(task_id)
        art = os.path.join(OUT_DIR, task_id)
        cands = globmod.glob(os.path.join(
            tempfile.gettempdir(), f"harness_eval_{task_id}_calib-v2_*"))
        saved = open(os.path.join(art, "01_PLAN.arm_a_high.md"), "rb").read()
        # Two workspaces exist per task: the abandoned first planner attempt
        # (empty zero-token turn) and the live one. The live baseline is the
        # workspace whose plan is byte-identical to the saved plan A — the
        # exact state the worker and reviewers saw.
        live = [c for c in cands if os.path.isfile(
            os.path.join(c, "01_PLAN.md")) and open(
            os.path.join(c, "01_PLAN.md"), "rb").read() == saved]
        if len(live) != 1:
            raise RuntimeError(f"expected 1 live workspace for {task_id}: {cands}")
        workspace, scratch = isolated_reviewer_baseline(
            meta, live[0], "calib-v2-high")
        runtimes = []
        try:
            EFFORT_MATRIX["reviewer"]["arm_a"] = "high"
            old = os.path.join(art, "reviewer_omp_high")
            if os.path.isdir(old):
                os.rename(old, os.path.join(art, "reviewer_omp_high_confounded"))
            rt, ad, cfg, gd, log = omp_runtime(art, "rev_high_clean")
            runtimes.append(rt)
            deadline = time.monotonic() + TASK_TIMEOUT_SECONDS
            rev = run_omp_stage(
                "3_REVIEWER", "reviewer",
                PROMPTS["3_REVIEWER"].format(impl_file=meta["impl_file"]),
                workspace, sub(art, "reviewer_omp_high"),
                rt, ad, cfg, gd, log, deadline,
                continue_session=False, scratch_dir=scratch)
            viol = check_integrity(rev, workspace, "02_REVIEW.md", log)
            copy_if_present(os.path.join(workspace, "02_REVIEW.md"),
                            os.path.join(art, "02_REVIEW.omp_high_clean.md"))
            summary_path = os.path.join(art, "summary.json")
            rec = json.load(open(summary_path))
            rec["configs"]["reviewer_omp_high_confounded"] = rec["configs"].pop(
                "reviewer_omp_high")
            clean = summarize(rev)
            clean["fresh_session"] = True
            clean["integrity_violations"] = viol
            rec["configs"]["reviewer_omp_high"] = clean
            json.dump(rec, open(summary_path, "w"), indent=2, sort_keys=True)
        finally:
            for path in runtimes:
                shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(workspace, ignore_errors=True)
            shutil.rmtree(scratch, ignore_errors=True)
    records = [json.load(open(os.path.join(OUT_DIR, t, "summary.json")))
               for t in V2_TASKS]
    json.dump(records, open(os.path.join(OUT_DIR, "summary.json"), "w"),
              indent=2, sort_keys=True)
    print(f"updated {OUT_DIR}/summary.json")
if __name__ == "__main__":
    main()
