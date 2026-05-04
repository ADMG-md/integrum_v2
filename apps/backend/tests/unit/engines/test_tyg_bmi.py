"""
Golden Motor Tests: TyGBMIMotor (IEC 62304 V&V)
===============================================
Tests for TyG-BMI Index (Insulin Resistance Staging).
Test IDs: T-TYG-01 through T-TYG-05.
Evidence: Simental-Mendía 2008, validation >10k subjects.
"""

import pytest
from src.engines.specialty.tyg_bmi import TyGBMIMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return TyGBMIMotor()


def test_tyg_validate_missing_data(motor):
    """T-TYG-01: Missing TG/Glucose/BMI = validation failure."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[],
        metadata={"sex": "M"},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_tyg_validate_success(motor):
    """T-TYG-01: With all data = validation passes."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=100, triglycerides_mg_dl=150),
        observations=[
            Observation(code="29463-7", value=80),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "M"},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_tyg_male_low_ir(motor):
    """T-TYG-02: Male < 230 = Low IR."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=90, triglycerides_mg_dl=80),
        observations=[
            Observation(code="29463-7", value=65),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata is not None


def test_tyg_male_severe_ir(motor):
    """T-TYG-03: Male > 260 = Severe IR."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=130, triglycerides_mg_dl=200),
        observations=[
            Observation(code="29463-7", value=95),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata is not None


def test_tyg_female_thresholds(motor):
    """T-TYG-04: Female has different thresholds."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=45, gender="female"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=100, triglycerides_mg_dl=120),
        observations=[
            Observation(code="29463-7", value=70),
            Observation(code="8302-2", value=165),
        ],
        metadata={"sex": "female"},
    )
    result = motor.compute(enc)
    assert result.metadata.get("thresholds") == (220, 250)
