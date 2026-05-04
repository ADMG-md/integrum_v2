"""
Golden Motor Tests: LaboratoryStewardshipMotor (IEC 62304 V&V)
=============================================================
Tests for Precision Eligibility Engine (LATAM Strategy).
Test IDs: T-STEW-01 through T-STEW-04.
Evidence: Ahlqvist 2018, Sniderman 2019, Angulo 2007.
"""

import pytest
from src.engines.specialty.stewardship import LaboratoryStewardshipMotor
from src.engines.domain import Encounter, Observation, Condition
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)

@pytest.fixture
def motor():
    return LaboratoryStewardshipMotor()

def _make_encounter(id="stew-test", observations=None, conditions=None):
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        conditions=conditions or [],
    )

def test_stewardship_ahlqvist_pack_eligibility(motor):
    """T-STEW-01: High HbA1c + Low BMI = Suggest Pack Ahlqvist."""
    enc = _make_encounter(
        id="1",
        observations=[
            Observation(code="4548-4", value=8.5), # HbA1c 8.5
            Observation(code="29463-7", value=65), # Weight 65
            Observation(code="8302-2", value=175), # Height 175 -> BMI < 25
        ]
    )
    result = motor.compute(enc)
    assert "Pack Ahlqvist" in result.calculated_value
    assert any(e.code == "LADA_SUSPICION" for e in result.evidence)

def test_stewardship_thyroid_360_eligibility(motor):
    """T-STEW-02: Normal TSH + Anxiety/Insomnia = Suggest Thyroid 360."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="11579-0", value=2.0), # Normal TSH
        ],
        conditions=[
            Condition(code="F41.1", title="Anxiety", system="CIE-10")
        ]
    )
    result = motor.compute(enc)
    assert "Thyroid 360" in result.calculated_value

def test_stewardship_apob_pack_eligibility(motor):
    """T-STEW-03: Atherogenic dyslipidemia = Suggest Cardio-ApoB Pack."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="18262-6", value=140), # LDL > 130
            Observation(code="2571-8", value=160),  # TG > 150
        ]
    )
    result = motor.compute(enc)
    assert "Cardio-ApoB Pack" in result.calculated_value

def test_stewardship_liver_staging_eligibility(motor):
    """T-STEW-04: Elevated transaminases = Suggest Profile MASLD."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="22538-3", value=35), # ALT > 30
        ]
    )
    result = motor.compute(enc)
    assert "Perfil MASLD" in result.calculated_value
