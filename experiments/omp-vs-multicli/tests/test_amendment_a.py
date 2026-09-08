#!/usr/bin/env python3
"""Amendment A (post-010) gate tests: C1/C2 containment, C4 retry, C5 split gate, C6/C7 fail-fast."""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "runners"))  # parse_omp_telemetry regression tests

import preflight_parity  # noqa: E402
from experiment_config import PROMPTS, SCRATCH_POLICY_SENTENCE  # noqa: E402
from preflight_parity import (  # noqa: E402
    STAGE_POOLED_REQUIRED,
    STAGE_TOST_REQUIRED,
    _telemetry_only_retryable,
    calculate_stage_tost,
    compute_composite_source_sha256,
    execute_arm_with_retries,
    run_pilot_parity_matrix,
)
from runner_common import seatbelt_profile, temp_root_write_violations  # noqa: E402
from run_matrix import require_parity_preflight  # noqa: E402

STAGES = ("1_PLANNER", "2_WORKER_INITIAL", "3_REVIEWER", "4_WORKER_REFINE")
BLIP = [{"code": "REASONING_TELEMETRY_MISSING"}, {"code": "NO_REASONING_TOKENS"}]
D1_COMMAND = 'echo "hello" > /tmp/test_grep.txt; grep -l "hello" /tmp/test_grep.txt; rm /tmp/test_grep.txt'


def _tokens(**overrides):
    base = {s: 1000 for s in STAGES}
    base.update(overrides)
    return base


def _arm_result(valid, tokens, violations=(), stage_violations=None):
    stages = [
        {
            "stage": s,
            "telemetry": {"reasoning_tokens": tokens[s]},
            "protocol_violations": list((stage_violations or {}).get(s, [])),
        }
        for s in STAGES
    ]
    return {
        "protocol_valid": valid,
        "protocol_violations": list(violations),
        "stages": stages,
    }


