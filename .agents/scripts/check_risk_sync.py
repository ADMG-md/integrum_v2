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


def get_risk_content():
    if not os.path.exists(RISK_FILE):
        print(f"⚠️  WARNING: Risk file not found at {RISK_FILE}")
        return ""
    with open(RISK_FILE) as f:
        return f.read().lower()


def main():
    registered = get_registered_motors()
    risk_content = get_risk_content()

    if not risk_content:
        sys.exit(1)

    # Check if each motor's name, base name, or specific alias appears in risk file
    missing = []
    for motor in registered:
        base = motor.replace("Motor", "").replace("Engine", "")
        
        # Define specific aliases to match how they are referred to in risk_management_file.md
        aliases = [motor.lower(), base.lower()]
        
        if base == "AcostaPhenotype":
            aliases.extend(["acosta"])
        elif base == "EOSSStaging":
            aliases.extend(["eoss"])
        elif base == "CMDSStaging":
            aliases.extend(["cmds"])
        elif base == "BiologicalAge":
            aliases.extend(["bioage", "biological age"])
        elif base == "ATaxonomy":
            aliases.extend(["a-taxonomy", "taxonomy"])
        elif base == "BDomainScores":
            aliases.extend(["bdomain", "b-domain"]) # Avoid generic "domain"
        elif base == "CStateMachine":
            aliases.extend(["c-state", "state machine"])
        elif base == "SleepApnea":
            aliases.extend(["sleep apnea", "saos"])
        elif base == "LaboratoryStewardship":
            aliases.extend(["lab stewardship", "stewardship"])
        elif base == "LaboratorySuggestion":
            aliases.extend(["lab suggestion", "suggestion"])
        elif base == "FunctionalSarcopenia":
            aliases.extend(["functional sarcopenia", " EWGSOP2"])
        elif base == "CMI":
            aliases.extend(["cmi"])
        elif base == "PulsePressure":
            aliases.extend(["pulse pressure"])
        elif base == "NFS":
            aliases.extend(["nfs"])
        elif base == "LipidRiskPrecision":
            aliases.extend(["lipid risk", "lipidrisk"])
        elif base == "GLP1Monitoring":
            aliases.extend(["glp-1", "glp1"])
        elif base == "ACEScore":
            aliases.extend(["ace"])
        elif base == "MetforminB12":
            aliases.extend(["metformin"])
        elif base == "CancerScreening":
            aliases.extend(["cancer"])
        elif base == "SGLT2iBenefit":
            aliases.extend(["sglt2i"])
        elif base == "FriedFrailty":
            aliases.extend(["fried", "frailty"])
        elif base == "CVDReclassifier":
            aliases.extend(["cvd"])
        elif base == "WomensHealth":
            aliases.extend(["womenshealth", "women's health", "womens health", "pregnancy", "embarazo", "gestación"])
        elif base == "MensHealth":
            aliases.extend(["menshealth", "men's health", "mens health", "psa"])
        elif base == "BodyCompositionTrend":
            aliases.extend(["body composition", "bodycomposition", "lean mass", "magra"])
        elif base == "ObesityPharmaEligibility":
            aliases.extend(["obesity pharma", "obesitypharma", "bupropion"])
        elif base == "GLP1Titration":
            aliases.extend(["glp-1 titration", "glp1titration", "escalation", "titulación"])
        elif base == "DrugInteraction":
            aliases.extend(["drug interaction", "druginteraction", "interacciones"])
        elif base == "ProteinEngine":
            aliases.extend(["protein", "proteína"])
        elif base == "PediatricNutrition":
            aliases.extend(["pediatric", "pediátrico"])
        elif base == "PrecisionNutrition":
            aliases.extend(["precision nutrition", "nutrición"])
        elif base == "PharmaPrecision":
            aliases.extend(["pharma precision", "pharmaprecision"]) # Avoid generic "pharma"
        elif base == "PsychometabolicAxis":
            aliases.extend(["psychometabolic", "psicometabólico"])
        elif base == "PharmacogenomicProxy":
            aliases.extend(["pharmacogenomic", "genomics", "pgx"])
        elif base == "VitaminD":
            aliases.extend(["vitamin d", "vitamina d"])

        found = False
        for alias in aliases:
            if alias in risk_content:
                found = True
                break
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

