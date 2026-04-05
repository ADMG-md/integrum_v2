#!/usr/bin/env python3
"""
Risk Management Sync Checker — verifies every registered motor has a risk entry.
Usage: python .agents/scripts/check_risk_sync.py
"""

import sys
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER = os.path.join(ROOT, "apps/backend/src/engines/specialty_runner.py")
RISK_FILE = os.path.join(ROOT, "docs/qms/risk_management_file.md")


def get_registered_motors():
    with open(RUNNER) as f:
        content = f.read()
    match = re.search(r"PRIMARY_MOTORS\s*=\s*\{([^}]+)\}", content, re.DOTALL)
    if not match:
        print("❌ FAIL: Could not find PRIMARY_MOTORS dict")
        sys.exit(1)
    return re.findall(r'"(\w+Motor|.*Engine)"', match.group(1))


def get_risk_entries():
    if not os.path.exists(RISK_FILE):
        print(f"⚠️  WARNING: Risk file not found at {RISK_FILE}")
        return set()
    with open(RISK_FILE) as f:
        content = f.read()
    # Find motor/engine references in risk file
    return set(re.findall(r"(?:REQUIREMENT_ID|Motor|Engine)[:\s]*(\w+)", content))


def main():
    registered = get_registered_motors()
    risk_entries = get_risk_entries()

    # Check if each motor's REQUIREMENT_ID appears in risk file
    missing = []
    for motor in registered:
        # Extract base name for matching
        base = motor.replace("Motor", "").replace("Engine", "")
        found = any(base.lower() in entry.lower() for entry in risk_entries)
        if not found:
            missing.append(motor)

    if missing:
        print(f"⚠️  WARNING: {len(missing)} motors may not have risk entries:")
        for m in missing:
            print(f"  - {m}")
        print(f"\nRisk file: {RISK_FILE}")
        print("Note: This is a warning, not a block. Ensure risk file is updated.")
        sys.exit(0)  # Warning only, not a hard block
    else:
        print(f"✅ PASS: All {len(registered)} registered motors have risk entries")
        sys.exit(0)


if __name__ == "__main__":
    main()
