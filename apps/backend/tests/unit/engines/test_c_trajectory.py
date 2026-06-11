import pytest
from src.engines.specialty.c_trajectory import CTrajectoryMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return CTrajectoryMotor()

def _make_encounter(observations=None, baseline_weight=None, baseline_ffm=None, days_elapsed=90):
    enc = Encounter(
        id="test-enc",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
    )
    if baseline_weight is not None:
        enc.metadata["baseline_weight_kg"] = baseline_weight
    if baseline_ffm is not None:
        enc.metadata["baseline_ffm_kg"] = baseline_ffm
    if days_elapsed is not None:
        enc.metadata["days_elapsed"] = days_elapsed
    return enc

def test_c_trajectory_missing_baseline(motor):
    enc = _make_encounter(
        observations=[Observation(code="W-001", value="90")],
        baseline_weight=None,
        days_elapsed=90
    )
    is_valid, reason = motor.validate(enc)
    assert not is_valid
    assert "baseline weight" in reason

def test_c_trajectory_missing_current(motor):
    enc = _make_encounter(
        observations=[],
        baseline_weight=100.0,
        days_elapsed=90
    )
    is_valid, reason = motor.validate(enc)
    assert not is_valid
    assert "current weight" in reason

def test_c_trajectory_missing_days(motor):
    enc = _make_encounter(
        observations=[Observation(code="W-001", value="90.0")],
        baseline_weight=100.0,
        days_elapsed=None
    )
    is_valid, reason = motor.validate(enc)
    assert not is_valid
    assert "days_elapsed" in reason

def test_c_trajectory_early_responder_safe(motor):
    # Baseline: 100 kg, FFM: 70 kg. Current: 92 kg, FFM: 69 kg. WL = 8% (>=5%). FFM loss = 1 kg (12.5% of 8 kg total loss, which is <25%).
    enc = _make_encounter(
        observations=[
            Observation(code="W-001", value="92.0"),
            Observation(code="BIA-FFM-KG", value="69.0")
        ],
        baseline_weight=100.0,
        baseline_ffm=70.0,
        days_elapsed=90
    )
    result = motor.compute(enc)
    assert result.calculated_value == "C1_RESPONDER_SAFE"
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["weight_loss_percent"] == 8.0
    assert result.metadata["ffm_loss_ratio"] == 0.125
    assert "Considerar" not in result.recomendacion_farmacologica[0]

def test_c_trajectory_non_responder(motor):
    # Baseline: 100 kg. Current: 97.5 kg (2.5% loss).
    enc = _make_encounter(
        observations=[Observation(code="W-001", value="97.5")],
        baseline_weight=100.0,
        days_elapsed=90
    )
    result = motor.compute(enc)
    assert result.calculated_value == "C2_NON_RESPONDER"
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.metadata["weight_loss_percent"] == 2.5
    assert "escalamiento" in result.recomendacion_farmacologica[0]

def test_c_trajectory_sarkopenic_risk(motor):
    # Baseline: 100 kg, FFM: 70 kg. Current: 92 kg, FFM: 67.5 kg. WL = 8% (>=5%). FFM loss = 2.5 kg (31.25% of 8 kg total loss, which is >=25%).
    enc = _make_encounter(
        observations=[
            Observation(code="W-001", value="92.0"),
            Observation(code="BIA-FFM-KG", value="67.5")
        ],
        baseline_weight=100.0,
        baseline_ffm=70.0,
        days_elapsed=90
    )
    result = motor.compute(enc)
    assert result.calculated_value == "C3_RESPONDER_SARKOPENIC_RISK"
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.metadata["weight_loss_percent"] == 8.0
    assert result.metadata["ffm_loss_ratio"] == 0.3125
    assert "aporte proteico" in result.recomendacion_farmacologica[0]

def test_c_trajectory_indeterminate_timeline(motor):
    enc = _make_encounter(
        observations=[Observation(code="W-001", value="90.0")],
        baseline_weight=100.0,
        days_elapsed=15  # Out of window (76-104 days)
    )
    result = motor.compute(enc)
    assert result.calculated_value == "C_INDETERMINATE"
    assert result.estado_ui == "INDETERMINATE_LOCKED"
