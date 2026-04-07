import pytest
from src.engines.specialty.ace_integration import ACEScoreEngine
from src.engines.domain import Encounter, ClinicalHistory, TraumaHistory
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return ACEScoreEngine()


def test_ace_validate_missing(motor):
    """T-ACE-01: Validation fails without ACE score."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=None),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is False


def test_ace_validate_success(motor):
    """T-ACE-02: Validation passes with ACE score."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=2)),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_ace_very_high(motor):
    """T-ACE-03: ACE >= 8 = very high risk (autoimmune, -20 years)."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=40, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=9)),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "autoinmune" in result.explanation
    assert result.action_checklist is not None
    assert len(result.action_checklist) >= 2


def test_ace_high(motor):
    """T-ACE-04: ACE 6-7 = high risk (-20 years life expectancy)."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=6)),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "20 anos" in result.explanation


def test_ace_moderate_high(motor):
    """T-ACE-05: ACE 4-5 = moderate-high (2x metabolic, 3x depression)."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=4)),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"
    assert "metabolica" in result.explanation


def test_ace_moderate(motor):
    """T-ACE-06: ACE 2-3 = moderate risk."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=2)),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"


def test_ace_low(motor):
    """T-ACE-07: ACE < 2 = low risk."""
    enc = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        history=ClinicalHistory(trauma=TraumaHistory(ace_score=0)),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "BAJO" in result.explanation
