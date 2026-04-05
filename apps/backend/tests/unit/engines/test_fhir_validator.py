"""
Tests for FHIR R4 profile validation.
"""

import pytest

from src.fhir.validator import (
    FHIRValidationResult,
    validate_fhir_bundle,
    validate_minimum_dataset,
    _extract_loinc_codes,
)


def _make_minimal_bundle():
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "p1"}},
            {"resource": {"resourceType": "Encounter", "id": "e1"}},
        ],
    }


def _make_observation_entry(loinc_code, display=""):
    return {
        "resource": {
            "resourceType": "Observation",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc_code,
                        "display": display,
                    }
                ]
            },
        }
    }


def _make_full_bundle():
    bundle = _make_minimal_bundle()
    bundle["entry"].append(_make_observation_entry("39156-5", "BMI"))
    bundle["entry"].append(_make_observation_entry("29463-7", "Body weight"))
    bundle["entry"].append(_make_observation_entry("8302-2", "Height"))
    bundle["entry"].append(_make_observation_entry("8280-0", "Waist"))
    bundle["entry"].append(_make_observation_entry("8480-6", "Systolic BP"))
    bundle["entry"].append(_make_observation_entry("8462-4", "Diastolic BP"))
    bundle["entry"].append(_make_observation_entry("1558-6", "Fasting glucose"))
    bundle["entry"].append(_make_observation_entry("4548-4", "HbA1c"))
    bundle["entry"].append(_make_observation_entry("2093-3", "Total cholesterol"))
    bundle["entry"].append(_make_observation_entry("2085-9", "HDL"))
    bundle["entry"].append(_make_observation_entry("13457-7", "LDL"))
    bundle["entry"].append(_make_observation_entry("2571-8", "Triglycerides"))
    return bundle


class TestFHIRValidationResult:
    def test_default_is_valid(self):
        result = FHIRValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.info == []
        assert result.completeness_score == 0.0

    def test_add_error_marks_invalid(self):
        result = FHIRValidationResult()
        result.add_error("test error")
        assert result.is_valid is False
        assert "test error" in result.errors

    def test_add_warning_does_not_invalidate(self):
        result = FHIRValidationResult()
        result.add_warning("test warning")
        assert result.is_valid is True
        assert "test warning" in result.warnings

    def test_add_info_does_not_invalidate(self):
        result = FHIRValidationResult()
        result.add_info("test info")
        assert result.is_valid is True
        assert "test info" in result.info

    def test_to_dict(self):
        result = FHIRValidationResult()
        result.add_error("err")
        result.add_warning("warn")
        result.add_info("info")
        result.completeness_score = 75.5
        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["completeness_score"] == 75.5
        assert d["errors"] == ["err"]
        assert d["warnings"] == ["warn"]
        assert d["info"] == ["info"]

    def test_multiple_errors(self):
        result = FHIRValidationResult()
        result.add_error("err1")
        result.add_error("err2")
        assert len(result.errors) == 2
        assert result.is_valid is False


class TestExtractLoincCodes:
    def test_empty_entries(self):
        assert _extract_loinc_codes([]) == set()

    def test_single_observation(self):
        entries = [_make_observation_entry("39156-5")]
        codes = _extract_loinc_codes(entries)
        assert codes == {"39156-5"}

    def test_multiple_observations(self):
        entries = [
            _make_observation_entry("39156-5"),
            _make_observation_entry("29463-7"),
            _make_observation_entry("8280-0"),
        ]
        codes = _extract_loinc_codes(entries)
        assert codes == {"39156-5", "29463-7", "8280-0"}

    def test_ignores_non_observations(self):
        entries = [
            {"resource": {"resourceType": "Patient"}},
            _make_observation_entry("39156-5"),
        ]
        codes = _extract_loinc_codes(entries)
        assert codes == {"39156-5"}

    def test_ignores_non_loinc_systems(self):
        entries = [
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "12345"}
                        ]
                    },
                }
            }
        ]
        codes = _extract_loinc_codes(entries)
        assert codes == set()

    def test_ignores_missing_code(self):
        entries = [
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org"}]},
                }
            }
        ]
        codes = _extract_loinc_codes(entries)
        assert codes == {""}


