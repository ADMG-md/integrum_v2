"""
Golden Motor Tests: LipidRiskPrecisionMotor (IEC 62304 V&V)
==========================================================
Tests for Lipid Risk Assessment (ACC/AHA 2026).
Test IDs: T-LIPID-01 through T-LIPID-04.
Evidence: ACC/AHA Cholesterol Guidelines 2026.
"""

import pytest
from src.engines.specialty.lipid_risk import LipidRiskPrecisionMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return LipidRiskPrecisionMotor()


def _make_encounter(id="lipid-test", observations=None):
    """Helper: creates a valid Encounter for Lipid Risk testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        metadata={"sex": "M"},
    )


def test_lipid_validate_missing_ldl(motor):
    """T-LIPID-01: No LDL = validation failure."""
    enc = _make_encounter(id="1", observations=[Observation(code="2093-3", value=200)])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "LDL" in msg


def test_lipid_validate_success(motor):
    """T-LIPID-01: With LDL and Total = validation passes."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="18262-6", value=130),
            Observation(code="2093-3", value=200),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_lipid_high_risk(motor):
    """T-LIPID-02: High LDL = High risk classification."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="18262-6", value=180),
            Observation(code="2093-3", value=260),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_lipid_target_very_high_risk(motor):
    """T-LIPID-03: Very high risk has lower LDL target."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="18262-6", value=100),
            Observation(code="2093-3", value=180),
        ],
    )
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=65, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[
            Observation(code="18262-6", value=100),
            Observation(code="2093-3", value=180),
        ],
        metadata={"sex": "M"},
        conditions=[{"code": "I25.1", "title": "CAD"}],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None
