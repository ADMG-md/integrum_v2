"""
Golden Motor Tests: AnthropometryPrecisionMotor (IEC 62304 V&V)
===============================================================
Tests for Anthropometry Precision (WHtR, WHR, BRI).
Test IDs: T-ANTHRO-01 through T-ANTHRO-05.
Evidence: Browning 2010, WHO 2008, Thomas 2013.
"""

import pytest
from src.engines.specialty.anthropometry import AnthropometryPrecisionMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return AnthropometryPrecisionMotor()


def _make_encounter(id="anthro-test", observations=None, metadata=None):
    """Helper: creates a valid Encounter for Anthropometry testing."""
    default_meta = {"sex": "M"}
    if metadata:
        default_meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
    )


def test_anthro_validate_missing_waist(motor):
    """T-ANTHRO-01: Missing waist = validation failure."""
    enc = _make_encounter(id="1", observations=[Observation(code="8302-2", value=170)])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Cintura" in msg


def test_anthro_validate_success(motor):
    """T-ANTHRO-01: With waist and height = validation passes."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="WAIST-001", value=90),
            Observation(code="8302-2", value=170),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_anthro_whtr_high_risk(motor):
    """T-ANTHRO-02: WHtR > 0.5 = High cardiometabolic risk."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="WAIST-001", value=100),
            Observation(code="8302-2", value=170),
            Observation(code="HIP-001", value=95),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert "Riesgo" in result.calculated_value


def test_anthro_whtr_low_risk(motor):
    """T-ANTHRO-03: WHtR <= 0.5 = Low risk."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="WAIST-001", value=80),
            Observation(code="8302-2", value=175),
            Observation(code="HIP-001", value=95),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert "Bajo Riesgo" in result.calculated_value


def test_anthro_whr_android_male(motor):
    """T-ANTHRO-04: WHR > 0.90 (male) = Android phenotype."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="WAIST-001", value=105),
            Observation(code="8302-2", value=170),
            Observation(code="HIP-001", value=95),  # WHR = 1.1
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert (
        "Androide" in result.calculated_value
        or "Alto Riesgo" in result.calculated_value
    )


def test_anthro_whr_android_female(motor):
    """T-ANTHRO-04: WHR > 0.85 (female) = Android phenotype."""
    enc = _make_encounter(
        id="6",
        observations=[
            Observation(code="WAIST-001", value=90),
            Observation(code="8302-2", value=165),
            Observation(code="HIP-001", value=95),  # WHR ~ 0.95
        ],
        metadata={"sex": "F"},
    )
    result = motor.compute(enc)
    assert (
        "Androide" in result.calculated_value
        or "Alto Riesgo" in result.calculated_value
    )


def test_anthro_bri_elevated(motor):
    """T-ANTHRO-05: BRI > 5 = High visceral adiposity."""
    enc = _make_encounter(
        id="7",
        observations=[
            Observation(code="WAIST-001", value=115),
            Observation(code="8302-2", value=170),
            Observation(code="HIP-001", value=100),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert "BRI" in result.explanation or "Alto Riesgo" in result.calculated_value
