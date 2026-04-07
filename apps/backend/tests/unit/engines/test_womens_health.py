"""
Golden Motor Tests: WomensHealthMotor (IEC 62304 V&V)
=======================================================
Tests for Women's Health Assessment Engine.
Test IDs: T-WH-01 through T-WH-07.
Evidence: Rotterdam 2003, ACOG guidelines.
"""

import pytest
from src.engines.specialty.womens_health import WomensHealthMotor
from src.engines.domain import Encounter, ClinicalHistory
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return WomensHealthMotor()


def _make_encounter(id="wh-test", history=None, metadata=None, metabolic=None):
    """Helper: creates a valid Encounter for Women's Health testing."""
    default_meta = {"sex": "F"}
    if metadata:
        default_meta.update(metadata)
    mp = MetabolicPanelSchema()
    if metabolic:
        for k, v in metabolic.items():
            setattr(mp, k, v)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=35, gender="female"),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata=default_meta,
        history=history or ClinicalHistory(),
    )


def test_womens_health_validate_male(motor):
    """T-WH-01: Male patient = validation failure."""
    enc = _make_encounter(id="1", metadata={"sex": "M"})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "female" in msg.lower()


def test_womens_health_validate_female(motor):
    """T-WH-01: Female patient = validation passes."""
    enc = _make_encounter(id="2")
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_womens_health_sop_confirmed(motor):
    """T-WH-02: 2+ Rotterdam criteria = SOP confirmed."""
    history = ClinicalHistory(
        cycle_regularity="irregular",
        ferriman_gallwey_score=10,
    )
    enc = _make_encounter(id="3", history=history)
    result = motor.compute(enc)
    assert result.metadata["sop_confirmed"] is True
    assert "Ovario Poliquistico" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_womens_health_pregnancy_gate(motor):
    """T-WH-04: Pregnant = critical action for teratogenic meds."""
    history = ClinicalHistory(pregnancy_status="pregnant")
    enc = _make_encounter(id="5", history=history)
    result = motor.compute(enc)
    assert (
        "embarazada" in result.calculated_value.lower()
        or "embarazo" in result.calculated_value.lower()
    )
    critical = [a for a in result.action_checklist if a.priority == "critical"]
    assert len(critical) > 0


def test_womens_health_preeclampsia_history(motor):
    """T-WH-05: History of preeclampsia = CV risk factor."""
    history = ClinicalHistory(has_history_preeclampsia=True)
    enc = _make_encounter(id="6", history=history)
    result = motor.compute(enc)
    assert "preeclampsia" in result.explanation.lower()


def test_womens_health_gestational_diabetes(motor):
    """T-WH-06: History of GDM = 7x DM2 risk."""
    history = ClinicalHistory(has_history_gestational_diabetes=True)
    enc = _make_encounter(id="7", history=history)
    result = motor.compute(enc)
    assert "gestacional" in result.explanation.lower()


def test_womens_health_postmenopausal(motor):
    """T-WH-07: Postmenopausal = increased CV risk."""
    history = ClinicalHistory(menopausal_status="post")
    enc = _make_encounter(id="8", history=history)
    result = motor.compute(enc)
    assert (
        "Post-menopausica" in result.explanation
        or "menopausia" in result.explanation.lower()
    )


def test_womens_health_no_findings(motor):
    """T-WH-07: Female, no risk factors = no findings."""
    enc = _make_encounter(id="9")
    result = motor.compute(enc)
    assert (
        "sin hallazgos" in result.calculated_value.lower()
        or "sin preocupacion" in result.calculated_value.lower()
    )


def test_womens_health_amh_criterion(motor):
    """T-WH-03: AMH > 4.5 ng/mL = polycystic morphology criterion."""
    history = ClinicalHistory(cycle_regularity="irregular")
    enc = _make_encounter(id="10", history=history, metabolic={"amh_ng_ml": 8.0})
    result = motor.compute(enc)
    assert result.metadata["sop_criteria"] >= 2
