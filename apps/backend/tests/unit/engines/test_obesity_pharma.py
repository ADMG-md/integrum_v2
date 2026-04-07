"""
Golden Motor Tests: ObesityPharmaEligibilityMotor (IEC 62304 V&V)
===================================================================
Tests for Anti-Obesity Medication (AOM) Eligibility Engine.
Test IDs: T-AOM-01 through T-AOM-08.
Evidence: FDA Guidance 2024, SELECT trial, SURMOUNT trials.
"""

import pytest
from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor
from src.engines.domain import Encounter, ClinicalHistory, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return ObesityPharmaEligibilityMotor()


def _make_encounter(id="aom-test", bmi=None, history=None, observations=None):
    """Helper: creates a valid Encounter for AOM eligibility testing."""
    obs = observations or []
    if bmi is not None and bmi > 0:
        weight = bmi * 1.7 * 1.7
        obs.extend(
            [
                Observation(code="29463-7", value=weight),
                Observation(code="8302-2", value=170),
            ]
        )
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=obs,
        metadata={},
        history=history,
    )


def test_aom_validate_missing_bmi(motor):
    """T-AOM-01: No BMI = validation failure."""
    enc = _make_encounter(id="1")
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "BMI" in msg


def test_aom_validate_with_bmi(motor):
    """T-AOM-01: With BMI = validation passes."""
    enc = _make_encounter(id="2", bmi=35.0)
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_aom_not_eligible_low_bmi(motor):
    """T-AOM-02: BMI < 27 = not eligible."""
    history = ClinicalHistory()
    enc = _make_encounter(id="3", bmi=24.0, history=history)
    result = motor.compute(enc)
    assert result.metadata["eligible"] is False
    assert "No elegible" in result.calculated_value


def test_aom_eligible_bmi_30(motor):
    """T-AOM-03: BMI >= 30 = eligible for any AOM."""
    history = ClinicalHistory()
    enc = _make_encounter(id="4", bmi=32.0, history=history)
    result = motor.compute(enc)
    assert result.metadata["eligible"] is True
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "Elegible" in result.calculated_value


def test_aom_eligible_bmi_27_with_comorbidity(motor):
    """T-AOM-03: BMI >= 27 + comorbidity = eligible."""
    history = ClinicalHistory(has_hypertension=True)
    enc = _make_encounter(id="5", bmi=28.0, history=history)
    result = motor.compute(enc)
    assert result.metadata["eligible"] is True
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_aom_glp1_contraindicated_tcm(motor):
    """T-AOM-04: TCM (medullary thyroid carcinoma) = GLP-1 contraindicated."""
    history = ClinicalHistory(
        has_history_medullary_thyroid_carcinoma=True, has_type2_diabetes=True
    )
    enc = _make_encounter(id="6", bmi=35.0, history=history)
    result = motor.compute(enc)
    assert "CONTRAINDICADO" in result.explanation
    assert "TCM" in result.explanation


def test_aom_glp1_contraindicated_men2(motor):
    """T-AOM-04: MEN2 = GLP-1 contraindicated."""
    history = ClinicalHistory(has_history_men2=True, has_type2_diabetes=True)
    enc = _make_encounter(id="7", bmi=35.0, history=history)
    result = motor.compute(enc)
    assert "CONTRAINDICADO" in result.explanation
    assert "MEN2" in result.explanation


def test_aom_bupropion_suicide_risk(motor):
    """T-AOM-05: PHQ-9 Item 9 > 0 = bupropion contraindicated (FDA Black Box)."""
    history = ClinicalHistory(has_type2_diabetes=True, phq9_item_9_score=2)
    enc = _make_encounter(id="8", bmi=32.0, history=history)
    result = motor.compute(enc)
    critical = [a for a in result.action_checklist if a.priority == "critical"]
    assert len(critical) > 0
    assert (
        "riesgo suicida" in str(critical[0].task).lower()
        or "contraindicado" in str(critical[0].task).lower()
    )


def test_aom_glp1_recommended_when_eligible(motor):
    """T-AOM-06: GLP-1 recommended as first-line when no contraindications."""
    history = ClinicalHistory(has_type2_diabetes=True)
    enc = _make_encounter(id="9", bmi=35.0, history=history)
    result = motor.compute(enc)
    glp1_actions = [
        a
        for a in result.action_checklist
        if "GLP-1" in a.task or "semaglutida" in a.task
    ]
    assert len(glp1_actions) > 0


def test_aom_pregnancy_contraindication(motor):
    """T-AOM-07: Pregnancy = GLP-1 contraindicated."""
    history = ClinicalHistory(pregnancy_status="pregnant")
    enc = _make_encounter(id="10", bmi=35.0, history=history)
    result = motor.compute(enc)
    assert "embarazo" in result.explanation.lower()


def test_aom_phentermine_contraindicated_htn(motor):
    """T-AOM-08: Phentermine contraindicated with uncontrolled HTN."""
    history = ClinicalHistory(has_hypertension=True)
    enc = _make_encounter(id="11", bmi=35.0, history=history)
    result = motor.compute(enc)
    assert "Fentermina contraindicada" in result.explanation
