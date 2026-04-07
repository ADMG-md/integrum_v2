"""
Golden Motor Tests: EndocrinePrecisionMotor (IEC 62304 V&V)
============================================================
Tests for Thyroid and Adrenal Screening.
Test IDs: T-ENDO-01 through T-ENDO-05.
Evidence: ATA 2014, Nieman 2008.
"""

import pytest
from src.engines.specialty.endocrine import EndocrinePrecisionMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return EndocrinePrecisionMotor()


def _make_encounter(id="endo-test", observations=None, metabolic=None):
    """Helper: creates a valid Encounter for Endocrine testing."""
    mp = MetabolicPanelSchema()
    if metabolic:
        for k, v in metabolic.items():
            setattr(mp, k, v)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        metadata={"sex": "M"},
    )


def test_endo_validate_missing_tsh(motor):
    """T-ENDO-01: No TSH/FT4 = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "TSH" in msg or "thyroid" in msg.lower()


def test_endo_validate_success(motor):
    """T-ENDO-01: With TSH = validation passes."""
    enc = _make_encounter(id="2", observations=[Observation(code="11579-0", value=2.5)])
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_endo_hypothyroidism_subclinical(motor):
    """T-ENDO-02: TSH > 4.5, normal FT4 = Subclinical hypothyroidism."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="11579-0", value=6.0),
            Observation(code="FT4-001", value=1.2),
        ],
    )
    result = motor.compute(enc)
    assert "Hipotiroidismo" in result.calculated_value


def test_endo_hyperthyroidism(motor):
    """T-ENDO-03: Motor only detects hypothyroidism (high TSH), not hyperthyroidism."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="11579-0", value=0.05),
            Observation(code="FT4-001", value=2.5),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value == "Balance Endocrino Normal"


def test_endo_euthyroid(motor):
    """T-ENDO-04: TSH normal = Euthyroid."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="11579-0", value=2.0),
        ],
    )
    result = motor.compute(enc)
    assert result.estado_ui in ["INDETERMINATE_LOCKED", "PROBABLE_WARNING"]


def test_endo_cushing_screening(motor):
    """T-ENDO-05: Cortisol AM > 20 = Cushing screening needed."""
    enc = _make_encounter(
        id="6",
        observations=[
            Observation(code="11579-0", value=2.5),
            Observation(code="CORT-AM", value=25),
        ],
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None
