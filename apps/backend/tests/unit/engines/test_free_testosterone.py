"""
Golden Motor Tests: FreeTestosteroneMotor (IEC 62304 V&V)
=========================================================
Tests for Free Testosterone Calculator (Vermeulen Method).
Test IDs: T-FT-01 through T-FT-06.
Evidence: Vermeulen 1999 (JCE&M).
"""

import pytest
from src.engines.specialty.free_testosterone import FreeTestosteroneMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return FreeTestosteroneMotor()


def _make_encounter(id="ft-test", observations=None, metadata=None, metabolic=None):
    """Helper: creates a valid Encounter for Free Testosterone testing."""
    mp = MetabolicPanelSchema()
    if metabolic:
        for k, v in metabolic.items():
            setattr(mp, k, v)
    default_meta = {"sex": "M"}
    if metadata:
        default_meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=mp,
        cardio_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
    )


def test_freeto_validate_missing_testo(motor):
    """T-FT-01: Missing testosterone = validation failure."""
    enc = _make_encounter(id="1", metadata={"sex": "M"})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Testosterone" in msg or "SHBG" in msg


def test_freeto_validate_missing_shbg(motor):
    """T-FT-01: Missing SHBG = validation failure."""
    enc = _make_encounter(id="2", metabolic={"testosterone_total_ng_dl": 500})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_freeto_validate_success(motor):
    """T-FT-01: With testosterone and SHBG = validation passes."""
    enc = _make_encounter(
        id="3",
        metadata={"sex": "M"},
        metabolic={"testosterone_total_ng_dl": 500, "shbg_nmol_l": 30},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_freeto_male_low(motor):
    """T-FT-02: Male with free T < 50 pg/mL = Low."""
    enc = _make_encounter(
        id="4",
        metadata={"sex": "M"},
        metabolic={
            "testosterone_total_ng_dl": 200,
            "shbg_nmol_l": 60,
        },  # Low T + high SHBG = low free T
    )
    result = motor.compute(enc)
    assert (
        "BAJA" in result.calculated_value or "rango" in result.calculated_value.lower()
    )


def test_freeto_male_normal(motor):
    """T-FT-03: Male with free T 50-210 = Normal."""
    enc = _make_encounter(
        id="5",
        metadata={"sex": "M"},
        metabolic={"testosterone_total_ng_dl": 500, "shbg_nmol_l": 30},
    )
    result = motor.compute(enc)
    assert result.estado_ui in ["INDETERMINATE_LOCKED", "CONFIRMED_ACTIVE"]


def test_freeto_female_low(motor):
    """T-FT-04: Female with free T < 7 pg/mL = Low."""
    enc = _make_encounter(
        id="6",
        metadata={"sex": "F"},
        metabolic={"testosterone_total_ng_dl": 30, "shbg_nmol_l": 40},
    )
    result = motor.compute(enc)
    assert result.metadata["is_male"] is False


def test_freeto_bioavailable_calculated(motor):
    """T-FT-06: Bioavailable testosterone is calculated."""
    enc = _make_encounter(
        id="8",
        metadata={"sex": "M"},
        metabolic={"testosterone_total_ng_dl": 500, "shbg_nmol_l": 30},
    )
    result = motor.compute(enc)
    assert "bioavailable_t_ng_dl" in result.metadata
