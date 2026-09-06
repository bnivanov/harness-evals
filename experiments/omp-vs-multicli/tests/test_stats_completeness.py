#!/usr/bin/env python3
"""Completeness-gate, token fallback, and analyze() structured-return tests."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ANALYSIS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../analysis"))
MODULE_PATH = os.path.join(ANALYSIS_DIR, "calculate_stats.py")
sys.path.insert(0, ANALYSIS_DIR)

from calculate_stats import CompletenessError, analyze, execution_token_count  # noqa: E402


def _write_json(path, payload):
    with open(path, "w") as fh:
        json.dump(payload, fh)


def _record(task_id, arm, ratio=1.0, passed=True, duration=10.0, tokens=100, cost=0.5, normalized=None):
    execution = {
        "duration": duration,
        "total_tokens": tokens,
        "total_cost_usd": cost,
    }
    if normalized is not None:
        execution["normalized_total_tokens"] = normalized
    return {
        "task_id": task_id,
        "arm": arm,
        "execution": execution,
        "verification": {
            "task_id": task_id,
            "passed": passed,
            "ratio": ratio,
        },
    }


def _write_pair(results_dir, task_id, **kwargs):
    a_kwargs = {k: v[0] if isinstance(v, tuple) else v for k, v in kwargs.items()}
    b_kwargs = {k: v[1] if isinstance(v, tuple) else v for k, v in kwargs.items()}
    _write_json(
        os.path.join(results_dir, f"{task_id}_arm_a.json"),
        _record(task_id, "arm_a", **a_kwargs),
    )
    _write_json(
        os.path.join(results_dir, f"{task_id}_arm_b.json"),
        _record(task_id, "arm_b", **b_kwargs),
    )


def _write_manifest(path, task_ids):
    _write_json(path, [{"task_id": tid} for tid in task_ids])


class TokenFallbackTests(unittest.TestCase):
    def test_prefers_normalized_total_tokens(self):
        self.assertEqual(
            execution_token_count({"normalized_total_tokens": 42, "total_tokens": 99}),
            42,
        )

    def test_falls_back_to_legacy_total_tokens(self):
        self.assertEqual(execution_token_count({"total_tokens": 99}), 99)

    def test_normalized_zero_is_not_legacy_fallback(self):
        self.assertEqual(
            execution_token_count({"normalized_total_tokens": 0, "total_tokens": 99}),
            0,
        )


class CompletenessGateTests(unittest.TestCase):
    def test_strict_mode_passes_when_every_manifest_task_is_paired(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha", "beta"])
            _write_pair(results, "alpha", ratio=(1.0, 0.5), passed=(True, False), duration=(8.0, 12.0))
            _write_pair(results, "beta", ratio=(0.8, 0.8), passed=(False, False), duration=(9.0, 9.0))
            out = analyze(
                results_dir=results,
                manifest_path=manifest,
                require_complete=True,
                report=False,
            )
            self.assertEqual(out["n"], 2)
            self.assertEqual(out["paired_tasks"], ["alpha", "beta"])
            self.assertTrue(out["require_complete"])
            self.assertIn("ratio", out["wilcoxon"])
            self.assertIn("duration", out["wilcoxon"])
            self.assertIn("tokens", out["wilcoxon"])
            self.assertIn("cost", out["wilcoxon"])
            self.assertIn("p_value", out["mcnemar"])
            self.assertEqual(out["wilson"]["arm_a"]["k"], 1)
            self.assertEqual(out["wilson"]["arm_a"]["n"], 2)

    def test_strict_mode_fails_on_missing_task(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha", "beta"])
            _write_pair(results, "alpha")
            with self.assertRaises(CompletenessError) as ctx:
                analyze(
                    results_dir=results,
                    manifest_path=manifest,
                    require_complete=True,
                    report=False,
                )
            self.assertEqual(ctx.exception.missing, ["beta"])
            self.assertEqual(ctx.exception.extra, [])

    def test_strict_mode_fails_on_extra_task(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha"])
            _write_pair(results, "alpha")
            _write_pair(results, "gamma")
            with self.assertRaises(CompletenessError) as ctx:
                analyze(
                    results_dir=results,
                    manifest_path=manifest,
                    require_complete=True,
                    report=False,
                )
            self.assertEqual(ctx.exception.extra, ["gamma"])
            self.assertEqual(ctx.exception.missing, [])

    def test_strict_mode_fails_on_unpaired_task(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha", "beta"])
            _write_pair(results, "alpha")
            _write_json(
                os.path.join(results, "beta_arm_a.json"),
                _record("beta", "arm_a"),
            )
            with self.assertRaises(CompletenessError) as ctx:
                analyze(
                    results_dir=results,
                    manifest_path=manifest,
                    require_complete=True,
                    report=False,
                )
            self.assertIn("beta", ctx.exception.unpaired)
            self.assertIn("beta", ctx.exception.missing)

    def test_cumulative_mode_allows_n_below_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha", "beta", "gamma"])
            _write_pair(results, "alpha", tokens=(10, 20), normalized=(None, None))
            out = analyze(
                results_dir=results,
                manifest_path=manifest,
                require_complete=False,
                report=False,
            )
            self.assertEqual(out["n"], 1)
            self.assertEqual(out["paired_tasks"], ["alpha"])


class AnalyzeStructuredTests(unittest.TestCase):
    def test_prefers_normalized_tokens_in_wilcoxon_and_means(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            _write_pair(
                results,
                "alpha",
                tokens=(999, 999),
                normalized=(10, 40),
                duration=(1.0, 2.0),
                cost=(0.1, 0.2),
                ratio=(1.0, 1.0),
            )
            out = analyze(results_dir=results, require_complete=False, report=False)
            self.assertEqual(out["means"]["tokens_a"], 10)
            self.assertEqual(out["means"]["tokens_b"], 40)
            # A-B = -30, one nonzero pair → W+ = 0, p = 1.0 (only 2 signings, both tails 1)
            self.assertEqual(out["wilcoxon"]["tokens"]["n"], 1)
            self.assertEqual(out["wilcoxon"]["tokens"]["statistic"], 0.0)
            self.assertEqual(out["wilcoxon"]["tokens"]["p_value"], 1.0)

    def test_legacy_total_tokens_used_when_normalized_absent(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            _write_pair(results, "alpha", tokens=(10, 40))
            out = analyze(results_dir=results, require_complete=False, report=False)
            self.assertEqual(out["means"]["tokens_a"], 10)
            self.assertEqual(out["means"]["tokens_b"], 40)

    def test_human_report_still_emitted_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            _write_pair(results, "alpha")
            proc = subprocess.run(
                [sys.executable, MODULE_PATH, "--results-dir", results],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("EXPERIMENT STATISTICAL ANALYSIS REPORT", proc.stdout)
            self.assertIn("Wilcoxon signed-rank (ratio)", proc.stdout)
            self.assertIn("Exact McNemar Test", proc.stdout)

    def test_cli_require_complete_exits_nonzero_when_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha", "beta"])
            _write_pair(results, "alpha")
            proc = subprocess.run(
                [
                    sys.executable,
                    MODULE_PATH,
                    "--results-dir",
                    results,
                    "--manifest-path",
                    manifest,
                    "--require-complete",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("Strict completeness gate failed", proc.stderr)
            self.assertIn("beta", proc.stderr)

    def test_cli_require_complete_passes_when_complete(self):
        with tempfile.TemporaryDirectory() as td:
            results = os.path.join(td, "results")
            os.makedirs(results)
            manifest = os.path.join(td, "manifest.json")
            _write_manifest(manifest, ["alpha"])
            _write_pair(results, "alpha")
            proc = subprocess.run(
                [
                    sys.executable,
                    MODULE_PATH,
                    "--results-dir",
                    results,
                    "--manifest-path",
                    manifest,
                    "--require-complete",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("N = 1 paired tasks", proc.stdout)


if __name__ == "__main__":
    unittest.main()