class TestValidateFHIRBundle:
    def test_non_bundle_resource(self):
        result = validate_fhir_bundle({"resourceType": "Patient"})
        assert result.is_valid is False
        assert any("not a FHIR Bundle" in e for e in result.errors)

    def test_non_collection_bundle(self):
        bundle = {"resourceType": "Bundle", "type": "searchset", "entry": []}
        result = validate_fhir_bundle(bundle)
        assert any("collection" in w for w in result.warnings)

    def test_missing_patient(self):
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": {"resourceType": "Encounter"}}],
        }
        result = validate_fhir_bundle(bundle)
        assert result.is_valid is False
        assert any("Patient" in e for e in result.errors)

    def test_missing_encounter(self):
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": {"resourceType": "Patient"}}],
        }
        result = validate_fhir_bundle(bundle)
        assert result.is_valid is False
        assert any("Encounter" in e for e in result.errors)

    def test_patient_and_encounter_present(self):
        bundle = _make_minimal_bundle()
        result = validate_fhir_bundle(bundle)
        assert any("Patient" in i for i in result.info)
        assert any("Encounter" in i for i in result.info)

    def test_all_required_observations_present(self):
        bundle = _make_full_bundle()
        result = validate_fhir_bundle(bundle)
        assert result.completeness_score > 0

    def test_missing_required_observation_non_strict(self):
        bundle = _make_minimal_bundle()
        result = validate_fhir_bundle(bundle, strict=False)
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_missing_required_observation_strict(self):
        bundle = _make_minimal_bundle()
        result = validate_fhir_bundle(bundle, strict=True)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_recommended_observation_present(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("20448-7", "Fasting insulin"))
        result = validate_fhir_bundle(bundle)
        assert any("Recommended observation present" in i for i in result.info)

    def test_recommended_observation_missing(self):
        bundle = _make_minimal_bundle()
        result = validate_fhir_bundle(bundle)
        assert any("Missing recommended" in w for w in result.warnings)

    def test_calculated_index_present(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("89242-2", "HOMA-IR"))
        result = validate_fhir_bundle(bundle)
        assert any("Calculated index present" in i for i in result.info)

    def test_condition_with_snomed(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "44054006"}
                        ]
                    },
                }
            }
        )
        result = validate_fhir_bundle(bundle)
        assert any("SNOMED-CT" in i for i in result.info)

    def test_condition_with_icd10(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"coding": [{"system": "http://icd-10", "code": "E11"}]},
                }
            }
        )
        result = validate_fhir_bundle(bundle)
        assert any("ICD-10" in i for i in result.info)

    def test_medication_with_atc(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {
                        "coding": [
                            {"system": "https://whocc.no/atc", "code": "A10BJ06"}
                        ]
                    },
                }
            }
        )
        result = validate_fhir_bundle(bundle)
        assert any("ATC" in i for i in result.info)

    def test_completeness_score_full_bundle(self):
        bundle = _make_full_bundle()
        result = validate_fhir_bundle(bundle)
        assert result.completeness_score > 0
        assert result.completeness_score <= 100

    def test_completeness_score_empty_bundle(self):
        bundle = _make_minimal_bundle()
        result = validate_fhir_bundle(bundle)
        assert result.completeness_score < 50

    def test_empty_bundle_dict(self):
        result = validate_fhir_bundle({})
        assert result.is_valid is False

    def test_bundle_without_entries(self):
        bundle = {"resourceType": "Bundle", "type": "collection", "entry": []}
        result = validate_fhir_bundle(bundle)
        assert result.is_valid is False


class TestValidateMinimumDataset:
    def test_minimum_met(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("39156-5", "BMI"))
        bundle["entry"].append(_make_observation_entry("29463-7", "Weight"))
        bundle["entry"].append(_make_observation_entry("8302-2", "Height"))
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is True
        assert missing == []

    def test_missing_patient(self):
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": {"resourceType": "Encounter"}},
                _make_observation_entry("39156-5"),
                _make_observation_entry("29463-7"),
                _make_observation_entry("8302-2"),
            ],
        }
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert "Patient" in missing

    def test_missing_encounter(self):
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": {"resourceType": "Patient"}},
                _make_observation_entry("39156-5"),
                _make_observation_entry("29463-7"),
                _make_observation_entry("8302-2"),
            ],
        }
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert "Encounter" in missing

    def test_missing_bmi(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("29463-7"))
        bundle["entry"].append(_make_observation_entry("8302-2"))
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert any("bmi" in m for m in missing)

    def test_missing_weight(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("39156-5"))
        bundle["entry"].append(_make_observation_entry("8302-2"))
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert any("weight" in m for m in missing)

    def test_missing_height(self):
        bundle = _make_minimal_bundle()
        bundle["entry"].append(_make_observation_entry("39156-5"))
        bundle["entry"].append(_make_observation_entry("29463-7"))
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert any("height" in m for m in missing)

    def test_missing_all_minimum_observations(self):
        bundle = _make_minimal_bundle()
        is_valid, missing = validate_minimum_dataset(bundle)
        assert is_valid is False
        assert len(missing) == 3
        assert all("Observation:" in m for m in missing)
