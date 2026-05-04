"""
Golden Motor Tests: HypertensionSecondaryMotor (IEC 62304 V&V)
================================================================
Tests for Secondary Hypertension Screening (Primary Aldosteronism).
Test IDs: T-HTN-01 through T-HTN-05.
Evidence: Endocrine Society 2016 (Funder), ESC/ESH 2018.
"""

import pytest
from src.engines.specialty.hypertension import HypertensionSecondaryMotor
from src.engines.domain import Encounter, Observation, Condition
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return HypertensionSecondaryMotor()


def _make_encounter(id="htn-test", conditions=None, observations=None):
    """Helper: creates a valid Encounter for Hypertension testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        conditions=conditions or [],
        observations=observations or [],
        metadata={},
    )


def test_hypertension_validate_no_htn(motor):
    """T-HTN-01: Patient without hypertension should not be validated."""
    enc = _make_encounter(id="1")
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "not hypertensive" in msg


def test_hypertension_validate_with_htn_code(motor):
    """T-HTN-01: Patient with I10 code should pass validation."""
    enc = _make_encounter(
        id="2",
        conditions=[
            Condition(code="I10", title="Essential Hypertension"),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_hypertension_validate_high_bp_reading(motor):
    """T-HTN-01: Patient with systolic BP >= 140 should pass validation."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="8480-6", value=145),  # Systolic BP
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_hypertension_arr_positive(motor):
    """T-HTN-02: ARR > 30 + aldosterone > 15 should flag high risk for PA."""
    enc = _make_encounter(
        id="4",
        conditions=[
            Condition(code="I10", title="Hypertension"),
        ],
        observations=[
            Observation(code="1762-0", value=20),  # Aldosterone 20 ng/dL
            Observation(code="2889-4", value=0.5),  # Renin 0.5 ng/mL/h → ARR = 40
        ],
    )
    result = motor.compute(enc)
    assert (
        "High risk" in result.calculated_value
        or "Primary Aldosteronism" in result.calculated_value
    )
    assert result.confidence == 0.9


def test_hypertension_arr_negative(motor):
    """T-HTN-02: ARR <= 30 should be negative screening."""
    enc = _make_encounter(
        id="5",
        conditions=[
            Condition(code="I10", title="Hypertension"),
        ],
        observations=[
            Observation(code="1762-0", value=10),  # Aldosterone 10 ng/dL
            Observation(code="2889-4", value=1.0),  # Renin 1.0 → ARR = 10
        ],
    )
    result = motor.compute(enc)
    assert "Negative" in result.calculated_value


def test_hypertension_arr_boundary_30(motor):
    """T-HTN-03: ARR = 30 exactly should be negative (threshold is > 30)."""
    enc = _make_encounter(
        id="6",
        conditions=[
            Condition(code="I10", title="Hypertension"),
        ],
        observations=[
            Observation(code="1762-0", value=15),
            Observation(code="2889-4", value=0.5),  # ARR = 30 exactly
        ],
    )
    result = motor.compute(enc)
    assert "Negative" in result.calculated_value


def test_hypertension_no_arr_data(motor):
    """T-HTN-04: Missing aldosterone/renin should return no data status."""
    enc = _make_encounter(
        id="7",
        conditions=[
            Condition(code="I10", title="Hypertension"),
        ],
    )
    result = motor.compute(enc)
    assert "No secondary HTA screening data" in result.calculated_value
    assert result.confidence == 0.7


def test_hypertension_arr_with_low_aldosterone(motor):
    """T-HTN-05: ARR > 30 but aldosterone < 15 should be negative."""
    enc = _make_encounter(
        id="8",
        conditions=[
            Condition(code="I10", title="Hypertension"),
        ],
        observations=[
            Observation(code="1762-0", value=10),  # Aldosterone too low
            Observation(
                code="2889-4", value=0.2
            ),  # ARR = 50 (>30) but aldosterone < 15
        ],
    )
    result = motor.compute(enc)
    assert "Negative" in result.calculated_value
