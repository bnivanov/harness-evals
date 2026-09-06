#!/usr/bin/env python3
"""Behavior tests for oracle verifier anti-tamper on one-commit workspaces."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

EXPERIMENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERIFIER_DIR = os.path.join(EXPERIMENT_DIR, "verifier")
REPO_ROOT = os.path.abspath(os.path.join(EXPERIMENT_DIR, "../.."))
TASK_ID = "proverb"
IMPL_FILE = "proverb.py"
TASK_SRC = os.path.join(REPO_ROOT, "benchmarks/aider-python/tasks", TASK_ID)
SOLUTION_SRC = os.path.join(REPO_ROOT, "benchmarks/aider-python/oracle/solutions", IMPL_FILE)

sys.path.insert(0, VERIFIER_DIR)
from oracle_verifier import verify_task  # noqa: E402


def _git(cwd, *args):
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_one_commit_workspace(dest):
    for name in os.listdir(TASK_SRC):
        src = os.path.join(TASK_SRC, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest, name))
    _git(dest, "init")
    _git(dest, "config", "user.name", "BenchmarkRunner")
    _git(dest, "config", "user.email", "runner@benchmark.local")
    _git(dest, "config", "commit.gpgsign", "false")
    _git(dest, "add", ".")
    _git(dest, "-c", "commit.gpgsign=false", "commit", "-m", "initial stub")


def _write_solution(dest):
    shutil.copy2(SOLUTION_SRC, os.path.join(dest, IMPL_FILE))


class OracleVerifierAntiTamperTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.ws = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def test_impl_only_passes(self):
        _init_one_commit_workspace(self.ws)
        _write_solution(self.ws)
        result = verify_task(TASK_ID, self.ws)
        self.assertNotEqual(result.get("tampered"), True, result)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["ratio"], 1.0)
        self.assertGreater(result["total_tests"], 0)
        self.assertEqual(result["passed_tests"], result["total_tests"])
        self.assertIn("returncode", result)
        self.assertIn("raw_output", result)
        self.assertFalse(os.path.exists(os.path.join(self.ws, "proverb_test.py")))

    def test_public_test_edit_fails(self):
        _init_one_commit_workspace(self.ws)
        _write_solution(self.ws)
        public_test = os.path.join(self.ws, "public_test.py")
        with open(public_test, "a", encoding="utf-8") as fh:
            fh.write("\n# tamper\n")

        unstaged = verify_task(TASK_ID, self.ws)
        self.assertTrue(unstaged.get("tampered"))
        self.assertFalse(unstaged["passed"])
        self.assertIn("public_test.py", unstaged.get("tamper_reason", ""))
        self.assertEqual(unstaged["ratio"], 0.0)
        self.assertNotIn("returncode", unstaged)

        _git(self.ws, "add", "public_test.py")
        staged = verify_task(TASK_ID, self.ws)
        self.assertTrue(staged.get("tampered"))
        self.assertFalse(staged["passed"])
        self.assertIn("public_test.py", staged.get("tamper_reason", ""))

    def test_config_or_extra_py_fails(self):
        cases = (
            ("helper.py", "print('extra')\n"),
            ("pyproject.toml", "[project]\nname = 'tamper'\n"),
        )
        for name, body in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as ws:
                    _init_one_commit_workspace(ws)
                    _write_solution(ws)
                    with open(os.path.join(ws, name), "w", encoding="utf-8") as fh:
                        fh.write(body)
                    result = verify_task(TASK_ID, ws)
                    self.assertTrue(result.get("tampered"), result)
                    self.assertFalse(result["passed"])
                    self.assertIn(name, result.get("tamper_reason", ""))
                    self.assertIn("extra source/config/test file", result.get("tamper_reason", ""))

                    _git(ws, "add", name)
                    staged = verify_task(TASK_ID, ws)
                    self.assertTrue(staged.get("tampered"), staged)
                    self.assertIn(name, staged.get("tamper_reason", ""))

    def test_expected_handoffs_and_pycache_pass(self):
        _init_one_commit_workspace(self.ws)
        _write_solution(self.ws)
        with open(os.path.join(self.ws, "01_PLAN.md"), "w", encoding="utf-8") as fh:
            fh.write("# plan\n")
        with open(os.path.join(self.ws, "02_REVIEW.md"), "w", encoding="utf-8") as fh:
            fh.write("# review\n")
        cache_dir = os.path.join(self.ws, "__pycache__")
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, "proverb.cpython-311.pyc"), "wb") as fh:
            fh.write(b"\0")

        result = verify_task(TASK_ID, self.ws)
        self.assertNotEqual(result.get("tampered"), True, result)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["ratio"], 1.0)

    def test_no_git_candidate_fails_closed(self):
        for name in os.listdir(TASK_SRC):
            src = os.path.join(TASK_SRC, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(self.ws, name))
        _write_solution(self.ws)
        result = verify_task(TASK_ID, self.ws)
        self.assertTrue(result.get("tampered"), result)
        self.assertFalse(result["passed"])
        self.assertIn("failed closed", result.get("tamper_reason", ""))
        self.assertEqual(result["ratio"], 0.0)
        self.assertEqual(result["passed_tests"], 0)
        self.assertEqual(result["total_tests"], 0)

    def test_malformed_git_candidate_fails_closed(self):
        for name in os.listdir(TASK_SRC):
            src = os.path.join(TASK_SRC, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(self.ws, name))
        _write_solution(self.ws)
        with open(os.path.join(self.ws, ".git"), "w", encoding="utf-8") as fh:
            fh.write("not a git directory\n")
        result = verify_task(TASK_ID, self.ws)
        self.assertTrue(result.get("tampered"), result)
        self.assertFalse(result["passed"])
        self.assertIn("failed closed", result.get("tamper_reason", ""))

    def test_no_git_allowed_with_explicit_testing_option(self):
        for name in os.listdir(TASK_SRC):
            src = os.path.join(TASK_SRC, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(self.ws, name))
        _write_solution(self.ws)
        result = verify_task(TASK_ID, self.ws, testing_allow_missing_git=True)
        self.assertNotEqual(result.get("tampered"), True, result)
        self.assertTrue(result["passed"], result)
        self.assertGreater(result["total_tests"], 0)


if __name__ == "__main__":
    unittest.main()
