"""
Golden Motor Tests: EOSSStagingMotor (IEC 62304 V&V)
=====================================================
Tests for the Edmonton Obesity Staging System.
Test IDs: T-EOS-01 through T-EOS-04 (Traceability Matrix).
"""
import pytest
from src.engines.eoss import EOSSStagingMotor
from src.engines.domain import Encounter, Condition, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return EOSSStagingMotor()

def _make_encounter(id="eoss-test", conditions=None, observations=None):
    """Helper: creates a valid Encounter with required schemas."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        conditions=conditions or [],
        observations=observations or [],
        metadata={},
    )

def test_eoss_validate_requires_e66(motor):
    # Covers SR-EOS-01
    enc = _make_encounter(id="1")
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "No obesity evidence" in msg

def test_eoss_stage_0(motor):
    # E66 alone -> Stage 0
    enc = _make_encounter(id="2", conditions=[Condition(code="E66", title="Obesity")])
    result = motor.compute(enc)
    assert "EOSS Stage 0" in result.calculated_value
    assert result.confidence == 0.95

def test_eoss_stage_1_prediabetes(motor):
    enc = _make_encounter(id="3", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="R73.0", title="Prediabetes"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 1" in result.calculated_value

def test_eoss_stage_2_dm2(motor):
    # Covers SR-EOS-02
    enc = _make_encounter(id="4", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="E11", title="Diabetes Type 2"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 2" in result.calculated_value

def test_eoss_stage_2_htn(motor):
    # Covers SR-EOS-02
    enc = _make_encounter(id="5", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="I10", title="Hypertension"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 2" in result.calculated_value

def test_eoss_stage_3_mi(motor):
    # Covers SR-EOS-03
    enc = _make_encounter(id="6", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="I21", title="Myocardial Infarction"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 3" in result.calculated_value

def test_eoss_stage_4_terminal(motor):
    # Covers SR-EOS-04
    enc = _make_encounter(id="7", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="I63.9", title="Stroke (Cerebral Infarction) with disability"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 4" in result.calculated_value

def test_eoss_highest_stage_priority(motor):
    enc = _make_encounter(id="8", conditions=[
        Condition(code="E66", title="Obesity"),
        Condition(code="E11", title="Diabetes T2"),
        Condition(code="I21", title="Myocardial Infarction"),
    ])
    result = motor.compute(enc)
    assert "EOSS Stage 3" in result.calculated_value

def test_eoss_no_obesity_condition(motor):
    enc = _make_encounter(id="9", conditions=[Condition(code="I10", title="Hypertension")])
    result = motor.compute(enc)
    assert "EOSS Stage" in result.calculated_value

# R-04 Tests: Biometric Trigger (BMI >= 30 without E66)
def test_eoss_triggers_with_bmi_without_e66(motor):
    """R-04: Patient with BMI >= 30 but no E66 code should trigger EOSS."""
    enc = _make_encounter(id="r04-bmi", observations=[
        Observation(code="29463-7", value="100"),  # Weight 100kg
        Observation(code="8302-2", value="170"),    # Height 170cm → BMI ~34.6
    ])
    is_valid, msg = motor.validate(enc)
    assert is_valid is True
