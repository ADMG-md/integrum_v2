"""
Golden Motor Tests: FriedFrailtyMotor (IEC 62304 V&V)
=======================================================
Tests for Fried Frailty Phenotype.
Test IDs: T-FRIED-01 through T-FRIED-06.
Evidence: Fried et al., 2001 (Cardiovascular Health Study).
"""

import pytest
from src.engines.specialty.fried_frailty import FriedFrailtyMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return FriedFrailtyMotor()


def _make_encounter(id="fried-test", observations=None, metadata=None):
    """Helper: creates a valid Encounter for Fried Frailty testing."""
    default_meta = {"sex": "M"}
    if metadata:
        default_meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=70, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
    )


def test_fried_validate_no_data(motor):
    """T-FRIED-01: No frailty data = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Fried" in msg or "grip" in msg or "gait" in msg


def test_fried_validate_with_data(motor):
    """T-FRIED-01: With some frailty data = validation passes."""
    enc = _make_encounter(
        id="2",
        observations=[Observation(code="29463-7", value=70)],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_fried_robust(motor):
    """T-FRIED-02: 0 criteria = Robust."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="29463-7", value=75),
            Observation(code="GRIP-STR-R", value=35),  # Good grip strength
            Observation(code="GAIT-SPEED", value=1.0),  # Fast gait
            Observation(code="PA-MIN-WEEK", value=200),  # Adequate activity
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["category"] == "robust"
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_fried_pre_frail(motor):
    """T-FRIED-03: 1-2 criteria = Pre-frail."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="29463-7", value=70),
            Observation(code="GRIP-STR-R", value=20),  # Low grip (<27 for male)
            Observation(code="PA-MIN-WEEK", value=100),  # Low activity
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["category"] == "pre-frail"
    assert result.estado_ui == "PROBABLE_WARNING"


def test_fried_frail(motor):
    """T-FRIED-04: >=3 criteria = Frail."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(
                code="29463-7", value=65
            ),  # Weight loss will be detected with metadata
            Observation(code="GRIP-STR-R", value=15),  # Very low grip
            Observation(code="GAIT-SPEED", value=0.6),  # Slow gait
            Observation(code="PA-MIN-WEEK", value=50),  # Very low activity
        ],
        metadata={
            "sex": "M",
            "prev_weight_kg": 75,  # 10% weight loss
        },
    )
    result = motor.compute(enc)
    assert result.metadata["category"] == "frail"
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["fried_score"] >= 3


def test_fried_weight_loss_criterion(motor):
    """T-FRIED-05: >=5% weight loss counts as criterion."""
    enc = _make_encounter(
        id="6",
        observations=[
            Observation(code="29463-7", value=66),
        ],
        metadata={
            "sex": "M",
            "prev_weight_kg": 70,  # Lost 4/70 = 5.7%
        },
    )
    result = motor.compute(enc)
    assert "5" in result.explanation or "perdida" in result.explanation.lower()


def test_fried_grip_threshold_male(motor):
    """T-FRIED-06: Male grip threshold is 27kg."""
    enc = _make_encounter(
        id="7",
        observations=[
            Observation(code="GRIP-STR-R", value=26),  # Just below threshold
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["fried_score"] >= 1


def test_fried_grip_threshold_female(motor):
    """T-FRIED-06: Female grip threshold is 16kg."""
    enc = _make_encounter(
        id="8",
        observations=[
            Observation(code="GRIP-STR-R", value=17),  # Above threshold for female
        ],
        metadata={"sex": "F"},
    )
    result = motor.compute(enc)
    assert result.metadata["fried_score"] == 0


def test_fried_sts_alternative(motor):
    """T-FRIED-05: 5xSTS > 15s can substitute for gait speed."""
    enc = _make_encounter(
        id="9",
        observations=[
            Observation(code="5XSTS-SEC", value=18),  # Slow STS
        ],
        metadata={"sex": "F"},
    )
    result = motor.compute(enc)
    assert result.metadata["fried_score"] >= 1
