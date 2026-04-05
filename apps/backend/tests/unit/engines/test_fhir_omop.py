"""
Tests for FHIR/OMOP interoperability layers.
Tests concept maps, profiles, and cohort SQL — not full Encounter conversion
(which requires a real database).
"""

import pytest


# ============================================================
# FHIR ConceptMap Tests
# ============================================================


class TestFHIRConceptMap:
    def test_observation_to_loinc_weight(self):
        from src.fhir.concept_map import get_loinc_for_code

        result = get_loinc_for_code("29463-7")
        assert result is not None
        assert result[0] == "29463-7"
        assert result[1] == "Body weight"

    def test_observation_to_loinc_waist(self):
        from src.fhir.concept_map import get_loinc_for_code

        result = get_loinc_for_code("WAIST-001")
        assert result is not None
        assert result[0] == "8280-0"
        assert result[1] == "Waist circumference"

    def test_loinc_to_observation_reverse(self):
        from src.fhir.concept_map import get_integrum_code_for_loinc

        result = get_integrum_code_for_loinc("8280-0")
        assert result == "WAIST-001"

    def test_snomed_for_icd10(self):
        from src.fhir.concept_map import get_snomed_for_icd10

        result = get_snomed_for_icd10("E11")
        assert result is not None
        assert result[0] == "44054006"

    def test_snomed_for_icd10_prefix_match(self):
        from src.fhir.concept_map import get_snomed_for_icd10

        result = get_snomed_for_icd10("E11.9")
        assert result is not None
        assert result[0] == "44054006"

    def test_atc_for_medication(self):
        from src.fhir.concept_map import get_atc_for_medication

        result = get_atc_for_medication("semaglutide")
        assert result is not None
        assert result[0] == "A10BJ06"

    def test_atc_for_medication_partial(self):
        from src.fhir.concept_map import get_atc_for_medication

        result = get_atc_for_medication("METFORMIN 1000mg")
        assert result is not None
        assert result[0] == "A10BA02"


# ============================================================
# FHIR Profile Tests
# ============================================================


class TestFHIRProfile:
    def test_required_observations_defined(self):
        from src.fhir.profile import REQUIRED_OBSERVATIONS

        assert "bmi" in REQUIRED_OBSERVATIONS
        assert REQUIRED_OBSERVATIONS["bmi"] == "39156-5"
        assert "waist" in REQUIRED_OBSERVATIONS
        assert REQUIRED_OBSERVATIONS["waist"] == "8280-0"
        assert len(REQUIRED_OBSERVATIONS) == 12

    def test_recommended_observations_defined(self):
        from src.fhir.profile import RECOMMENDED_OBSERVATIONS

        assert "insulin_fasting" in RECOMMENDED_OBSERVATIONS
        assert "vitamin_d" in RECOMMENDED_OBSERVATIONS
        assert len(RECOMMENDED_OBSERVATIONS) == 15

    def test_calculated_indices_defined(self):
        from src.fhir.profile import CALCULATED_INDICES

        assert "homa_ir" in CALCULATED_INDICES
        assert "tyg_index" in CALCULATED_INDICES
        assert len(CALCULATED_INDICES) == 11

    def test_psychometric_questionnaires_defined(self):
        from src.fhir.profile import PSYCHOMETRIC_QUESTIONNAIRES

        assert "phq9" in PSYCHOMETRIC_QUESTIONNAIRES
        assert "gad7" in PSYCHOMETRIC_QUESTIONNAIRES
        assert len(PSYCHOMETRIC_QUESTIONNAIRES) == 5


# ============================================================
# OMOP ConceptMap Tests
# ============================================================


class TestOMOPConceptMap:
    def test_loinc_to_omop_measurement_bmi(self):
        from src.omop.concept_map import get_omop_measurement_concept

        result = get_omop_measurement_concept("39156-5")
        assert result is not None
        assert result[1] == "Body mass index"

    def test_loinc_to_omop_measurement_waist(self):
        from src.omop.concept_map import get_omop_measurement_concept

        result = get_omop_measurement_concept("8280-0")
        assert result is not None

    def test_icd10_to_omop_condition(self):
        from src.omop.concept_map import get_omop_condition_concept

        result = get_omop_condition_concept("E11")
        assert result is not None
        assert result[1] == "Type 2 diabetes mellitus"

    def test_icd10_to_omop_condition_prefix(self):
        from src.omop.concept_map import get_omop_condition_concept

        result = get_omop_condition_concept("E11.9")
        assert result is not None

    def test_atc_to_omop_drug(self):
        from src.omop.concept_map import get_omop_drug_concept

        result = get_omop_drug_concept("A10BJ06")
        assert result is not None
        assert result[1] == "semaglutide"

    def test_mapping_counts(self):
        from src.omop.concept_map import (
            LOINC_TO_OMOP_MEASUREMENT,
            ICD10_TO_OMOP_CONDITION,
            ATC_TO_OMOP_DRUG,
        )

        assert len(LOINC_TO_OMOP_MEASUREMENT) >= 50
        assert len(ICD10_TO_OMOP_CONDITION) >= 30
        assert len(ATC_TO_OMOP_DRUG) >= 50


# ============================================================
# OMOP Cohort Tests
# ============================================================


