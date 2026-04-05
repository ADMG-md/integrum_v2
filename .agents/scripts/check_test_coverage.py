#!/usr/bin/env python3
"""
Test Coverage Auditor — verifies every registered motor has tests.
Usage: python3 .agents/scripts/check_test_coverage.py
"""

import sys
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER = os.path.join(ROOT, "apps/backend/src/engines/specialty_runner.py")
TESTS_DIR = os.path.join(ROOT, "apps/backend/tests/unit/engines")

FORBIDDEN_IMPORTS = ["fastapi", "sqlalchemy", "requests", "httpx", "aiohttp", "random"]


def get_registered_motors():
    with open(RUNNER) as f:
        content = f.read()
    match = re.search(r"PRIMARY_MOTORS\s*=\s*\{([^}]+)\}", content, re.DOTALL)
    if not match:
        print("❌ FAIL: Could not find PRIMARY_MOTORS dict")
        sys.exit(1)
    motors = re.findall(r'"(\w+Motor|.*Engine)"', match.group(1))
    return motors


def get_tested_motors():
    tested = set()
    for fname in os.listdir(TESTS_DIR):
        if not fname.startswith("test_") or not fname.endswith(".py"):
            continue
        with open(os.path.join(TESTS_DIR, fname)) as f:
            content = f.read()
        # Find motor class references in test files
        for match in re.findall(
            r"(?:from\s+src\.engines\.[^\s]+\s+import\s+|class\s+Test)(\w+)", content
        ):
            tested.add(match)
        # Also check specialty_runner.run_all results
        for match in re.findall(r'results\["(\w+)"\]', content):
            tested.add(match)
    return tested


def main():
    registered = get_registered_motors()
    tested = get_tested_motors()

    # Filter to only motor/engine names
    registered_motors = [m for m in registered if "Motor" in m or "Engine" in m]

    missing = []
    for motor in registered_motors:
        # Check if motor name appears in any test file
        found = False
        for fname in os.listdir(TESTS_DIR):
            if not fname.startswith("test_"):
                continue
            with open(os.path.join(TESTS_DIR, fname)) as f:
                if motor in f.read():
                    found = True
                    break
        if not found:
            missing.append(motor)

    if missing:
        print(f"❌ FAIL: {len(missing)} motors without test coverage:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)
    else:
        print(
            f"✅ PASS: All {len(registered_motors)} registered motors have test coverage"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
