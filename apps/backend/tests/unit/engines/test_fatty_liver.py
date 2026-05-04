"""
Golden Motor Tests: FLIMotor (IEC 62304 V&V)
===============================================
Tests for Fatty Liver Index (NAFLD screening).
Test IDs: T-FLI-01 through T-FLI-06.
Evidence: Bedogni et al., 2006.
"""

import pytest
from src.engines.specialty.fatty_liver import FLIMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return FLIMotor()

def _make_encounter(id="fli-test", ggt=40, tg=150, bmi=30, waist=95):
    mp = MetabolicPanelSchema(ggt_u_l=ggt, triglycerides_mg_dl=tg)
    obs = [
        Observation(code="29463-7", value=bmi * 1.7 * 1.7), # BMI proxy
        Observation(code="8302-2", value=170),
        Observation(code="WAIST-001", value=waist),
    ]
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=mp,
        observations=obs
    )

def test_fli_high_risk(motor):
    """T-FLI-01: High risk scenario."""
    enc = _make_encounter(ggt=100, tg=250, bmi=35, waist=110)
    result = motor.compute(enc)
    assert result.metadata["category"] == "high"
    assert result.estado_ui == "CONFIRMED_ACTIVE"

def test_fli_low_risk(motor):
    """T-FLI-02: Low risk scenario."""
    enc = _make_encounter(ggt=20, tg=80, bmi=23, waist=80)
    result = motor.compute(enc)
    assert result.metadata["category"] == "low"
    assert result.estado_ui == "INDETERMINATE_LOCKED"
