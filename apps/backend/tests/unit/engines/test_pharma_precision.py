"""
Golden Motor Tests: PharmaPrecisionMotor (IEC 62304 V&V)
=========================================================
Tests for Master Pharmacological Prescriber V2.
Test IDs: T-PHARMA-01 through T-PHARMA-06.
Evidence: ADA 2026, KDIGO 2024, Ahlqvist 2018.
"""

import pytest
from src.engines.specialty.pharma_precision import PharmaPrecisionMotor
from src.engines.domain import Encounter, Observation, ClinicalHistory, MedicationStatement
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)

@pytest.fixture
def motor():
    return PharmaPrecisionMotor()

def _make_encounter(id="pharma-test", bmi=32.0, history=None, observations=None):
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata={"sex": "male"},
        history=history or ClinicalHistory(),
    )

def test_pharma_validate_missing_bmi(motor):
    """T-PHARMA-01: No BMI = validation failure."""
    enc = _make_encounter(id="1", bmi=None)
    is_valid, msg = motor.validate(enc)
    assert is_valid is False

def test_pharma_cardiorenal_priority(motor):
    """T-PHARMA-02: CKD/HF = Prioritize SGLT2i."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="33914-3", value=45), # eGFR 45
        ],
        history=ClinicalHistory(has_heart_failure=True)
    )
    result = motor.compute(enc)
    assert any("iSGLT2" in a.task for a in result.action_checklist)
    assert any("CARDIORENAL-BENEFIT" in e.code for e in result.evidence)

def test_pharma_sarcopenia_warning(motor):
    """T-PHARMA-03: Sarcopenia = GLP-1 with caution."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="8302-2", value=170),
            Observation(code="29463-7", value=90),  # BMI ~31
            Observation(code="BIA-MUSCLE-KG", value=15),  # Low SMI
        ]
    )
    result = motor.compute(enc)
    assert any("Vigilancia de Masa Magra" in a.task for a in result.action_checklist)

def test_pharma_mtc_contraindication(motor):
    """T-PHARMA-04: MTC = GLP-1 absolute contraindication."""
    enc = _make_encounter(
        id="4",
        history=ClinicalHistory(has_history_medullary_thyroid_carcinoma=True)
    )
    result = motor.compute(enc)
    assert any(gap.gap_type == "CONTRAINDICATED" for gap in result.critical_omissions)

def test_pharma_phenotype_emotional_eating(motor):
    """T-PHARMA-05: Emotional eating = Psiconutrición referral."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="TFEQ-EMOTIONAL", value=3.5),
        ]
    )
    result = motor.compute(enc)
    assert any("Psiconutrición" in a.task for a in result.action_checklist)

def test_pharma_metformin_restriction(motor):
    """T-PHARMA-06: eGFR < 45 = Metformin restriction."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=60, gender="male"),
        metabolic_panel=MetabolicPanelSchema(creatinine_mg_dl=1.9),  # eGFR ~38
        observations=[
            Observation(code="29463-7", value=90),
            Observation(code="8302-2", value=170),
            Observation(code="AGE-001", value=60),
        ],
        metadata={"sex": "male"},
        history=ClinicalHistory(),
    )
    result = motor.compute(enc)
    assert any("Metformina" in a.task and "1000mg" in a.task for a in result.action_checklist)
