"""
Golden Motor Tests: AcostaPhenotypeMotor (IEC 62304 V&V)
=========================================================
Tests for the Acosta Phenotype Classifier.
Test IDs: T-ACO-01 through T-ACO-04 (Traceability Matrix).
"""
import pytest
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return AcostaPhenotypeMotor()

def _make_encounter(id="test-enc", sex="M", observations=None, metadata=None):
    """Helper: creates a valid Encounter with required schemas."""
    gender_map = {"M": "male", "F": "female"}
    gender = gender_map.get(sex, "male")
    meta = {"bmi": 35.0, "sex": sex}
    if metadata:
        meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=45, gender=gender),
        metabolic_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=meta,
    )

def test_acosta_validate_missing_bmi(motor):
    enc = _make_encounter(id="1", metadata={"bmi": None})
    # BMI property is computed from observations, not metadata
    # Remove any weight/height observations so bmi property returns None
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "Missing BMI" in msg

def test_acosta_threshold_male_boundary(motor):
    # Covers SR-ACO-01
    # Threshold for Male: 1376
    enc = _make_encounter(observations=[Observation(code="BUFFET-KCAL", value="1376")])
    result = motor.compute(enc)
    assert "Cerebro Hambriento" not in result.calculated_value
    
    # Just above threshold -> trigger
    enc = _make_encounter(observations=[Observation(code="BUFFET-KCAL", value="1377")])
    result = motor.compute(enc)
    assert "Cerebro Hambriento" in result.calculated_value

def test_acosta_threshold_female_boundary(motor):
    # Covers SR-ACO-01
    enc = _make_encounter(id="2", sex="F", observations=[Observation(code="BUFFET-KCAL", value="894")])
    result = motor.compute(enc)
    assert "Cerebro Hambriento" not in result.calculated_value
    
    enc = _make_encounter(id="2", sex="F", observations=[Observation(code="BUFFET-KCAL", value="895")])
    result = motor.compute(enc)
    assert "Cerebro Hambriento" in result.calculated_value

def test_acosta_emotional_hunger_anxiety_boundary(motor):
    # Covers SR-ACO-02
    enc = _make_encounter(observations=[Observation(code="GAD-7", value="10")])
    result = motor.compute(enc)
    assert "Hambre Emocional" in result.calculated_value
    
    enc = _make_encounter(observations=[Observation(code="GAD-7", value="9")])
    result = motor.compute(enc)
    assert "Hambre Emocional" not in result.calculated_value

def test_acosta_emotional_hunger_with_psych(motor):
    # Covers SR-ACO-04
    enc = _make_encounter(
        observations=[Observation(code="GAD-7", value="12")],
        metadata={"external_psych_confirmation": True},
    )
    result = motor.compute(enc)
    assert "Hambre Emocional" in result.calculated_value
    assert result.confidence == 0.85

def test_acosta_gastric_emptying_boundary(motor):
    # Covers SR-ACO-03
    enc = _make_encounter(observations=[Observation(code="GE-T12", value="85")])
    result = motor.compute(enc)
    assert "Intestino Hambriento" not in result.calculated_value
    
    enc = _make_encounter(observations=[Observation(code="GE-T12", value="84")])
    result = motor.compute(enc)
    assert "Intestino Hambriento" in result.calculated_value

def test_acosta_early_satiety_trigger(motor):
    # Covers SR-ACO-03
    enc = _make_encounter(observations=[Observation(code="ST-001", value="1")])
    result = motor.compute(enc)
    assert "Intestino Hambriento" in result.calculated_value
    assert result.confidence == 0.60

def test_acosta_invalid_data_handling(motor):
    enc = _make_encounter(observations=[Observation(code="BUFFET-KCAL", value="INVALID")])
    result = motor.compute(enc)
    assert "Cerebro Hambriento" not in result.calculated_value
    assert result.confidence == 1.0
