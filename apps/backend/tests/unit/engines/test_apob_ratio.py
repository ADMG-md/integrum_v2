"""
Golden Motor Tests: ApoBApoA1Motor (IEC 62304 V&V)
=================================================
Tests for ApoB/ApoA1 Ratio (INTERHEART).
Test IDs: T-APO-01 through T-APO-05.
Evidence: Yusuf et al., 2004 (INTERHEART).
"""

import pytest
from src.engines.specialty.apob_ratio import ApoBApoA1Motor
from src.engines.domain import Encounter
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return ApoBApoA1Motor()


def _make_encounter(id="apo-test", cardio=None):
    """Helper: creates a valid Encounter for ApoB/ApoA1 testing."""
    cp = CardioPanelSchema()
    if cardio:
        for k, v in cardio.items():
            setattr(cp, k, v)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=cp,
        observations=[],
        metadata={},
    )


def test_apo_validate_missing_apob(motor):
    """T-APO-01: Missing ApoB = validation failure."""
    enc = _make_encounter(id="1", cardio={"apoa1_mg_dl": 150})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_apo_validate_missing_apoa1(motor):
    """T-APO-01: Missing ApoA1 = validation failure."""
    enc = _make_encounter(id="2", cardio={"apob_mg_dl": 100})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_apo_validate_success(motor):
    """T-APO-01: With both = validation passes."""
    enc = _make_encounter(id="3", cardio={"apob_mg_dl": 100, "apoa1_mg_dl": 150})
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_apo_low_risk(motor):
    """T-APO-02: Ratio < 0.6 = Low risk."""
    enc = _make_encounter(id="4", cardio={"apob_mg_dl": 60, "apoa1_mg_dl": 140})
    result = motor.compute(enc)
    assert "Bajo" in result.calculated_value
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_apo_moderate_risk(motor):
    """T-APO-03: Ratio 0.6-0.8 = Moderate risk."""
    enc = _make_encounter(id="5", cardio={"apob_mg_dl": 90, "apoa1_mg_dl": 130})
    result = motor.compute(enc)
    assert "Moderado" in result.calculated_value
    assert result.estado_ui == "PROBABLE_WARNING"


def test_apo_high_risk(motor):
    """T-APO-04: Ratio 0.8-1.0 = High risk."""
    enc = _make_encounter(id="6", cardio={"apob_mg_dl": 110, "apoa1_mg_dl": 130})
    result = motor.compute(enc)
    assert "Alto" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_apo_very_high_risk(motor):
    """T-APO-05: Ratio > 1.0 = Very high risk."""
    enc = _make_encounter(id="7", cardio={"apob_mg_dl": 150, "apoa1_mg_dl": 130})
    result = motor.compute(enc)
    assert "Muy Alto" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_apo_boundary_06(motor):
    """T-APO-05: Ratio = 0.6 exactly = Moderate."""
    enc = _make_encounter(id="8", cardio={"apob_mg_dl": 78, "apoa1_mg_dl": 130})
    result = motor.compute(enc)
    assert result.metadata["ratio"] < 0.8
