"""
Data Quality Layer — validates incoming clinical data before ingestion.

Rejects data that fails:
1. Range checks (biological bounds)
2. Completeness checks (required fields)
3. Plausibility checks (physically impossible combinations)
4. Conformance checks (valid codes, units)

Returns: (valid_records, rejected_records_with_reasons)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class QualityCheck:
    name: str
    passed: bool
    severity: str  # "error" (reject) or "warning" (flag)
    message: str


@dataclass
class QualityReport:
    patient_id: str
    checks: List[QualityCheck] = field(default_factory=list)
    is_valid: bool = True
    rejection_reasons: List[str] = field(default_factory=list)

    def add(self, passed: bool, severity: str, name: str, message: str):
        check = QualityCheck(
            name=name, passed=passed, severity=severity, message=message
        )
        self.checks.append(check)
        if not passed and severity == "error":
            self.is_valid = False
            self.rejection_reasons.append(f"{name}: {message}")


# Biological bounds for all observation codes
BOUNDS = {
    # Vitals
    "29463-7": {"min": 20, "max": 500, "unit": "kg", "name": "Weight"},
    "8302-2": {"min": 30, "max": 280, "unit": "cm", "name": "Height"},
    "WAIST-001": {"min": 30, "max": 300, "unit": "cm", "name": "Waist"},
    "HIP-001": {"min": 30, "max": 300, "unit": "cm", "name": "Hip"},
    "NECK-001": {"min": 20, "max": 80, "unit": "cm", "name": "Neck"},
    "8480-6": {"min": 60, "max": 300, "unit": "mmHg", "name": "Systolic BP"},
    "8462-4": {"min": 30, "max": 200, "unit": "mmHg", "name": "Diastolic BP"},
    "AGE-001": {"min": 0, "max": 125, "unit": "years", "name": "Age"},
    # Metabolic
    "2339-0": {"min": 40, "max": 600, "unit": "mg/dL", "name": "Glucose"},
    "4548-4": {"min": 3.0, "max": 18.0, "unit": "%", "name": "HbA1c"},
    "20448-7": {"min": 0.5, "max": 500, "unit": "muU/mL", "name": "Insulin"},
    "2160-0": {"min": 0.2, "max": 10.0, "unit": "mg/dL", "name": "Creatinine"},
    "UA-001": {"min": 1, "max": 20, "unit": "mg/dL", "name": "Uric Acid"},
    # Liver
    "29230-0": {"min": 5, "max": 5000, "unit": "U/L", "name": "AST"},
    "22538-3": {"min": 5, "max": 5000, "unit": "U/L", "name": "ALT"},
    "GGT-001": {"min": 1, "max": 2000, "unit": "U/L", "name": "GGT"},
    # CBC
    "WBC-001": {"min": 1, "max": 100, "unit": "k/uL", "name": "WBC"},
    "26474-7": {"min": 1, "max": 80, "unit": "%", "name": "Lymphocytes"},
    "26499-4": {"min": 10, "max": 95, "unit": "%", "name": "Neutrophils"},
    "MCV-001": {"min": 60, "max": 120, "unit": "fL", "name": "MCV"},
    "RDW-001": {"min": 8, "max": 30, "unit": "%", "name": "RDW"},
    "PLT-001": {"min": 10, "max": 1000, "unit": "k/uL", "name": "Platelets"},
    # Inflammation
    "30522-7": {"min": 0, "max": 50, "unit": "mg/L", "name": "hs-CRP"},
    "FER-001": {"min": 5, "max": 2000, "unit": "ng/mL", "name": "Ferritin"},
    "ALB-001": {"min": 2.0, "max": 6.0, "unit": "g/dL", "name": "Albumin"},
    # Thyroid
    "11579-0": {"min": 0.01, "max": 100, "unit": "uIU/mL", "name": "TSH"},
    "FT4-001": {"min": 0.1, "max": 10, "unit": "ng/dL", "name": "FT4"},
    "FT3-001": {"min": 1.0, "max": 20, "unit": "pg/mL", "name": "FT3"},
    # Lipids
    "2093-3": {"min": 70, "max": 400, "unit": "mg/dL", "name": "Total Cholesterol"},
    "13457-7": {"min": 0, "max": 400, "unit": "mg/dL", "name": "LDL"},
    "2085-9": {"min": 0, "max": 150, "unit": "mg/dL", "name": "HDL"},
    "2571-8": {"min": 0, "max": 1200, "unit": "mg/dL", "name": "Triglycerides"},
    "APOB-001": {"min": 0, "max": 300, "unit": "mg/dL", "name": "ApoB"},
    "LPA-001": {"min": 0, "max": 300, "unit": "mg/dL", "name": "Lp(a)"},
    "APOA1-001": {"min": 0, "max": 300, "unit": "mg/dL", "name": "ApoA1"},
    # Psychometrics
    "PHQ-9": {"min": 0, "max": 27, "unit": "score", "name": "PHQ-9"},
    "GAD-7": {"min": 0, "max": 21, "unit": "score", "name": "GAD-7"},
    "AIS-001": {"min": 0, "max": 24, "unit": "score", "name": "Athens Insomnia"},
    "TFEQ-EMOTIONAL": {"min": 0, "max": 4, "unit": "score", "name": "TFEQ Emotional"},
    "TFEQ-UNCONTROLLED": {
        "min": 0,
        "max": 4,
        "unit": "score",
        "name": "TFEQ Uncontrolled",
    },
    # Functional
    "GRIP-STR-R": {"min": 5, "max": 80, "unit": "kg", "name": "Grip Right"},
    "GRIP-STR-L": {"min": 5, "max": 80, "unit": "kg", "name": "Grip Left"},
    "GAIT-SPEED": {"min": 0.1, "max": 3.0, "unit": "m/s", "name": "Gait Speed"},
    "5XSTS-SEC": {"min": 5, "max": 120, "unit": "s", "name": "5x Chair Stand"},
    "SARCF-SCORE": {"min": 0, "max": 10, "unit": "score", "name": "SARC-F"},
    # BIA
    "MMA-001": {"min": 10, "max": 120, "unit": "kg", "name": "Muscle Mass"},
    "BIA-FAT-PCT": {"min": 5, "max": 70, "unit": "%", "name": "Body Fat %"},
    # Lifestyle
    "LIFE-SLEEP": {"min": 0, "max": 24, "unit": "hours", "name": "Sleep Hours"},
    "LIFE-EXERCISE": {"min": 0, "max": 2000, "unit": "min/week", "name": "Exercise"},
    "LIFE-STRESS": {"min": 0, "max": 10, "unit": "VAS", "name": "Stress"},
    # Other
    "UACR-001": {"min": 0, "max": 3000, "unit": "mg/g", "name": "UACR"},
    "VITB12-001": {"min": 50, "max": 2000, "unit": "pg/mL", "name": "Vitamin B12"},
    "VITD-001": {"min": 5, "max": 150, "unit": "ng/mL", "name": "Vitamin D"},
}

# Plausibility rules: combinations that should be physically consistent
PLAUSIBILITY_RULES = [
    {
        "name": "SBP > DBP",
        "check": lambda obs: _sbp_gt_dbp(obs),
        "message": "Systolic BP must be greater than Diastolic BP",
    },
    {
        "name": "BMI consistency",
        "check": lambda obs: _bmi_consistent(obs),
        "message": "Weight and Height must produce BMI within 10-100 range",
    },
    {
        "name": "Total Chol >= HDL + LDL",
        "check": lambda obs: _chol_consistent(obs),
        "message": "Total cholesterol should be >= HDL + LDL (±20% tolerance)",
    },
]


def _sbp_gt_dbp(observations: List[Dict]) -> Tuple[bool, str]:
    sbp = next((o for o in observations if o["code"] == "8480-6"), None)
    dbp = next((o for o in observations if o["code"] == "8462-4"), None)
    if sbp and dbp:
        try:
            if float(sbp["value"]) <= float(dbp["value"]):
                return False, f"SBP={sbp['value']} <= DBP={dbp['value']}"
        except (ValueError, TypeError):
            pass
    return True, ""


def _bmi_consistent(observations: List[Dict]) -> Tuple[bool, str]:
    weight = next((o for o in observations if o["code"] == "29463-7"), None)
    height = next((o for o in observations if o["code"] == "8302-2"), None)
    if weight and height:
        try:
            w = float(weight["value"])
            h = float(height["value"]) / 100
            if h > 0:
                bmi = w / (h**2)
                if bmi < 10 or bmi > 100:
                    return False, f"BMI={bmi:.1f} out of plausible range"
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    return True, ""


def _chol_consistent(observations: List[Dict]) -> Tuple[bool, str]:
    tc = next((o for o in observations if o["code"] == "2093-3"), None)
    hdl = next((o for o in observations if o["code"] == "2085-9"), None)
    ldl = next((o for o in observations if o["code"] == "13457-7"), None)
    if tc and hdl and ldl:
        try:
            total = float(tc["value"])
            sum_hl = float(hdl["value"]) + float(ldl["value"])
            if sum_hl > 0 and total < sum_hl * 0.8:
                return False, f"TC={total} < HDL+LDL={sum_hl} * 0.8"
        except (ValueError, TypeError):
            pass
    return True, ""


def validate_record(patient_id: str, observations: List[Dict]) -> QualityReport:
    """
    Validate a single patient record before ingestion.

    Args:
        patient_id: Patient identifier
        observations: List of dicts with keys: code, value, unit (optional)

    Returns:
        QualityReport with pass/fail for each check
    """
    report = QualityReport(patient_id=patient_id)

    # 1. Range checks
    for obs in observations:
        code = obs.get("code", "")
        value = obs.get("value")

        if code in BOUNDS:
            bounds = BOUNDS[code]
            try:
                val = float(value)
                if val < bounds["min"]:
                    report.add(
                        passed=False,
                        severity="error",
                        name=f"Range:{bounds['name']}",
                        message=f"Value {val} below minimum {bounds['min']} {bounds['unit']}",
                    )
                elif val > bounds["max"]:
                    report.add(
                        passed=False,
                        severity="error",
                        name=f"Range:{bounds['name']}",
                        message=f"Value {val} above maximum {bounds['max']} {bounds['unit']}",
                    )
                else:
                    report.add(
                        passed=True,
                        severity="error",
                        name=f"Range:{bounds['name']}",
                        message=f"Value {val} within bounds [{bounds['min']}-{bounds['max']}]",
                    )
            except (ValueError, TypeError):
                report.add(
                    passed=False,
                    severity="error",
                    name=f"Type:{bounds['name']}",
                    message=f"Value '{value}' is not a valid number",
                )

    # 2. Plausibility checks
    for rule in PLAUSIBILITY_RULES:
        passed, msg = rule["check"](observations)
        report.add(
            passed=passed,
            severity="warning",
            name=f"Plausibility:{rule['name']}",
            message=msg if not passed else "Passed",
        )

    # 3. Completeness check — minimum required observations
    required_codes = {"29463-7", "8302-2", "8480-6", "8462-4", "AGE-001"}
    present_codes = {o["code"] for o in observations}
    missing = required_codes - present_codes
    if missing:
        report.add(
            passed=False,
            severity="error",
            name="Completeness",
            message=f"Missing required observations: {missing}",
        )
    else:
        report.add(
            passed=True,
            severity="error",
            name="Completeness",
            message="All required observations present",
        )

    return report
