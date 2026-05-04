"""
Golden Motor Tests: VAIMotor (IEC 62304 V&V)
==============================================
Tests for Visceral Adiposity Index.
Test IDs: T-VAI-01 through T-VAI-03.
Evidence: Amato et al., 2010.
"""

import pytest
from src.engines.specialty.visceral_adiposity import VAIMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return VAIMotor()

def test_vai_male_high(motor):
    """T-VAI-01: High VAI in male."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(triglycerides_mg_dl=250, hdl_mg_dl=35),
        observations=[
            Observation(code="29463-7", value=100),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=110),
        ]
    )
    result = motor.compute(enc)
    assert result.metadata["vai"] > 1.0
    assert result.estado_ui == "CONFIRMED_ACTIVE"
