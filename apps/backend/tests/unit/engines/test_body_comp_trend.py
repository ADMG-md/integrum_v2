"""
Golden Motor Tests: BodyCompositionTrendMotor (IEC 62304 V&V)
=============================================================
Tests for Body Composition Trend tracking during therapy.
"""

import pytest
from src.engines.specialty.body_comp_trend import BodyCompositionTrendMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema


@pytest.fixture
def motor():
    return BodyCompositionTrendMotor()


def test_body_comp_validate_missing(motor):
    """Validation fails without required metadata."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        metadata={"prev_weight_kg": 100.0},  # Missing prev_muscle_mass_kg
        observations=[
            Observation(code="29463-7", value=90.0),
            Observation(code="MMA-001", value=39.0),
        ],
    )
    valid, msg = motor.validate(enc)
    assert valid is False
    assert "prev_muscle_mass_kg" in msg


def test_body_comp_normal_values(motor):
    """Test physiological values: lean mass loss < 15%."""
    # Weight loss = 10kg, Muscle loss = 1kg -> 10% lean loss
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        metadata={
            "prev_weight_kg": 100.0,
            "prev_muscle_mass_kg": 40.0,
        },
        observations=[
            Observation(code="29463-7", value=90.0),
            Observation(code="MMA-001", value=39.0),
        ],
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert result.metadata["lean_loss_pct"] == 10.0


def test_body_comp_boundary_values(motor):
    """Test boundary values: lean mass loss between 15% and 25%."""
    # Weight loss = 10kg, Muscle loss = 2kg -> 20% lean loss
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        metadata={
            "prev_weight_kg": 100.0,
            "prev_muscle_mass_kg": 40.0,
        },
        observations=[
            Observation(code="29463-7", value=90.0),
            Observation(code="MMA-001", value=38.0),
        ],
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.metadata["lean_loss_pct"] == 20.0
    assert any("Aumentar ingesta proteica" in task.task for task in result.action_checklist)


def test_body_comp_pathological_values(motor):
    """Test pathological values: lean mass loss > 25%."""
    # Weight loss = 10kg, Muscle loss = 3kg -> 30% lean loss
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        metadata={
            "prev_weight_kg": 100.0,
            "prev_muscle_mass_kg": 40.0,
        },
        observations=[
            Observation(code="29463-7", value=90.0),
            Observation(code="MMA-001", value=37.0),
        ],
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["lean_loss_pct"] == 30.0
    assert any("Considerar reducción de dosis" in task.task for task in result.action_checklist)


def test_body_comp_no_weight_loss(motor):
    """Test when weight increases or stays the same."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        metadata={
            "prev_weight_kg": 100.0,
            "prev_muscle_mass_kg": 40.0,
        },
        observations=[
            Observation(code="29463-7", value=102.0),
            Observation(code="MMA-001", value=41.0),
        ],
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "Sin pérdida de peso" in result.calculated_value
