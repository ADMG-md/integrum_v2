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

def test_acosta_quema_lenta_no_bia_bmr(motor):
    # Sin BIA-BMR, pero con SMI bajo -> conf 0.60
    enc = _make_encounter(observations=[
        Observation(code="W-001", value="100"),
        Observation(code="H-001", value="170"),
        Observation(code="BIA-MUSCLE-KG", value="15"), # SMI = 15 / (1.7^2) = 5.19 (<7.0 male)
    ])
    result = motor.compute(enc)
    assert "Quema Lenta" in result.calculated_value
    assert result.metadata["phenotype_scores"]["quema_lenta"] == 0.60

def test_acosta_quema_lenta_no_bia_missing_flag(motor):
    # Sin BIA-BMR y SMI normal -> conf 0.0 y dato_faltante
    enc = _make_encounter(observations=[
        Observation(code="W-001", value="100"),
        Observation(code="H-001", value="170"),
        Observation(code="BIA-MUSCLE-KG", value="30"), # SMI = 10.3 (>7.0)
    ])
    result = motor.compute(enc)
    assert "Quema Lenta" not in result.calculated_value
    assert result.metadata["phenotype_scores"]["quema_lenta"] == 0.0
    assert "BIA-BMR requerido" in result.dato_faltante

def test_acosta_quema_lenta_ratio_0_85(motor):
    # Ratio < 0.85 Mifflin y < 0.90 Cunningham
    enc = _make_encounter(observations=[
        Observation(code="W-001", value="100"),
        Observation(code="H-001", value="170"),
        Observation(code="BIA-FFM-KG", value="60"),
        # Mifflin male (10*100) + (6.25*170) - (5*45) + 5 = 1000 + 1062.5 - 225 + 5 = 1842.5
        # Cunningham 500 + (22*60) = 1820
        # For 0.85: Mifflin < 0.85 -> < 1566
        # For 0.90: Cunningham < 0.90 -> < 1638
        # We set BMR to 1400 (which is < 1566 and < 1638)
        Observation(code="BIA-BMR", value="1400"),
    ])
    result = motor.compute(enc)
    assert "Quema Lenta" in result.calculated_value
    assert result.metadata["phenotype_scores"]["quema_lenta"] == 0.85

def test_acosta_quema_lenta_ratio_0_72(motor):
    # Solo un ratio cumple
    enc = _make_encounter(observations=[
        Observation(code="W-001", value="100"),
        Observation(code="H-001", value="170"),
        Observation(code="BIA-FFM-KG", value="60"),
        # Mifflin = 1842.5. 85% = 1566.
        # Cunningham = 1820. 90% = 1638.
        # BMR = 1600. ratio_mifflin = 1600/1842.5 = 0.86 (>0.85).
        # ratio_cunningham = 1600/1820 = 0.879 (<0.90).
        # So one fulfills, the other does not -> 0.72
        Observation(code="BIA-BMR", value="1600"),
    ])
    result = motor.compute(enc)
    assert "Quema Lenta" in result.calculated_value
    assert result.metadata["phenotype_scores"]["quema_lenta"] == 0.72
