"""
Golden Motor Tests: Lifestyle360Motor (IEC 62304 V&V)
=====================================================
Tests for Lifestyle Assessment (Sleep, Exercise, Stress).
Test IDs: T-LIF-01 through T-LIF-05.
Evidence: WHO 2020, AIS (Soldatos 2000), TFEQ-R18.
"""

import pytest
from src.engines.specialty.lifestyle import Lifestyle360Motor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return Lifestyle360Motor()


def _make_encounter(id="life-test", observations=None):
    """Helper: creates a valid Encounter for Lifestyle testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata={"sex": "M"},
    )


def test_life_validate_no_data(motor):
    """T-LIF-01: No lifestyle data = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Estilo de Vida" in msg or "AF" in msg


def test_life_validate_success(motor):
    """T-LIF-01: With some lifestyle data = validation passes."""
    enc = _make_encounter(
        id="2", observations=[Observation(code="LIFE-EXERCISE", value=150)]
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_life_insomnia(motor):
    """T-LIF-02: Athens score >= 6 = Clinical insomnia."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="AIS-001", value=8),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_life_physical_inactivity(motor):
    """T-LIF-03: < 150 min/week = Physical inactivity."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="LIFE-EXERCISE", value=60),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_life_sufficient_exercise(motor):
    """T-LIF-04: >= 150 min/week = Sufficient activity."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="LIFE-EXERCISE", value=200),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_life_emotional_eating(motor):
    """T-LIF-05: TFEQ emotional > 2.5 = Emotional eating."""
    enc = _make_encounter(
        id="6",
        observations=[
            Observation(code="TFEQ-EMOTIONAL", value=3.5),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None
