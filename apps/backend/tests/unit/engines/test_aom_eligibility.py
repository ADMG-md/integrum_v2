"""
Golden Motor Tests: ObesityPharmaEligibilityMotor (IEC 62304 V&V)
===================================================================
Tests for Anti-Obesity Medication (AOM) Eligibility Engine.
Test IDs: T-AOM-01 through T-AOM-08.
Evidence: FDA Guidance 2024.
"""

import pytest
from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor
from src.engines.domain import Encounter, Observation, ClinicalHistory

@pytest.fixture
def motor():
    return ObesityPharmaEligibilityMotor()

def test_aom_eligible_bmi_32(motor):
    """T-AOM-01: BMI 32 = Eligible."""
    enc = Encounter(
        id="1",
        demographics={"age_years": 50},
        metabolic_panel={},
        observations=[
            Observation(code="29463-7", value=92), # Weight 92
            Observation(code="8302-2", value=170), # Height 170 -> BMI 31.8
        ],
        history=ClinicalHistory()
    )
    result = motor.compute(enc)
    assert result.metadata["eligible"] is True
    assert result.estado_ui == "CONFIRMED_ACTIVE"
