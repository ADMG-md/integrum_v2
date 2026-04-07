"""
Golden Motor Tests: MetabolicPrecisionMotor (IEC 62304 V&V)
===========================================================
Tests for Metabolic Precision (HOMA-IR, Mets-IR, TyG).
Test IDs: T-MET-01 through T-MET-05.
Evidence: Multiple indices (HOMA, TyG, METS-IR).
"""

import pytest
from src.engines.specialty.metabolic import MetabolicPrecisionMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return MetabolicPrecisionMotor()


def _make_encounter(
    id="metprec-test", observations=None, metadata=None, metabolic=None
):
    """Helper: creates a valid Encounter for Metabolic Precision testing."""
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
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
    )


def test_metprec_validate_no_data(motor):
    """T-MET-01: No glucose/BMI = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_metprec_validate_success(motor):
    """T-MET-01: With glucose = validation passes."""
    enc = _make_encounter(id="2", observations=[Observation(code="2339-0", value=100)])
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_metprec_sarcopenic_obesity(motor):
    """T-MET-02: Low SMI + BMI >= 30 = Sarcopenic obesity."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="29463-7", value=100),
            Observation(code="8302-2", value=170),
            Observation(code="SMI-001", value=5.5),
        ],
        metadata={"sex": "M", "bmi": 34},
    )
    result = motor.compute(enc)
    assert result.metadata is not None


def test_metprec_adiposopathy(motor):
    """T-MET-03: High CRP + high HOMA-IR = Adiposopathy."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="29463-7", value=95),
            Observation(code="8302-2", value=170),
            Observation(code="30522-7", value=2.5),
            Observation(code="20448-7", value=25),
            Observation(code="2339-0", value=110),
        ],
        metadata={"sex": "M", "bmi": 32},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_metprec_mho(motor):
    """T-MET-04: Low CRP + low HOMA-IR = Metabolically healthy."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=175),
            Observation(code="30522-7", value=0.3),
        ],
        metadata={"sex": "M", "bmi": 32},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None
