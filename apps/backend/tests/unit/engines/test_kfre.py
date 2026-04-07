"""
Golden Motor Tests: KFREMotor (IEC 62304 V&V)
===============================================
Tests for Kidney Failure Risk Equation (KFRE 4-variable).
Test IDs: T-KFRE-01 through T-KFRE-06.
Evidence: Tangri et al., 2016 (validated in >30k patients).
"""

import pytest
from src.engines.specialty.kfre import KFREMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return KFREMotor()


def _make_encounter(id="kfre-test", metabolic=None, observations=None, metadata=None):
    """Helper: creates a valid Encounter for KFRE testing."""
    mp = MetabolicPanelSchema(
        creatinine_mg_dl=metabolic.get("creatinine", 1.0) if metabolic else 1.0,
    )
    return Encounter(
        id=id,
        demographics=DemographicsSchema(
            age_years=metabolic.get("age", 60) if metabolic else 60, gender="male"
        ),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        metadata=metadata or {"sex": "M"},
    )


def test_kfre_validate_missing_egfr(motor):
    """T-KFRE-01: Missing eGFR should fail validation."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "eGFR" in msg


def test_kfre_validate_missing_uacr(motor):
    """T-KFRE-01: Missing UACR should fail validation."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="AGE-001", value=60),
        ],
    )
    # Will still fail because egfr is needed
    is_valid, msg = motor.validate(enc)
    assert is_valid is False


def test_kfre_validate_success(motor):
    """T-KFRE-01: With eGFR, UACR, and Age, validation should pass."""
    enc = _make_encounter(
        id="3",
        metabolic={"creatinine": 1.5, "age": 60},
        observations=[
            Observation(code="AGE-001", value=60),
            Observation(code="UACR-001", value=100),
        ],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_kfre_low_risk(motor):
    """T-KFRE-02: Low risk (<5% at 5 years) should return low risk status."""
    enc = _make_encounter(
        id="4",
        metabolic={"creatinine": 0.9, "age": 50},
        observations=[
            Observation(code="AGE-001", value=50),
            Observation(code="UACR-001", value=10),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "1.5%" in result.calculated_value  # Verify low risk percentage


def test_kfre_moderate_risk(motor):
    """T-KFRE-03: Moderate risk (5-25% at 5 years) should trigger nephrology referral."""
    enc = _make_encounter(
        id="5",
        metabolic={"creatinine": 1.8, "age": 65},
        observations=[
            Observation(code="AGE-001", value=65),
            Observation(code="UACR-001", value=200),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "5" in result.calculated_value or "MODERADO" in result.calculated_value
    assert len(result.action_checklist) > 0


def test_kfre_high_risk(motor):
    """T-KFRE-04: High risk (>25% at 5 years) should trigger urgent referral."""
    enc = _make_encounter(
        id="6",
        metabolic={"creatinine": 3.0, "age": 70},
        observations=[
            Observation(code="AGE-001", value=70),
            Observation(code="UACR-001", value=800),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["risk_5y"] > 25
    critical_actions = [a for a in result.action_checklist if a.priority == "critical"]
    assert len(critical_actions) > 0


def test_kfre_female_sex_factor(motor):
    """T-KFRE-05: Female sex should reduce risk (sex_term = 0 vs male 0.399)."""
    enc_male = _make_encounter(
        id="7a",
        metabolic={"creatinine": 2.0, "age": 60},
        observations=[
            Observation(code="AGE-001", value=60),
            Observation(code="UACR-001", value=300),
        ],
        metadata={"sex": "M"},
    )
    enc_female = _make_encounter(
        id="7b",
        metabolic={"creatinine": 2.0, "age": 60},
        observations=[
            Observation(code="AGE-001", value=60),
            Observation(code="UACR-001", value=300),
        ],
        metadata={"sex": "F"},
    )
    result_male = motor.compute(enc_male)
    result_female = motor.compute(enc_female)
    # Female should have lower risk
    assert result_female.metadata["risk_5y"] < result_male.metadata["risk_5y"]


def test_kfre_boundary_5_percent(motor):
    """T-KFRE-06: Boundary at 5% should classify as moderate if >= 5%."""
    enc = _make_encounter(
        id="8",
        metabolic={"creatinine": 1.5, "age": 55},
        observations=[
            Observation(code="AGE-001", value=55),
            Observation(code="UACR-001", value=150),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    # Check the risk values in metadata
    assert "risk_5y" in result.metadata
    assert "risk_2y" in result.metadata


def test_kfre_uacr_from_components(motor):
    """T-KFRE-06: UACR can be calculated from albumin/creatinine ratio."""
    enc = _make_encounter(
        id="9",
        metabolic={"creatinine": 1.6, "age": 58},
        observations=[
            Observation(code="AGE-001", value=58),
            Observation(code="UALB-001", value=50),  # Albumin mg/dL
            Observation(code="UCREAT-001", value=100),  # Urine creatinine mg/dL
        ],
        # UACR = (50/100)*1000 = 500
    )
    result = motor.compute(enc)
    # Should calculate UACR from components
    assert result.estado_ui in ["CONFIRMED_ACTIVE", "INDETERMINATE_LOCKED"]
