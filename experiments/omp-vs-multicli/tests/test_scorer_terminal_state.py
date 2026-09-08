"""Verdict-(b) scorer regression: the terminal-state rule must apply to
retained traces at scoring time, so historical stage-ok counts correct
without rewriting source records."""

import copy
import json
import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "analysis"))

import score_matrix  # noqa: E402


def _load(name):
    with open(os.path.join(BASE_DIR, "runs", "confirmatory-003", "results", name),
              encoding="utf-8") as handle:
        return json.load(handle)


class ScorerTerminalStateTests(unittest.TestCase):
    def test_rest_api_planner_not_ok_but_shadow_preserved(self):
        # Legacy record predates the parser flag: the rule must fire from the
        # retained trace (final turn stopReason=error, no plan written).
        res = _load("rest-api_arm_a.json")
        scored = score_matrix.score_run(res, score_matrix.PRIMARY_RUN)
        self.assertFalse(scored["stages"]["1_PLANNER"]["ok"])
        self.assertFalse(scored["valid"])
        self.assertEqual(scored["shadow_passed"], 9)
        self.assertEqual(scored["total_tests"], 9)

    def test_healthy_planner_untouched(self):
        res = _load("affine-cipher_arm_a.json")
        scored = score_matrix.score_run(res, score_matrix.PRIMARY_RUN)
        self.assertTrue(scored["stages"]["1_PLANNER"]["ok"])

    def test_new_flag_honored_without_trace(self):
        # Records from the fixed runner carry terminal_error directly; a
        # bogus run_dir must not matter.
        res = _load("affine-cipher_arm_a.json")
        res = copy.deepcopy(res)
        res["execution"]["stages"][0]["telemetry"]["terminal_error"] = {
            "stop_reason": "error", "error_message": "stall", "error_id": 1,
            "model": "grok-4.6",
        }
        scored = score_matrix.score_run(res, "/nonexistent-run-dir")
        self.assertFalse(scored["stages"]["1_PLANNER"]["ok"])

    def test_explicit_clean_flag_beats_trace(self):
        # terminal_error: null on a new record means the parser saw the full
        # stream and found no error — no trace re-parse.
        res = _load("rest-api_arm_a.json")
        res = copy.deepcopy(res)
        res["execution"]["stages"][0]["telemetry"]["terminal_error"] = None
        scored = score_matrix.score_run(res, score_matrix.PRIMARY_RUN)
        self.assertTrue(scored["stages"]["1_PLANNER"]["ok"])

    def test_planner_a_count_is_24_of_25(self):
        primary = score_matrix.load_run(score_matrix.PRIMARY_RUN)
        oks = [score_matrix.score_run(res, score_matrix.PRIMARY_RUN)["stages"]["1_PLANNER"]["ok"]
               for name, res in sorted(primary.items()) if name.endswith("_arm_a")]
        self.assertEqual((sum(oks), len(oks)), (24, 25))


if __name__ == "__main__":
    unittest.main()
