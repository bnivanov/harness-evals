#!/usr/bin/env python3
"""
Oracle Verifier for Aider-Python Benchmark Tasks.
Runs in an isolated temporary directory against quarantined oracle tests.
Enforces anti-tamper constraints (no test modifications, no extra files).
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import re

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../benchmarks/aider-python"))

def verify_task(task_id: str, candidate_dir: str) -> dict:
    manifest_path = os.path.join(BENCHMARK_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        return {"error": f"Manifest not found at {manifest_path}", "passed": False}
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    task_meta = next((item for item in manifest if item["task_id"] == task_id), None)
    if not task_meta:
        return {"error": f"Task {task_id} not found in manifest", "passed": False}
        
    impl_file = task_meta["impl_file"]
    test_file = task_meta["test_file"]
    
    candidate_impl = os.path.join(candidate_dir, impl_file)
    if not os.path.exists(candidate_impl):
        return {
            "task_id": task_id,
            "error": f"Candidate implementation file {impl_file} does not exist",
            "passed": False,
            "ratio": 0.0,
            "passed_tests": 0,
            "total_tests": 0
        }
        
    # Anti-tamper check: ensure public_test.py or other files were not modified maliciously
    tampered = False
    tamper_reason = None
    if os.path.exists(os.path.join(candidate_dir, ".git")):
        res = subprocess.run(["git", "diff", "--name-only", "HEAD~1"], cwd=candidate_dir, capture_output=True, text=True)
        changed_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        for cf in changed_files:
            if cf != impl_file and ("test" in cf.lower() or cf.endswith(".toml") or cf.endswith(".json")):
                tampered = True
                tamper_reason = f"Illegal modification of non-implementation file: {cf}"
                break
                
    if tampered:
        return {
            "task_id": task_id,
            "passed": False,
            "tampered": True,
            "tamper_reason": tamper_reason,
            "ratio": 0.0,
            "passed_tests": 0,
            "total_tests": 0
        }
        
    oracle_test = os.path.join(BENCHMARK_DIR, "oracle", "tests", test_file)
    if not os.path.exists(oracle_test):
        return {"error": f"Oracle test file {test_file} not found", "passed": False}
        
    # Run verification in an isolated temporary sandbox
    with tempfile.TemporaryDirectory() as td:
        shutil.copy2(candidate_impl, os.path.join(td, impl_file))
        shutil.copy2(oracle_test, os.path.join(td, test_file))
        
        proc = subprocess.run(
            ["python3", "-m", "unittest", "-v", test_file],
            cwd=td,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = proc.stderr + "\n" + proc.stdout
        
        # Parse test results: "Ran X tests in Ys"
        ran_match = re.search(r"Ran (\d+) tests?", output)
        total_tests = int(ran_match.group(1)) if ran_match else 0
        
        if proc.returncode == 0 and "OK" in output:
            passed_tests = total_tests
            failed_tests = 0
            errors = 0
            ratio = 1.0
            binary_passed = True
        else:
            # Count failures and errors
            fails_match = re.search(r"FAILED \((?:failures=(\d+))?,?\s*(?:errors=(\d+))?\)", output)
            failures = int(fails_match.group(1)) if (fails_match and fails_match.group(1)) else 0
            errors = int(fails_match.group(2)) if (fails_match and fails_match.group(2)) else 0
            
            failed_tests = failures + errors
            passed_tests = max(0, total_tests - failed_tests)
            ratio = round(passed_tests / total_tests, 4) if total_tests > 0 else 0.0
            binary_passed = (ratio == 1.0 and total_tests > 0)
            
        return {
            "task_id": task_id,
            "passed": binary_passed,
            "ratio": ratio,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": total_tests,
            "returncode": proc.returncode,
            "raw_output": output[-500:]  # tail
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: oracle_verifier.py <task_id> <candidate_dir>")
        sys.exit(1)
        
    res = verify_task(sys.argv[1], sys.argv[2])
    print(json.dumps(res, indent=2))
