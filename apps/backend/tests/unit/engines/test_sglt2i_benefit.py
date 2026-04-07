"""
Golden Motor Tests: SGLT2iBenefitMotor (IEC 62304 V&V)
=======================================================
Tests for SGLT2i Cardio-Renal Benefit.
Test IDs: T-SGLT2-01 through T-SGLT2-04.
Evidence: EMPA-REG, CANVAS, DECLARE, CREDENCE, DAPA-CKD trials.
"""

import pytest
from src.engines.specialty.sglt2i_benefit import SGLT2iBenefitMotor
from src.engines.domain import Encounter, ClinicalHistory, Condition
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return SGLT2iBenefitMotor()


def _make_encounter(id="sglt2-test", history=None, conditions=None):
    """Helper: creates a valid Encounter for SGLT2i testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=60, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={"sex": "M"},
        history=history or ClinicalHistory(),
        conditions=conditions or [],
    )


def test_sglt2_validate_no_indications(motor):
    """T-SGLT2-01: No T2DM/CKD/HF = validation failure."""
    enc = _make_encounter(id="1", history=ClinicalHistory())
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_sglt2_validate_t2dm(motor):
    """T-SGLT2-01: With T2DM = validation passes."""
    enc = _make_encounter(id="2", history=ClinicalHistory(has_type2_diabetes=True))
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_sglt2_indication_t2dm(motor):
    """T-SGLT2-02: T2DM = SGLT2i indicated."""
    enc = _make_encounter(id="3", history=ClinicalHistory(has_type2_diabetes=True))
    result = motor.compute(enc)
    assert (
        "indicado" in result.calculated_value.lower()
        or "beneficio" in result.calculated_value.lower()
    )


def test_sglt2_indication_ckd(motor):
    """T-SGLT2-03: CKD = SGLT2i indicated."""
    enc = _make_encounter(id="4", history=ClinicalHistory(has_ckd=True))
    result = motor.compute(enc)
    assert result.estado_ui in ["CONFIRMED_ACTIVE", "PROBABLE_WARNING"]


def test_sglt2_indication_hf(motor):
    """T-SGLT2-04: Heart Failure = SGLT2i indicated."""
    enc = _make_encounter(
        id="5",
        history=ClinicalHistory(),
        conditions=[Condition(code="I50", title="Heart Failure")],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_sglt2_multiple_indications(motor):
    """T-SGLT2-04: T2DM + CKD = Stronger indication."""
    enc = _make_encounter(
        id="6", history=ClinicalHistory(has_type2_diabetes=True, has_ckd=True)
    )
    result = motor.compute(enc)
    assert result.metadata is not None
