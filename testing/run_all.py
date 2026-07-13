#!/usr/bin/env python3
"""
Execution Framework — Full Test Suite Runner
Run from the testing/ directory:  python3 run_all.py
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

TESTS = ['test_template_generator', 'test_reporting_engine']

total_failures = 0
for test_module in TESTS:
    print(f"\n{'=' * 60}")
    print(f"  {test_module}")
    print('=' * 60)
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', test_module, '-v'],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    if result.returncode != 0:
        total_failures += 1

print()
if total_failures == 0:
    print("=" * 60)
    print("[+] ALL TESTS PASSED")
    print("=" * 60)
    sys.exit(0)
else:
    print("=" * 60)
    print(f"[-] {total_failures} MODULE(S) HAD FAILURES")
    print("=" * 60)
    sys.exit(1)