class StubRunner:
    """Queued (valid, tokens, violations, stage_violations) tuples, one per arm execution."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
        self.calls.append({"meta": meta, "early_stop": pilot_early_stop})
        item = self.script[min(len(self.calls) - 1, len(self.script) - 1)]
        valid, tokens, violations, stage_violations = item() if callable(item) else item
        return _arm_result(valid, tokens, violations, stage_violations)


class MatrixHarness:
    """Isolated RUNS_DIR + task sources for stub-driven pilot matrix runs."""

    def __init__(self, test, tasks=("grep", "list-ops"), repeats=7):
        self.tmp = tempfile.mkdtemp(prefix="amend_a_")
        self.src = os.path.join(self.tmp, "src")
        os.makedirs(self.src)
        with open(os.path.join(self.src, "x.py"), "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        runs = os.path.join(self.tmp, "runs")
        os.makedirs(runs)
        self.tasks = list(tasks)
        self.patches = [
            mock.patch.object(preflight_parity, "RUNS_DIR", runs),
            mock.patch.object(preflight_parity, "PILOT_TASKS", self.tasks),
            mock.patch.object(preflight_parity, "PILOT_REPEATS", repeats),
        ]
        for patcher in self.patches:
            patcher.start()
        test.addCleanup(self.close)

    def close(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run(self, runners, run_id="trial", **kwargs):
        meta = {t: {"task_id": t, "impl_file": "x.py"} for t in self.tasks}
        return run_pilot_parity_matrix(
            run_id,
            runners=runners,
            task_meta_map=meta,
            task_source={t: self.src for t in self.tasks},
            **kwargs,
        )

    def run_dir(self, run_id="trial"):
        return os.path.join(self.tmp, "runs", run_id)


class TempRootDetectionTests(unittest.TestCase):
    def test_d1_exact_command_is_caught(self):
        hits = temp_root_write_violations(D1_COMMAND, "")
        self.assertTrue(hits, "D1 grep /tmp write must be detected")
        self.assertTrue(all(h["code"] == "TEMP_ROOT_WRITE" for h in hits))

    def test_redirect_and_write_verbs_are_caught(self):
        positives = [
            "echo data > /tmp/x",
            "echo data >>/private/tmp/x",
            "touch /tmp/a",
            "mkdir -p /tmp/b",
            "cp f /tmp/c",
            "cd /tmp",
            "rm /tmp/test_grep.txt",
            'open("/tmp/x", "w")',
            '{"path": "/tmp/x", "content": "1"}',
            "tee /private/tmp/log",
        ]
        for sample in positives:
            hits = temp_root_write_violations(sample, "")
            self.assertTrue(hits, f"Missed temp-root write in: {sample}")

    def test_scratch_workspace_and_bare_prose_are_clean(self):
        benign = [
            "echo 'hello' > $TMPDIR/test1.txt\ngrep 'hello' $TMPDIR/test1.txt",
            "cat $TMPDIR/out.txt",
            "cd /Users/agentlab/work && python3 -m unittest",
            "open('results.json')",
            '{"path": "grep.py"}',
            "save your work and run the tests",
            "I avoided /tmp/x for scratch",
            "/var/folders/zz/workspace/grep.py",
            SCRATCH_POLICY_SENTENCE,
        ]
        for sample in benign:
            hits = temp_root_write_violations(sample, "")
            self.assertFalse(hits, f"False positive on: {sample}")


class RetryTaxonomyTests(unittest.TestCase):
    def test_pure_blip_is_retryable(self):
        self.assertTrue(_telemetry_only_retryable(list(BLIP)))

    def test_blip_with_third_code_is_not_retryable(self):
        self.assertFalse(_telemetry_only_retryable(list(BLIP) + [{"code": "MISSING_HANDOFF"}]))
        self.assertFalse(_telemetry_only_retryable(list(BLIP) + [{"code": "STAGE_TIMEOUT"}]))

    def test_bare_no_reasoning_is_not_retryable(self):
        self.assertFalse(_telemetry_only_retryable([{"code": "NO_REASONING_TOKENS"}]))

    def test_empty_and_unrelated_are_not_retryable(self):
        self.assertFalse(_telemetry_only_retryable([]))
        self.assertFalse(_telemetry_only_retryable([{"code": "MISSING_HANDOFF"}]))


class SplitGateTests(unittest.TestCase):
    def test_worker_divergence_passes_without_pooled_requirement(self):
        res = calculate_stage_tost([2000] * 5, [1000] * 5, pooled_required=False, tost_required=False)
        self.assertFalse(res["pooled_ok"])
        self.assertTrue(res["passed"])

    def test_tost_only_planner_fails_off_band(self):
        # §A.6: pooled_required=False must NOT bypass TOST for the planner.
        res = calculate_stage_tost([470] * 5, [1000] * 5, pooled_required=False, tost_required=True)
        self.assertFalse(res["pooled_ok"])
        self.assertFalse(res["tost_ok"])
        self.assertFalse(res["passed"])

    def test_tost_only_planner_passes_matched(self):
        res = calculate_stage_tost([1000] * 5, [1000] * 5, pooled_required=False, tost_required=True)
        self.assertTrue(res["passed"])

    def test_same_divergence_fails_with_pooled_requirement(self):
        res = calculate_stage_tost([2000] * 5, [1000] * 5, pooled_required=True)
        self.assertFalse(res["passed"])

    def test_matched_stage_passes(self):
        res = calculate_stage_tost([1000] * 5, [1000] * 5, pooled_required=True)
        self.assertTrue(res["passed"])

    def test_insufficient_pairs_cannot_pass(self):
        res = calculate_stage_tost([1000], [1000])
        self.assertFalse(res.get("passed"))
        self.assertIn("error", res)


class ExecuteRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="amend_a_exec_")
        with open(os.path.join(self.tmp, "x.py"), "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_telemetry_blip_retries_then_succeeds(self):
        blip = (False, _tokens(), list(BLIP), {"1_PLANNER": list(BLIP)})
        good = (True, _tokens(), [], None)
        stub = StubRunner([blip, good])
        out = execute_arm_with_retries(stub, {"task_id": "t"}, self.tmp, "arm_a", "t", 1)
        self.assertTrue(out["protocol_valid"])
        self.assertEqual(out["retries"], 1)
        self.assertEqual(len(stub.calls), 2)
        self.assertEqual(out["retry_log"][0]["stages"], ["1_PLANNER"])

    def test_persistent_blip_becomes_infra_after_max_retries(self):
        blip = (False, _tokens(), list(BLIP), {"1_PLANNER": list(BLIP)})
        stub = StubRunner([blip])
        out = execute_arm_with_retries(stub, {"task_id": "t"}, self.tmp, "arm_a", "t", 1)
        self.assertFalse(out["protocol_valid"])
        self.assertIn("unrecovered", out.get("infra_error", ""))
        self.assertEqual(out["retries"], 2)
        self.assertEqual(len(stub.calls), 3)

    def test_handoff_failure_never_retries(self):
        bad = (
            False,
            _tokens(),
            [{"code": "MISSING_HANDOFF", "path": "01_PLAN.md"}],
            {"1_PLANNER": [{"code": "MISSING_HANDOFF"}]},
        )
        stub = StubRunner([bad, (True, _tokens(), [], None)])
        out = execute_arm_with_retries(stub, {"task_id": "t"}, self.tmp, "arm_a", "t", 1)
        self.assertFalse(out["protocol_valid"])
        self.assertNotIn("infra_error", out)
        self.assertEqual(out["retries"], 0)
        self.assertEqual(len(stub.calls), 1)


class FailFastTests(unittest.TestCase):
    def test_first_drop_aborts_and_skips_second_arm(self):
        harness = MatrixHarness(self, tasks=("grep",), repeats=3)
        bad = (False, _tokens(), [{"code": "STAGE_FAILED"}], None)
        good = (True, _tokens(), [], None)
        arm_a = StubRunner([bad, good])
        arm_b = StubRunner([good])
        res = harness.run({"arm_a": arm_a, "arm_b": arm_b})
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(res["dropped_pairs_count"], 1)
        self.assertEqual(res["total_pairs_evaluated"], 1)
        self.assertTrue(res["abort_reason"].startswith("FIRST_DROP:grep:rep1:protocol"))
        self.assertTrue(res["diagnostic_only"])
        self.assertEqual(len(arm_a.calls), 1)
        self.assertEqual(len(arm_b.calls), 0)
        self.assertTrue(all(c["early_stop"] for c in arm_a.calls))
        self.assertTrue(os.path.isfile(os.path.join(harness.run_dir(), "pilot_aborted.json")))
        with self.assertRaises(RuntimeError):
            harness.run({"arm_a": arm_a, "arm_b": arm_b})

    def test_continue_diagnostics_runs_on_but_stays_diagnostic(self):
        harness = MatrixHarness(self, tasks=("grep",), repeats=3)
        bad = (False, _tokens(), [{"code": "STAGE_FAILED"}], None)
        good = (True, _tokens(), [], None)
        arm_a = StubRunner([bad, good])
        arm_b = StubRunner([good])
        harness.run({"arm_a": arm_a, "arm_b": arm_b})
        res = harness.run({"arm_a": arm_a, "arm_b": arm_b}, continue_diagnostics=True)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(res["total_pairs_evaluated"], 3)
        self.assertTrue(res["diagnostic_only"])
        self.assertEqual(len(arm_b.calls), 2)

    def test_ratio_watch_aborts_at_five_valid_pairs(self):
        # v2 outcome (§A.6): planner is TOST-only, so the pooled-ratio watch
        # applies to the reviewer, the remaining pooled-gated stage.
        harness = MatrixHarness(self, tasks=("grep",), repeats=7)
        tok_a = _tokens(**{"3_REVIEWER": 470})
        tok_b = _tokens()
        arm_a = StubRunner([(True, tok_a, [], None)])
        arm_b = StubRunner([(True, tok_b, [], None)])
        res = harness.run({"arm_a": arm_a, "arm_b": arm_b})
        self.assertEqual(res["verdict"], "FAIL")
        self.assertEqual(res["total_pairs_evaluated"], 5)
        self.assertTrue(res["abort_reason"].startswith("UNRECOVERABLE_POOLED_RATIO:3_REVIEWER"))
        self.assertEqual(len(arm_a.calls), 5)

    def test_full_pass_under_split_gate(self):
        harness = MatrixHarness(self)
        tok_a = _tokens(**{"2_WORKER_INITIAL": 2000, "4_WORKER_REFINE": 500})
        tok_b = _tokens()
        arm_a = StubRunner([(True, tok_a, [], None)])
        arm_b = StubRunner([(True, tok_b, [], None)])
        res = harness.run({"arm_a": arm_a, "arm_b": arm_b})
        self.assertEqual(res["verdict"], "PASS")
        self.assertFalse(res["diagnostic_only"])
        self.assertIsNone(res["abort_reason"])
        worker = res["stage_metrics"]["2_WORKER_INITIAL"]
        self.assertFalse(worker["pooled_ok"])
        self.assertTrue(worker["passed"])
        self.assertEqual(
            res["stage_gates"],
            {s: {"pooled_required": STAGE_POOLED_REQUIRED[s], "tost_required": STAGE_TOST_REQUIRED[s]} for s in STAGES},
        )
        self.assertTrue(res["retry_gate"]["ok"])


class SeatbeltPromptTests(unittest.TestCase):
    def test_seatbelt_denies_tmp_but_not_var_folders(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as scratch:
            profile = seatbelt_profile(ws, scratch)
        self.assertIn('(subpath "/tmp")', profile)
        self.assertIn('(subpath "/private/tmp")', profile)
        self.assertNotIn('(subpath "/var/folders")', profile)

    def test_all_prompts_carry_the_shared_sentence(self):
        self.assertEqual(len(PROMPTS), 4)
        for stage, prompt in PROMPTS.items():
            self.assertIn(SCRATCH_POLICY_SENTENCE, prompt, f"Missing policy sentence in {stage}")
            prompt.format(impl_file="grep.py")


class MatrixGateTests(unittest.TestCase):
    def _write_report(self, run_dir, run_id, manifest_hash, composite, **overrides):
        report = {
            "run_id": run_id,
            "verdict": "PASS",
            "run_manifest_sha256": manifest_hash,
            "composite_source_sha256": composite,
            "diagnostic_only": False,
            "abort_reason": None,
            "stage_gates": {s: {"pooled_required": STAGE_POOLED_REQUIRED[s], "tost_required": STAGE_TOST_REQUIRED[s]} for s in STAGES},
        }
        report.update(overrides)
        with open(os.path.join(run_dir, "preflight_parity.json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle)

    def test_diagnostics_and_abort_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "amend-a-gate-check"
            run_dir = os.path.join(tmp, run_id)
            os.makedirs(run_dir)
            manifest_path = os.path.join(run_dir, "run_manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump({"run_id": run_id}, handle)
            with open(manifest_path, "rb") as handle:
                manifest_hash = hashlib.sha256(handle.read()).hexdigest()
            composite, _ = compute_composite_source_sha256()

            self._write_report(run_dir, run_id, manifest_hash, composite)
            accepted = require_parity_preflight(manifest_path)
            self.assertEqual(accepted["verdict"], "PASS")

            self._write_report(run_dir, run_id, manifest_hash, composite, diagnostic_only=True)
            with self.assertRaises(RuntimeError):
                require_parity_preflight(manifest_path)

            self._write_report(
                run_dir, run_id, manifest_hash, composite,
                diagnostic_only=True, abort_reason="FIRST_DROP:grep:rep1:protocol",
            )
            with self.assertRaises(RuntimeError):
                require_parity_preflight(manifest_path)

            self._write_report(run_dir, run_id, manifest_hash, composite, stage_gates={})
            with self.assertRaises(RuntimeError):
                require_parity_preflight(manifest_path)



class ArmBTelemetrySemanticsTests(unittest.TestCase):
    # Sign-off change 2: no Arm B vendor CLI exposes a reasoning-text stream,
    # so zero accounted reasoning tokens with response text present is an arm
    # failure (NO_REASONING_TOKENS), never a retryable telemetry blip.
    def test_grok_zero_reasoning_with_text_is_not_retryable(self):
        from runners.arm_b_multicli import parse_grok_telemetry
        payload = json.dumps({
            "num_turns": 3, "response": "plan text here",
            "text": "plan text here",
            "usage": {"input_tokens": 100, "output_tokens": 50,
                      "reasoning_tokens": 0},
        })
        tel = parse_grok_telemetry(payload, "planner")
        self.assertFalse(tel["telemetry_missing"])
        self.assertNotIn("thinking_chars", tel)
        self.assertGreater(tel["output_text_chars"], 0)

    def test_codex_zero_reasoning_with_text_is_not_retryable(self):
        from runners.arm_b_multicli import parse_codex_telemetry
        stdout = "\n".join([
            json.dumps({"type": "thread.started"}),
            json.dumps({"type": "item.completed",
                        "item": {"type": "agent_message", "text": "did the thing"}}),
            json.dumps({"type": "turn.completed",
                        "usage": {"input_tokens": 200, "output_tokens": 60,
                                  "reasoning_tokens": 0}}),
        ])
        tel = parse_codex_telemetry(stdout, "worker")
        self.assertFalse(tel["telemetry_missing"])
        self.assertNotIn("thinking_chars", tel)
        self.assertGreater(tel["output_text_chars"], 0)

    def test_agy_zero_reasoning_with_text_is_not_retryable(self):
        from runners.arm_b_multicli import parse_agy_telemetry
        payload = json.dumps({
            "num_turns": 2, "response": "review text",
            "usage": {"input_tokens": 300, "output_tokens": 70,
                      "thinking_tokens": 0},
        })
        tel = parse_agy_telemetry(payload, "reviewer")
        self.assertFalse(tel["telemetry_missing"])
        self.assertNotIn("thinking_chars", tel)
        self.assertGreater(tel["output_text_chars"], 0)


class SeatbeltTempRootTests(unittest.TestCase):
    # Sign-off change 4: the profile refuses roots the /tmp denies would revoke.
    def test_tmp_workspace_raises(self):
        with self.assertRaises(RuntimeError):
            seatbelt_profile("/tmp/some_workspace")

    def test_tmp_scratch_raises(self):
        with tempfile.TemporaryDirectory() as ws:
            with self.assertRaises(RuntimeError):
                seatbelt_profile(ws, "/tmp/some_scratch")

    def test_var_folders_roots_ok(self):
        with tempfile.TemporaryDirectory() as ws:
            with tempfile.TemporaryDirectory() as sc:
                profile = seatbelt_profile(ws, sc)
        self.assertIn("(deny file-write* (subpath \"/tmp\"))", profile)


class ThrottleGuardTests(unittest.TestCase):
    # 2026-09-08: ANY vendor throttle signal aborts with NO retry — retrying
    # a 429 converts a brush with quota into a lockout.
    def test_scanner_hits_vendor_signals(self):
        for text in (
            "Error 429: Too Many Requests",
            json.dumps({"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}}),
            "quota exceeded for gemini-3.8-flash, retry in 70s",
            "Rate limit reached for xai-oauth",
            "The server is overloaded, try again shortly",
            "agy request failed with error 429, see docs",
        ):
            self.assertIsNotNone(
                preflight_parity.find_rate_limit({"stderr": text}), text)

    def test_scanner_misses_clean_text(self):
        for text in (
            "OK: 16 tests passed",
            "retry rate 5% over 20 arm executions",
            "model capacity is sufficient for separate stages",
        ):
            self.assertIsNone(
                preflight_parity.find_rate_limit({"stderr": text}), text)

    def test_scanner_ignores_bare_telemetry_numbers(self):
        # Reviewer 2026-09-08: reasoning_tokens=429 / duration=429.12 are
        # legitimate telemetry, not throttles. A bare numeric 429 with zero
        # surrounding error text is telemetry-shaped and correctly ignored —
        # real vendor throttles always wrap the code in error text.
        misses = [
            {"telemetry": {"reasoning_tokens": 429}, "duration": 429.12},
            {"error": {"code": 429}},
            {"stderr_summary": "exit 0 in 429ms", "telemetry": {"reasoning_tokens": 429}},
        ]
        for payload in misses:
            self.assertIsNone(preflight_parity.find_rate_limit(payload), payload)
        hits = [
            {"stderr_summary": "request failed: Error 429", "telemetry": {"reasoning_tokens": 5}},
            {"stdout_summary": "RESOURCE_EXHAUSTED: quota exceeded", "telemetry": {"reasoning_tokens": 5}},
        ]
        for payload in hits:
            self.assertIsNotNone(preflight_parity.find_rate_limit(payload), payload)

    def test_quota_unknown_is_breach(self):
        snap = dict(preflight_parity.parse_usage(_USAGE_SAMPLE))
        snap["google_weekly"] = None  # partial parse: binding quota unverified
        breach = preflight_parity.check_quota(snap)
        self.assertIsNotNone(breach)
        self.assertIn("unknown:google_weekly", breach)

    def test_read_usage_failure_is_all_none(self):
        import subprocess as subprocess_mod
        with mock.patch.object(subprocess_mod, "run", side_effect=subprocess_mod.TimeoutExpired("omp", 120)):
            snap = preflight_parity.read_usage()
        self.assertTrue(all(v is None for v in snap.values()))
        self.assertIn("unknown", preflight_parity.check_quota(snap))

    def _run_with(self, runner):
        with tempfile.TemporaryDirectory() as src:
            open(os.path.join(src, "f.py"), "w").write("x = 1\n")
            return preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_b", "grep", 1)

    def test_throttled_result_returns_without_retry(self):
        calls = []

        def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
            calls.append(1)
            return {
                "protocol_valid": False,
                "protocol_violations": [],
                "stages": [{"stage": "3_REVIEWER",
                            "telemetry": {"reasoning_tokens": 0}}],
                "stderr": "agy: Error 429 RESOURCE_EXHAUSTED quota exceeded",
            }

        res = self._run_with(runner)
        self.assertTrue(res.get("rate_limited"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(res.get("retries"), 0)

    def test_throttled_exception_returns_without_retry(self):
        calls = []

        def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
            calls.append(1)
            raise RuntimeError("grok CLI failed: 429 Too Many Requests")

        res = self._run_with(runner)
        self.assertTrue(res.get("rate_limited"))
        self.assertEqual(len(calls), 1)
        self.assertIn("RATE_LIMITED", res.get("infra_error", ""))

    def test_plain_infra_error_still_retries(self):
        from preflight_parity import MAX_INFRA_RETRIES
        calls = []

        def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
            calls.append(1)
            raise ValueError("boom: subprocess segfault")

        res = self._run_with(runner)
        self.assertNotIn("rate_limited", res)
        self.assertEqual(len(calls), MAX_INFRA_RETRIES + 1)

    def test_attempt_evidence_retained_on_invalid_result(self):
        # Doubt-stop verdict b (2026-09-08): raw attempt evidence must survive
        # temp cleanup under the run dir, keyed by task/rep/arm/attempt.
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as run:
            open(os.path.join(src, "f.py"), "w").write("x = 1\n")

            def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
                os.makedirs(art_dir, exist_ok=True)
                open(os.path.join(art_dir, "guard.ndjson"), "w").write("{}\n")
                open(os.path.join(workdir, "01_PLAN.md"), "w").write("plan\n")
                return {"protocol_valid": False,
                        "protocol_violations": [{"stage": "3_REVIEWER", "code": "NO_REASONING_TOKENS"}],
                        "stages": [{"stage": "3_REVIEWER", "telemetry": {"reasoning_tokens": 0}}]}

            res = preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_a", "grep", 4, retain_root=run)
            dirs = res.get("attempt_dirs", [])
            self.assertEqual(len(dirs), 1)
            attempt = os.path.join(run, dirs[0])
            self.assertTrue(os.path.isfile(os.path.join(attempt, "arm_result.json")))
            self.assertTrue(os.path.isfile(os.path.join(attempt, "attempt_meta.json")))
            self.assertTrue(os.path.isfile(os.path.join(attempt, "artifacts", "guard.ndjson")))
            self.assertTrue(os.path.isfile(os.path.join(attempt, "workspace", "01_PLAN.md")))
            stored = json.load(open(os.path.join(attempt, "arm_result.json")))
            self.assertEqual(stored["protocol_violations"][0]["code"], "NO_REASONING_TOKENS")

    def test_failed_attempts_preserved_across_retry(self):
        # Retried attempts must keep the FAILED attempts too, not just the last.
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as run:
            open(os.path.join(src, "f.py"), "w").write("x = 1\n")
            calls = []

            def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
                calls.append(1)
                raise ValueError("boom: subprocess segfault")

            res = preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_a", "grep", 1, retain_root=run)
            dirs = res.get("attempt_dirs", [])
            self.assertEqual(len(dirs), len(calls))
            self.assertGreater(len(dirs), 1)
            for rel in dirs:
                meta_path = os.path.join(run, rel, "attempt_meta.json")
                self.assertTrue(os.path.isfile(meta_path))
                meta = json.load(open(meta_path))
                self.assertIn("ValueError", meta["error"])
                self.assertFalse(os.path.exists(os.path.join(run, rel, "arm_result.json")))

    def test_repeat_keys_do_not_overwrite_prior_attempts(self):
        # Re-review: --continue-diagnostics re-executes identical keys;
        # each attempt dir carries a unique suffix, nothing overwritten.
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as run:
            open(os.path.join(src, "f.py"), "w").write("x = 1\n")

            def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
                return {"protocol_valid": True, "protocol_violations": [], "stages": []}

            first = preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_a", "grep", 1, retain_root=run)
            second = preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_a", "grep", 1, retain_root=run)
            self.assertEqual(len(first["attempt_dirs"]), 1)
            self.assertEqual(len(second["attempt_dirs"]), 1)
            self.assertNotEqual(first["attempt_dirs"][0], second["attempt_dirs"][0])
            for res in (first, second):
                self.assertTrue(os.path.isfile(
                    os.path.join(run, res["attempt_dirs"][0], "arm_result.json")))

    def test_retention_failure_is_loud_not_silent(self):
        # Re-review: retention OSError must surface as a RETENTION_FAILED
        # sentinel, never a silent pass — and the workspace must SURVIVE in
        # place (cleanup disarmed), since scratch/art never hold the handoffs
        # and any fallback allocation could itself fail under ENOSPC.
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(src, "f.py"), "w").write("x = 1\n")
            blocker = os.path.join(tmp, "blocker")
            open(blocker, "w").write("not a dir\n")
            seen = []

            def runner(meta, workdir, art_dir, scratch_dir=None, pilot_early_stop=False):
                open(os.path.join(workdir, "01_PLAN.md"), "w").write("plan\n")
                seen.append(workdir)
                return {"protocol_valid": True, "protocol_violations": [], "stages": []}

            res = preflight_parity.execute_arm_with_retries(
                runner, {}, src, "arm_a", "grep", 1, retain_root=blocker)
            try:
                self.assertEqual(len(res.get("attempt_dirs", [])), 1)
                self.assertTrue(res["attempt_dirs"][0].startswith("RETENTION_FAILED:"))
                self.assertEqual(len(seen), 1)
                self.assertTrue(os.path.isfile(os.path.join(seen[0], "01_PLAN.md")))
            finally:
                shutil.rmtree(seen[0], ignore_errors=True)
            self.assertTrue(res["protocol_valid"])


class TerminalErrorTests(unittest.TestCase):
    """Verdict (b) offline replay: OMP stream-stall errors must surface from
    retained event traces instead of reading as success with exit 0."""

    STALL_LINE = json.dumps({
        "type": "turn_end",
        "message": {"role": "assistant", "content": [],
                    "model": "grok-4.6", "stopReason": "error",
                    "errorMessage": "Thinking loop detected: stall.",
                    "errorId": 462848},
    })
    OK_LINE = json.dumps({
        "type": "turn_end",
        "message": {"role": "assistant",
                    "content": [{"type": "text", "text": "plan here"}],
                    "model": "grok-4.6", "stopReason": "complete",
                    "usage": {"input": 10, "output": 5, "cacheRead": 0,
                             "cacheWrite": 0, "reasoningTokens": 71}},
    })

    def test_stream_stall_captured_with_cause(self):
        from arm_a_omp import parse_omp_telemetry
        tel = parse_omp_telemetry(self.OK_LINE + "\n" + self.STALL_LINE, "planner")
        err = tel.get("terminal_error")
        self.assertIsNotNone(err)
        self.assertEqual(err["error_id"], 462848)
        self.assertEqual(err["model"], "grok-4.6")
        self.assertIn("Thinking loop", err["error_message"])
        # Earlier completed-turn accounting untouched, not synthesized.
        self.assertEqual(tel["reasoning_tokens"], 71)

    def test_clean_stream_has_no_terminal_error(self):
        from arm_a_omp import parse_omp_telemetry
        tel = parse_omp_telemetry(self.OK_LINE, "planner")
        self.assertIsNone(tel.get("terminal_error"))

    def test_replay_013_listops_planner_stall(self):
        # Offline replay of the exact retained events behind doubt-stop #2.
        from arm_a_omp import parse_omp_telemetry
        trace = os.path.join(
            BASE_DIR, "runs", "confirmatory-013", "attempts",
            "list-ops_rep1_arm_a_att1_f5423605", "artifacts",
            "1_PLANNER.stdout.jsonl")
        if not os.path.isfile(trace):
            self.skipTest("retained 013 evidence not present")
        tel = parse_omp_telemetry(open(trace, encoding="utf-8").read(), "planner")
        err = tel.get("terminal_error")
        self.assertIsNotNone(err)
        self.assertEqual(err["error_id"], 462848)

class PriorQuotaSnapshotTests(unittest.TestCase):
    """Pairs-1-7 audit finding 2: resume invocations must inherit earlier
    pairs' quota snapshots instead of overwriting them with the latest."""

    def test_missing_prior_report_yields_no_seeds(self):
        with tempfile.TemporaryDirectory() as run:
            self.assertEqual(preflight_parity._prior_quota_snapshots(run), [])

    def test_prior_snapshots_survive_resume(self):
        with tempfile.TemporaryDirectory() as run:
            seeds = [{"phase": "pre", "task_id": "grep", "repeat": 1,
                      "quotas": {"ok": True}}]
            with open(os.path.join(run, "preflight_parity.json"), "w") as handle:
                json.dump({"quota_snapshots": seeds}, handle)
            self.assertEqual(preflight_parity._prior_quota_snapshots(run), seeds)

    def test_corrupt_prior_report_never_blocks(self):
        with tempfile.TemporaryDirectory() as run:
            open(os.path.join(run, "preflight_parity.json"), "w").write("{nope")
            self.assertEqual(preflight_parity._prior_quota_snapshots(run), [])



