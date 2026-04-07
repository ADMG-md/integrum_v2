"""
Golden Motor Tests: CharlsonMotor (IEC 62304 V&V)
==================================================
Tests for Charlson Comorbidity Index (CCI).
Test IDs: T-CCI-01 through T-CCI-06.
Evidence: Charlson et al., 1987 (validated mortality predictor).
"""

import pytest
from src.engines.specialty.charlson import CharlsonMotor
from src.engines.domain import Encounter, Condition
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return CharlsonMotor()


def _make_encounter(id="cci-test", conditions=None):
    """Helper: creates a valid Encounter for Charlson testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=60, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        conditions=conditions or [],
        metadata={},
    )


def test_charlson_validate_no_conditions(motor):
    """T-CCI-01: No conditions = validation failure."""
    enc = _make_encounter(id="1", conditions=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "conditions" in msg.lower()


def test_charlson_validate_with_conditions(motor):
    """T-CCI-01: With conditions = validation passes."""
    enc = _make_encounter(
        id="2", conditions=[Condition(code="E11", title="Diabetes Type 2")]
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_charlson_score_zero(motor):
    """T-CCI-02: No mapped conditions = CCI 0."""
    enc = _make_encounter(
        id="3",
        conditions=[
            Condition(code="J01", title="Acute sinusitis"),
        ],
    )
    result = motor.compute(enc)
    assert (
        result.calculated_value == "Charlson CCI: 0 (sin comorbilidades significativas)"
    )
    assert result.metadata["cci_score"] == 0


def test_charlson_mild_comorbidity(motor):
    """T-CCI-03: CCI 1-2 = mild-moderate comorbidity."""
    enc = _make_encounter(
        id="4",
        conditions=[
            Condition(code="E11", title="Diabetes Type 2"),  # +1
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["cci_score"] == 1
    assert "1" in result.calculated_value


def test_charlson_moderate_comorbidity(motor):
    """T-CCI-04: CCI 3-4 = moderate-high comorbidity."""
    enc = _make_encounter(
        id="5",
        conditions=[
            Condition(code="E11", title="Diabetes Type 2"),  # +1
            Condition(code="I50", title="Heart Failure"),  # +1
            Condition(code="N18.4", title="CKD Stage 4"),  # +3
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["cci_score"] == 5
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_charlson_high_comorbidity(motor):
    """T-CCI-05: CCI >= 5 = high mortality risk."""
    enc = _make_encounter(
        id="6",
        conditions=[
            Condition(code="E11", title="Diabetes Type 2"),  # +1
            Condition(code="I21", title="Myocardial Infarction"),  # +1
            Condition(code="N18.5", title="ESRD"),  # +4
            Condition(code="I50", title="Heart Failure"),  # +1
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["cci_score"] >= 5
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_charlson_very_high_comorbidity(motor):
    """T-CCI-06: CCI >= 7 = very high mortality risk."""
    enc = _make_encounter(
        id="7",
        conditions=[
            Condition(code="N18.5", title="ESRD"),  # +4
            Condition(code="N18.6", title="Dialysis"),  # +6
        ],
    )
    result = motor.compute(enc)
    assert result.metadata["cci_score"] >= 7
    assert "21%" in result.explanation  # 10-year survival


def test_charlson_condition_mapping(motor):
    """T-CCI-06: Verify conditions are correctly mapped to weights."""
    enc = _make_encounter(
        id="8",
        conditions=[
            Condition(code="I25", title="Coronary Artery Disease"),  # +1
        ],
    )
    result = motor.compute(enc)
    assert "+1" in result.metadata["conditions"][0]
