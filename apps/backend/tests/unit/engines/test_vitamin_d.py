"""
Golden Motor Tests: VitaminDMotor (IEC 62304 V&V)
==================================================
Tests for Vitamin D Status Assessment.
Test IDs: T-VITD-01 through T-VITD-06.
Evidence: Holick 2011 (Endocrine Society).
"""

import pytest
from src.engines.specialty.vitamin_d import VitaminDMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return VitaminDMotor()


def _make_encounter(id="vitd-test", observations=None, vitd_value=None):
    """Helper: creates a valid Encounter for Vitamin D testing."""
    mp = MetabolicPanelSchema()
    if vitd_value is not None:
        mp.vitamin_d_ng_ml = vitd_value
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        metadata={},
    )


def test_vitd_validate_missing(motor):
    """T-VITD-01: No Vitamin D = validation failure."""
    enc = _make_encounter(id="1")
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Vitamin D" in msg


def test_vitd_validate_success(motor):
    """T-VITD-01: With Vitamin D = validation passes."""
    enc = _make_encounter(id="2", vitd_value=30)
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_vitd_severe_deficiency(motor):
    """T-VITD-02: < 10 ng/mL = Severe deficiency."""
    enc = _make_encounter(id="3", vitd_value=8)
    result = motor.compute(enc)
    assert "SEVERA" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.confidence == 0.95


def test_vitd_deficiency(motor):
    """T-VITD-03: 10-20 ng/mL = Deficiency."""
    enc = _make_encounter(id="4", vitd_value=15)
    result = motor.compute(enc)
    assert "Deficiencia" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_vitd_insufficiency(motor):
    """T-VITD-04: 20-30 ng/mL = Insufficiency."""
    enc = _make_encounter(id="5", vitd_value=25)
    result = motor.compute(enc)
    assert "Insuficiencia" in result.calculated_value
    assert result.estado_ui == "PROBABLE_WARNING"


def test_vitd_sufficient(motor):
    """T-VITD-05: 30-100 ng/mL = Sufficient."""
    enc = _make_encounter(id="6", vitd_value=45)
    result = motor.compute(enc)
    assert "suficiente" in result.calculated_value.lower()
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_vitd_elevated(motor):
    """T-VITD-05: 100-150 ng/mL = Elevated."""
    enc = _make_encounter(id="7", vitd_value=120)
    result = motor.compute(enc)
    assert "elevada" in result.calculated_value.lower()
    assert result.estado_ui == "PROBABLE_WARNING"


def test_vitd_toxicity(motor):
    """T-VITD-06: > 150 ng/mL = Toxicity."""
    enc = _make_encounter(id="8", vitd_value=160)
    result = motor.compute(enc)
    assert "toxicidad" in result.calculated_value.lower()
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_vitd_boundary_20(motor):
    """T-VITD-06: 20 exactly = insufficiency."""
    enc = _make_encounter(id="9", vitd_value=20)
    result = motor.compute(enc)
    assert "Insuficiencia" in result.calculated_value


def test_vitd_boundary_30(motor):
    """T-VITD-06: 30 exactly = sufficient."""
    enc = _make_encounter(id="10", vitd_value=30)
    result = motor.compute(enc)
    assert "suficiente" in result.calculated_value.lower()