_USAGE_SAMPLE = """Usage · fetched 807ms ago
Google Antigravity — 1 account
  ● bobby.ivanov91@gmail.com
      ● Usage (Google) (Weekly)     ██████████████████████████░░  92.8% used · resets in 2d23h
      ● Usage (Google) (5 Hour)     ██░░░░░░░░░░░░░░░░░░░░░░░░░░  8.5% used · resets in 1h9m
Xai Oauth — 1 account
  ● bozhidar.n.ivanov@gmail.com · fetched 5m1s ago
      ● Grok Build (Weekly)       ███████████░░░░░░░░░░░░░░░░░  40.0% used · resets in 1d11h
Openai Codex — 1 account
  ● bn.ivanov91@outlook.com · plan: plus
      ● 5 hours  ██████████░░░░░░░░░░░░░░░░░░  34.0% used · resets in 4h22m
      ● 7 days   █░░░░░░░░░░░░░░░░░░░░░░░░░░░  5.0% used · resets in 6d23h
"""


class StepperTests(unittest.TestCase):
    # 2026-09-08: sequential pair-by-pair launch with quota gates.
    def test_parse_usage_sample(self):
        snap = preflight_parity.parse_usage(_USAGE_SAMPLE)
        self.assertEqual(snap["google_weekly"], 92.8)
        self.assertEqual(snap["google_5h"], 8.5)
        self.assertEqual(snap["xai_weekly"], 40.0)
        self.assertEqual(snap["codex_5h"], 34.0)
        self.assertEqual(snap["codex_7d"], 5.0)
        self.assertIsNone(preflight_parity.check_quota(snap))

    def test_quota_breach_detected(self):
        snap = dict(preflight_parity.parse_usage(_USAGE_SAMPLE))
        snap["google_weekly"] = 97.1
        breach = preflight_parity.check_quota(snap)
        self.assertIsNotNone(breach)
        self.assertIn("google_weekly", breach)

    def test_max_new_pairs_steps_and_resumes(self):
        harness = MatrixHarness(self, tasks=("grep",), repeats=3)
        good = (True, _tokens(), [], None)
        runners = {"arm_a": StubRunner([good] * 3), "arm_b": StubRunner([good] * 3)}
        first = harness.run(runners, run_id="step", max_new_pairs=1)
        self.assertEqual(first["new_pairs"], 1)
        self.assertEqual(first["total_pairs_evaluated"], 1)
        self.assertTrue(first["diagnostic_only"])  # incomplete, not a verdict
        second = harness.run(runners, run_id="step", max_new_pairs=1)
        self.assertEqual(second["new_pairs"], 1)
        self.assertEqual(second["total_pairs_evaluated"], 2)

    def test_quota_cap_stops_before_spending(self):
        harness = MatrixHarness(self, tasks=("grep",), repeats=3)
        good = (True, _tokens(), [], None)
        runners = {"arm_a": StubRunner([good] * 3), "arm_b": StubRunner([good] * 3)}
        hot = dict(preflight_parity.parse_usage(_USAGE_SAMPLE))
        hot["google_weekly"] = 98.5
        with mock.patch.object(preflight_parity, "read_usage", return_value=hot):
            res = harness.run(runners, run_id="capped", quota_guard=True)
        self.assertEqual(res["new_pairs"], 0)
        self.assertTrue(res["abort_reason"].startswith("QUOTA_CAP:pre"))
        self.assertEqual(len(runners["arm_a"].calls), 0)
        marker = os.path.join(harness.run_dir("capped"), "pilot_aborted.json")
        self.assertTrue(os.path.isfile(marker))


if __name__ == "__main__":
    unittest.main()

