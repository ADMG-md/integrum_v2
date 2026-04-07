"""
Golden Motor Tests: MensHealthMotor (IEC 62304 V&V)
====================================================
Tests for Men's Health Assessment Engine.
Test IDs: T-MH-01 through T-MH-07.
Evidence: AUA 2018, Endocrine Society 2018.
"""

import pytest
from src.engines.specialty.mens_health import MensHealthMotor
from src.engines.domain import Encounter, ClinicalHistory
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return MensHealthMotor()


def _make_encounter(id="mh-test", history=None, metadata=None, metabolic=None):
    """Helper: creates a valid Encounter for Men's Health testing."""
    default_meta = {"sex": "M"}
    if metadata:
        default_meta.update(metadata)
    mp = MetabolicPanelSchema()
    if metabolic:
        for k, v in metabolic.items():
            setattr(mp, k, v)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata=default_meta,
        history=history or ClinicalHistory(),
    )


def test_mens_health_validate_female(motor):
    """T-MH-01: Female patient = validation failure."""
    enc = _make_encounter(id="1", metadata={"sex": "F"})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "male" in msg.lower()


def test_mens_health_validate_male(motor):
    """T-MH-01: Male patient = validation passes."""
    enc = _make_encounter(id="2")
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_mens_health_hypogonadism_confirmed(motor):
    """T-MH-02: Low T + symptoms = hypogonadism confirmed."""
    history = ClinicalHistory(has_erectile_dysfunction=True)
    enc = _make_encounter(
        id="3",
        history=history,
        metabolic={"testosterone_total_ng_dl": 250},
    )
    result = motor.compute(enc)
    assert result.metadata["hypogonadism_risk"] >= 3
    assert (
        "Hipogonadismo" in result.calculated_value
        and "confirmado" in result.calculated_value.lower()
    )


def test_mens_health_hypogonadism_suspected(motor):
    """T-MH-03: Borderline T = hypogonadism suspected."""
    enc = _make_encounter(
        id="4",
        metabolic={"testosterone_total_ng_dl": 330},
    )
    result = motor.compute(enc)
    assert result.metadata["hypogonadism_risk"] >= 1


def test_mens_health_psa_high(motor):
    """T-MH-04: PSA > 4 = urology referral."""
    enc = _make_encounter(
        id="5",
        metabolic={"psa_ng_ml": 5.5},
    )
    result = motor.compute(enc)
    assert result.estado_ui in ["CONFIRMED_ACTIVE", "PROBABLE_WARNING"]
    high_priority = [
        a for a in result.action_checklist if a.priority in ["high", "critical"]
    ]
    assert len(high_priority) > 0


def test_mens_health_psa_critical(motor):
    """T-MH-05: PSA > 10 = urgent urology referral."""
    enc = _make_encounter(
        id="6",
        metabolic={"psa_ng_ml": 12.0},
    )
    result = motor.compute(enc)
    critical = [a for a in result.action_checklist if a.priority == "critical"]
    assert len(critical) > 0
    assert (
        "urgente" in critical[0].task.lower() or "biopsia" in critical[0].task.lower()
    )


def test_mens_health_ed_severe(motor):
    """T-MH-06: IIEF-5 <= 7 = severe ED."""
    history = ClinicalHistory(iief5_score=5)
    enc = _make_encounter(id="7", history=history)
    result = motor.compute(enc)
    assert (
        "severa" in result.calculated_value.lower()
        or "severa" in result.explanation.lower()
    )


def test_mens_health_secondary_hypogonadism(motor):
    """T-MH-07: Low T + low LH = secondary hypogonadism."""
    enc = _make_encounter(
        id="8",
        metabolic={
            "testosterone_total_ng_dl": 200,
            "lh_u_l": 3.0,  # Low LH
        },
    )
    result = motor.compute(enc)
    assert "secundario" in result.explanation.lower()


def test_mens_health_no_findings(motor):
    """T-MH-07: Male, no risk factors = no findings."""
    enc = _make_encounter(id="9")
    result = motor.compute(enc)
    assert (
        "sin hallazgos" in result.calculated_value.lower()
        or "sin preocupacion" in result.calculated_value.lower()
    )


def test_mens_health_gynecomastia(motor):
    """T-MH-06: Gynecomastia with low T = diagnostic action."""
    history = ClinicalHistory(has_gynecomastia=True)
    enc = _make_encounter(
        id="10",
        history=history,
        metabolic={"testosterone_total_ng_dl": 250},
    )
    result = motor.compute(enc)
    assert "ginecomastia" in result.explanation.lower()
