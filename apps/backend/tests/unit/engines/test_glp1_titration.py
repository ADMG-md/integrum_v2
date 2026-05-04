"""
Golden Motor Tests: GLP1TitrationMotor (IEC 62304 V&V)
=========================================================
Tests for GLP-1/GIP Dose Titration Protocol Engine.
Test IDs: T-GLP-TIT-01 through T-GLP-TIT-05.
Evidence: FDA Labeling, STEP trials, SURMOUNT trials.
"""

import pytest
from src.engines.specialty.glp1_titration import GLP1TitrationMotor
from src.engines.domain import Encounter, Observation, MedicationStatement
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)

@pytest.fixture
def motor():
    return GLP1TitrationMotor()

def _make_encounter(id="glp-tit-test", medications=None, metadata=None, observations=None):
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        medications=medications or [],
        metadata=metadata or {},
    )

def test_glp1_titration_validate_no_glp1(motor):
    """T-GLP-TIT-01: No GLP-1 therapy = validation failure."""
    enc = _make_encounter(id="1", medications=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "No GLP-1" in msg

def test_glp1_titration_validate_success(motor):
    """T-GLP-TIT-01: With GLP-1 = validation passes."""
    enc = _make_encounter(
        id="2",
        medications=[
            MedicationStatement(code="SEMAGLUTIDE", name="Semaglutide", is_active=True)
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True

def test_glp1_titration_suboptimal_response(motor):
    """T-GLP-TIT-02: <5% weight loss at 12+ weeks = suboptimal response."""
    enc = _make_encounter(
        id="3",
        medications=[
            MedicationStatement(code="SEMAGLUTIDE", name="Semaglutide", dose_amount="0.5mg", is_active=True)
        ],
        observations=[
            Observation(code="29463-7", value=98), # Current weight
        ],
        metadata={
            "glp1_weeks": 14,
            "prev_weight_kg": 100, # 2% loss
        }
    )
    result = motor.compute(enc)
    assert "subóptima" in result.calculated_value
    assert any("Escalar dosis" in a.task for a in result.action_checklist)

def test_glp1_titration_max_dose_reached(motor):
    """T-GLP-TIT-03: Suboptimal response at max dose = consider alternative."""
    enc = _make_encounter(
        id="4",
        medications=[
            MedicationStatement(code="SEMAGLUTIDE", name="Wegovy", dose_amount="2.4mg", is_active=True)
        ],
        observations=[
            Observation(code="29463-7", value=98),
        ],
        metadata={
            "glp1_weeks": 14,
            "prev_weight_kg": 100,
        }
    )
    result = motor.compute(enc)
    assert "máxima" in result.explanation
    assert any("Evaluar cambio" in a.task for a in result.action_checklist)

def test_glp1_titration_adequate_response(motor):
    """T-GLP-TIT-04: >=5% weight loss = adequate response."""
    enc = _make_encounter(
        id="5",
        medications=[
            MedicationStatement(code="TIRZEPATIDE", name="Zepbound", dose_amount="5mg", is_active=True)
        ],
        observations=[
            Observation(code="29463-7", value=94), # 6% loss
        ],
        metadata={
            "glp1_weeks": 16,
            "prev_weight_kg": 100,
        }
    )
    result = motor.compute(enc)
    assert "adecuada" in result.calculated_value
