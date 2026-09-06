#!/usr/bin/env python3
"""Unit tests for trace violation patterns in runner_common."""

import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from runner_common import trace_violations  # noqa: E402


class TraceViolationTests(unittest.TestCase):
    def test_benign_prose_does_not_trigger_raw_network_code(self):
        benign_samples = [
            "--dangerously-skip-permissions Auto-approve all tool permission requests without prompting",
            "Address all review findings, bug reports, and user requests in wordy.py",
            "The socket is closed by the operating system after timeout",
            "We do not use urllib or requests in this problem",
            "Client requests are validated before processing",
        ]
        for sample in benign_samples:
            violations = trace_violations(sample)
            codes = [v["code"] for v in violations]
            self.assertNotIn("RAW_NETWORK_CODE", codes, f"False positive on: {sample}")

    def test_genuine_network_code_is_caught(self):
        positive_samples = [
            "import requests\nresp = requests.get('http://example.com')",
            "from urllib.request import urlopen",
            "import urllib.request",
            "import httpx",
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)",
            "socket.create_connection(('1.1.1.1', 80))",
            "const https = require('node:https');",
            "const net = require('net');",
            "await fetch('https://api.openai.com')",
        ]
        for sample in positive_samples:
            violations = trace_violations(sample)
            codes = [v["code"] for v in violations]
            self.assertIn("RAW_NETWORK_CODE", codes, f"Missed genuine network code in: {sample}")

    def test_variable_named_nc_is_not_a_network_command(self):
        # `confirmatory-003` scored `connect` as a protocol violation in both arms
        # because a bare `\bnc\b` matched this plan prose. Regression guard.
        benign_samples = [
            "A neighbor `(nr, nc)` is valid iff:\n\n0 <= nr < height and 0 <= nc < len(grid[nr])",
            "for nr, nc in neighbors(row, col):",
            "nc = col + delta",
        ]
        for sample in benign_samples:
            codes = [v["code"] for v in trace_violations(sample)]
            self.assertNotIn("NETWORK_COMMAND", codes, f"False positive on: {sample}")

    def test_genuine_network_commands_are_caught(self):
        positive_samples = [
            "nc -l 4444",
            "cat payload | nc example.com 80",
            "curl https://example.com",
            "wget https://example.com/file",
        ]
        for sample in positive_samples:
            codes = [v["code"] for v in trace_violations(sample)]
            self.assertIn("NETWORK_COMMAND", codes, f"Missed network command in: {sample}")

    def test_oracle_path_is_detected_without_a_leading_prefix(self):
        sample = 'read("/tmp/x/benchmarks/aider-python/oracle/connect/connect_test.py")'
        codes = [v["code"] for v in trace_violations(sample)]
        self.assertIn("ORACLE_PATH", codes)
        self.assertNotIn("ORACLE_PATH", [v["code"] for v in trace_violations("benchmarks/aider-python only")])


if __name__ == "__main__":
    unittest.main()