class TestOMOPCohorts:
    def test_cohort_definitions_available(self):
        from src.omop.cohorts import COHORT_DEFINITIONS

        assert "obesity_bmi" in COHORT_DEFINITIONS
        assert "t2dm" in COHORT_DEFINITIONS
        assert "metabolic_syndrome" in COHORT_DEFINITIONS
        assert "glp1_eligible" in COHORT_DEFINITIONS
        assert len(COHORT_DEFINITIONS) == 6

    def test_cohort_sql_is_valid(self):
        from src.omop.cohorts import COHORT_DEFINITIONS

        for name, sql in COHORT_DEFINITIONS.items():
            assert "SELECT" in sql.upper()
            assert "person_id" in sql.lower()

    def test_outcome_definitions_available(self):
        from src.omop.cohorts import OUTCOME_DEFINITIONS

        assert "mace" in OUTCOME_DEFINITIONS
        for name, sql in OUTCOME_DEFINITIONS.items():
            assert "SELECT" in sql.upper()

    def test_feature_definitions_available(self):
        from src.omop.cohorts import FEATURE_DEFINITIONS

        assert "baseline" in FEATURE_DEFINITIONS
        for name, sql in FEATURE_DEFINITIONS.items():
            assert "SELECT" in sql.upper()


# ============================================================
# OMOP → FHIR Reverse Transformation Tests
# ============================================================


class TestOMOPToFHIR:
    def _make_omop_data(self):
        return {
            "PERSON": [
                {
                    "person_id": 1,
                    "gender_concept_id": 8507,
                    "year_of_birth": 1970,
                    "race_concept_id": 0,
                }
            ],
            "VISIT_OCCURRENCE": [
                {
                    "visit_occurrence_id": 1,
                    "person_id": 1,
                    "visit_concept_id": 9202,
                    "visit_start_date": "2026-04-04",
                    "visit_end_date": "2026-04-04",
                }
            ],
            "MEASUREMENT": [
                {
                    "measurement_id": 1,
                    "person_id": 1,
                    "measurement_concept_id": 3036277,  # BMI
                    "measurement_date": "2026-04-04",
                    "value_as_number": 34.0,
                    "unit_source_value": "kg/m2",
                },
                {
                    "measurement_id": 2,
                    "person_id": 1,
                    "measurement_concept_id": 3004249,  # SBP
                    "measurement_date": "2026-04-04",
                    "value_as_number": 145.0,
                    "unit_source_value": "mmHg",
                },
            ],
            "CONDITION_OCCURRENCE": [
                {
                    "condition_occurrence_id": 1,
                    "person_id": 1,
                    "condition_concept_id": 201820,  # T2DM
                    "condition_start_date": "2026-04-04",
                    "condition_source_value": "E11",
                }
            ],
            "DRUG_EXPOSURE": [
                {
                    "drug_exposure_id": 1,
                    "person_id": 1,
                    "drug_concept_id": 1580747,  # semaglutide
                    "drug_exposure_start_date": "2026-01-01",
                    "drug_exposure_end_date": None,
                    "drug_source_value": "semaglutide",
                }
            ],
            "OBSERVATION": [
                {
                    "observation_id": 1,
                    "person_id": 1,
                    "observation_concept_id": 44249,
                    "observation_date": "2026-04-04",
                    "value_as_number": 12,
                    "observation_source_value": "PHQ-9",
                }
            ],
        }

    def test_omop_to_fhir_bundle(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        assert bundle.resourceType == "Bundle"
        assert bundle.type == "collection"
        assert len(bundle.entry) > 0

    def test_omop_to_fhir_contains_patient(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        resource_types = [e["resource"]["resourceType"] for e in bundle.entry]
        assert "Patient" in resource_types

    def test_omop_to_fhir_patient_gender(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        patient_entry = [
            e for e in bundle.entry if e["resource"]["resourceType"] == "Patient"
        ][0]
        assert patient_entry["resource"]["gender"] == "male"

    def test_omop_to_fhir_contains_encounter(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        resource_types = [e["resource"]["resourceType"] for e in bundle.entry]
        assert "Encounter" in resource_types

    def test_omop_to_fhir_measurements_to_observations(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        obs_entries = [
            e for e in bundle.entry if e["resource"]["resourceType"] == "Observation"
        ]
        assert len(obs_entries) >= 2  # 2 measurements + 1 psychometric

    def test_omop_to_fhir_conditions(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        cond_entries = [
            e for e in bundle.entry if e["resource"]["resourceType"] == "Condition"
        ]
        assert len(cond_entries) >= 1

    def test_omop_to_fhir_medications(self):
        from src.omop.fhir_reverse import omop_to_fhir_bundle

        omop_data = self._make_omop_data()
        bundle = omop_to_fhir_bundle(omop_data, person_id=1)
        med_entries = [
            e
            for e in bundle.entry
            if e["resource"]["resourceType"] == "MedicationStatement"
        ]
        assert len(med_entries) >= 1

    def test_omop_reverse_mapping_coverage(self):
        from src.omop.fhir_reverse import (
            OMOP_MEASUREMENT_TO_LOINC,
            OMOP_CONDITION_TO_ICD10,
            OMOP_DRUG_TO_ATC,
        )

        # Reverse mappings are smaller since many LOINC share OMOP concept_ids
        assert len(OMOP_MEASUREMENT_TO_LOINC) >= 10
        assert len(OMOP_CONDITION_TO_ICD10) >= 10
        assert len(OMOP_DRUG_TO_ATC) >= 10
