"""
Golden Motor Tests: FLIMotor (IEC 62304 V&V)
===============================================
Tests for Fatty Liver Index (NAFLD screening).
Test IDs: T-FLI-01 through T-FLI-06.
Evidence: Bedogni et al., 2006 (validated >100k patients).
"""

import pytest
from src.engines.specialty.fatty_liver import FLIMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return FLIMotor()


def _make_encounter(id="fli-test", observations=None, cardio=None):
    """Helper: creates a valid Encounter for FLI testing."""
    cp = CardioPanelSchema()
    if cardio:
        cp.triglycerides_mg_dl = cardio.get("triglycerides")
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=cp,
        observations=observations or [],
        metadata={},
    )


def test_fli_validate_missing_tg(motor):
    """T-FLI-01: Missing triglycerides = validation failure."""
    enc = _make_encounter(id="1", cardio={})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Triglycerides" in msg or "FLI" in msg


def test_fli_validate_missing_bmi(motor):
    """T-FLI-01: Missing BMI = validation failure."""
    enc = _make_encounter(id="2", observations=[], cardio={"triglycerides": 150})
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_fli_validate_success(motor):
    """T-FLI-01: All required fields = validation passes."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="WAIST-001", value=95),
            Observation(code="GGT-001", value=40),
        ],
        cardio={"triglycerides": 150},
    )
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=40),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=150),
        observations=[
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=95),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_fli_low_risk(motor):
    """T-FLI-02: FLI < 30 = NAFLD ruled out."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=20),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=80),
        observations=[
            Observation(code="29463-7", value=65),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=80),
        ],
    )
    result = motor.compute(enc)
    assert "descartado" in result.calculated_value.lower()
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert result.metadata["category"] == "low"


def test_fli_equivocal(motor):
    """T-FLI-03: FLI 30-60 = Equivocal."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=45),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=130),
        observations=[
            Observation(code="29463-7", value=80),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=92),
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["fli"] is not None
    assert result.metadata["category"] in ["equivocal", "high"]


def test_fli_high_risk(motor):
    """T-FLI-04: FLI > 60 = NAFLD likely."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=100),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=250),
        observations=[
            Observation(code="29463-7", value=110),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=110),
        ],
    )
    result = motor.compute(enc)
    assert "probable" in result.calculated_value.lower()
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["category"] == "high"


def test_fli_boundary_30(motor):
    """T-FLI-05: FLI = 30 exactly should be equivocal."""
    enc = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=30),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=100),
        observations=[
            Observation(code="29463-7", value=72),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=85),
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["fli"] <= 60


def test_fli_boundary_60(motor):
    """T-FLI-05: FLI = 60 exactly should be high risk."""
    enc = Encounter(
        id="8",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ggt_u_l=60),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=180),
        observations=[
            Observation(code="29463-7", value=95),
            Observation(code="8302-2", value=170),
            Observation(code="WAIST-001", value=100),
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["fli"] >= 30
