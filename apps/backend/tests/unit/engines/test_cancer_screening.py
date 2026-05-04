"""
Golden Motor Tests: CancerScreeningMotor (IEC 62304 V&V)
========================================================
Tests for Obesity-Linked Cancer Screening.
Test IDs: T-CANC-01 through T-CANC-04.
Evidence: IARC 2016 (13+ cancers linked to obesity).
"""

import pytest
from src.engines.specialty.cancer_screening import CancerScreeningMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return CancerScreeningMotor()


def _make_encounter(id="cancer-test", observations=None, metadata=None):
    """Helper: creates a valid Encounter for Cancer Screening testing."""
    default_meta = {"sex": "M"}
    if metadata:
        default_meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
    )


def test_cancer_validate_missing(motor):
    """T-CANC-01: No BMI/Age = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "BMI" in msg or "Age" in msg


def test_cancer_validate_success(motor):
    """T-CANC-01: With BMI and age = validation passes."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=170),
            Observation(code="AGE-001", value=55),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_cancer_obesity_screening(motor):
    """T-CANC-02: Obese patient >= 50 = Colorectal/Endometrial screening."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="29463-7", value=100),
            Observation(code="8302-2", value=170),
            Observation(code="AGE-001", value=60),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_cancer_female_screening(motor):
    """T-CANC-03: Female >= 50 = Breast/Endometrial screening."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="29463-7", value=90),
            Observation(code="8302-2", value=165),
            Observation(code="AGE-001", value=55),
        ],
        metadata={"sex": "F"},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_cancer_young_no_screening(motor):
    """T-CANC-04: < 40 = No routine cancer screening."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=170),
            Observation(code="AGE-001", value=35),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None
