import pytest
from src.engines.specialty.hemodynamics import PulsePressureMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return PulsePressureMotor()


def test_hemo_validate_missing(motor):
    """T-HEMO-01: Validation fails without SBP/DBP."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is False


def test_hemo_validate_success(motor):
    """T-HEMO-02: Validation passes with SBP and DBP."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="8480-6", value=120),
            Observation(code="8462-4", value=80),
        ],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_hemo_wide_pulse_pressure(motor):
    """T-HEMO-03: PP > 60 = wide pulse pressure (arterial stiffness)."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=60, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="8480-6", value=160),
            Observation(code="8462-4", value=80),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "amplia" in result.explanation


def test_hemo_borderline_pulse_pressure(motor):
    """T-HEMO-04: PP 50-60 = borderline."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="8480-6", value=135),
            Observation(code="8462-4", value=80),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"
    assert "limtrofe" in result.explanation


def test_hemo_normal_pulse_pressure(motor):
    """T-HEMO-05: PP < 50 = normal."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="8480-6", value=120),
            Observation(code="8462-4", value=80),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "normal" in result.explanation


def test_hemo_low_map(motor):
    """T-HEMO-06: MAP < 65 = low perfusion risk."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="8480-6", value=65),
            Observation(code="8462-4", value=55),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert "hipoperfusion" in result.explanation
    assert result.metadata.get("map") is not None
    assert result.metadata.get("map") < 65
