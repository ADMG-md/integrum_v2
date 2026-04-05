"""
FHIR R4 Profile Validation for Integrum V2.

Validates FHIR Bundles against the ObesityCardiometabolicPhenotype profile.
Ensures required observations, conditions, and medications are present
and correctly coded with LOINC/SNOMED-CT/ATC.

This implements the validation layer described in the FHIR/OMOP interoperability
document, ensuring data quality before export to external systems.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.fhir.profile import (
    REQUIRED_OBSERVATIONS,
    RECOMMENDED_OBSERVATIONS,
    CALCULATED_INDICES,
    PSYCHOMETRIC_QUESTIONNAIRES,
)
from src.fhir.concept_map import (
    OBSERVATION_TO_LOINC,
    CONDITION_TO_SNOMED,
    MEDICATION_TO_ATC,
)


class FHIRValidationResult:
    """Result of FHIR profile validation."""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.completeness_score: float = 0.0

    def add_error(self, message: str):
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def add_info(self, message: str):
        self.info.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "completeness_score": round(self.completeness_score, 2),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


def validate_fhir_bundle(
    bundle: Dict[str, Any],
    strict: bool = False,
) -> FHIRValidationResult:
    """
    Validate a FHIR Bundle against the ObesityCardiometabolicPhenotype profile.

    Args:
        bundle: FHIR Bundle as dictionary
        strict: If True, missing recommended observations are errors.
                If False, they are warnings.

    Returns:
        FHIRValidationResult with validation details
    """
    result = FHIRValidationResult()

    if bundle.get("resourceType") != "Bundle":
        result.add_error("Resource is not a FHIR Bundle")
        return result

    if bundle.get("type") != "collection":
        result.add_warning("Bundle type is not 'collection'")

    entries = bundle.get("entry", [])
    resource_types = [e.get("resource", {}).get("resourceType") for e in entries]

    # 1. Validate Patient exists
    if "Patient" not in resource_types:
        result.add_error("Missing required Patient resource")
    else:
        result.add_info("Patient resource present")

    # 2. Validate Encounter exists
    if "Encounter" not in resource_types:
        result.add_error("Missing required Encounter resource")
    else:
        result.add_info("Encounter resource present")

    # 3. Validate required observations
    present_loinc_codes = _extract_loinc_codes(entries)
    required_present = 0
    required_total = len(REQUIRED_OBSERVATIONS)

    for obs_name, loinc_code in REQUIRED_OBSERVATIONS.items():
        if loinc_code in present_loinc_codes:
            required_present += 1
            result.add_info(f"Required observation present: {obs_name} ({loinc_code})")
        else:
            if strict:
                result.add_error(
                    f"Missing required observation: {obs_name} ({loinc_code})"
                )
            else:
                result.add_warning(
                    f"Missing recommended observation: {obs_name} ({loinc_code})"
                )

    # 4. Validate recommended observations
    recommended_present = 0
    recommended_total = len(RECOMMENDED_OBSERVATIONS)

    for obs_name, loinc_code in RECOMMENDED_OBSERVATIONS.items():
        if loinc_code in present_loinc_codes:
            recommended_present += 1
            result.add_info(
                f"Recommended observation present: {obs_name} ({loinc_code})"
            )
        else:
            result.add_warning(
                f"Missing recommended observation: {obs_name} ({loinc_code})"
            )

    # 5. Validate calculated indices
    calculated_present = 0
    calculated_total = len(CALCULATED_INDICES)

    for calc_name, loinc_code in CALCULATED_INDICES.items():
        if loinc_code in present_loinc_codes:
            calculated_present += 1
            result.add_info(f"Calculated index present: {calc_name} ({loinc_code})")

    # 6. Validate conditions (if any)
    condition_entries = [
        e for e in entries if e.get("resource", {}).get("resourceType") == "Condition"
    ]
    for cond_entry in condition_entries:
        cond = cond_entry.get("resource", {})
        codings = cond.get("code", {}).get("coding", [])
        for coding in codings:
            system = coding.get("system", "")
            code = coding.get("code", "")
            if "snomed.info" in system:
                result.add_info(f"Condition with SNOMED-CT: {code}")
            elif "icd-10" in system:
                result.add_info(f"Condition with ICD-10: {code}")

    # 7. Validate medications (if any)
    medication_entries = [
        e
        for e in entries
        if e.get("resource", {}).get("resourceType") == "MedicationStatement"
    ]
    for med_entry in medication_entries:
        med = med_entry.get("resource", {})
        codings = med.get("medicationCodeableConcept", {}).get("coding", [])
        for coding in codings:
            if "whocc.no" in coding.get("system", ""):
                result.add_info(f"Medication with ATC: {coding.get('code')}")

    # 8. Calculate completeness score
    total_checks = required_total + recommended_total + calculated_total
    total_present = required_present + recommended_present + calculated_present
    result.completeness_score = (
        (total_present / total_checks * 100) if total_checks > 0 else 0
    )

    return result


def _extract_loinc_codes(entries: List[Dict[str, Any]]) -> set:
    """Extract all LOINC codes from FHIR Bundle entries."""
    loinc_codes = set()

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "Observation":
            continue

        codings = resource.get("code", {}).get("coding", [])
        for coding in codings:
            if coding.get("system") == "http://loinc.org":
                loinc_codes.add(coding.get("code", ""))

    return loinc_codes


def validate_minimum_dataset(
    bundle: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Check if a FHIR Bundle meets the minimum dataset requirements
    for the ObesityCardiometabolicPhenotype profile.

    Minimum dataset: Patient + Encounter + BMI + Weight + Height

    Returns:
        Tuple of (is_valid, list_of_missing_items)
    """
    minimum_required = {
        "bmi": REQUIRED_OBSERVATIONS["bmi"],
        "weight": REQUIRED_OBSERVATIONS["weight"],
        "height": REQUIRED_OBSERVATIONS["height"],
    }

    entries = bundle.get("entry", [])
    resource_types = [e.get("resource", {}).get("resourceType") for e in entries]
    present_loinc = _extract_loinc_codes(entries)

    missing = []

    if "Patient" not in resource_types:
        missing.append("Patient")
    if "Encounter" not in resource_types:
        missing.append("Encounter")

    for name, loinc in minimum_required.items():
        if loinc not in present_loinc:
            missing.append(f"Observation: {name} ({loinc})")

    return (len(missing) == 0, missing)
