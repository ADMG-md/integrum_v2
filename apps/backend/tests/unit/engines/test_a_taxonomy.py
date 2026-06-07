import pytest
from src.engines.domain import Encounter, Observation, DemographicsSchema, ClinicalHistory
from src.engines.base_models import AdjudicationResult
from src.engines.specialty.a_taxonomy import ATaxonomyMotor

def _build_encounter(tfeq_unc=None, tfeq_emo=None, gad7=None, phq9=None) -> Encounter:
    obs = []
    if tfeq_unc is not None:
        obs.append(Observation(code="TFEQ-UNCONTROLLED", value=tfeq_unc))
    if tfeq_emo is not None:
        obs.append(Observation(code="TFEQ-EMOTIONAL", value=tfeq_emo))
    if gad7 is not None:
        obs.append(Observation(code="GAD-7", value=gad7))
    if phq9 is not None:
        obs.append(Observation(code="PHQ9-SCORE", value=phq9))
        
    from src.engines.domain import MetabolicPanelSchema
    return Encounter(
        id="TEST",
        demographics=DemographicsSchema(age_years=40, gender="male"),
        observations=obs,
        history=ClinicalHistory(),
        metabolic_panel=MetabolicPanelSchema()
    )

def test_a4_anxiety_uncontrolled():
    # Paciente A4: TFEQ-UNCONTROLLED=3.0, GAD-7=12
    enc = _build_encounter(tfeq_unc=3.0, gad7=12)
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {})
    
    assert res.metadata["code"] == "A4"
    assert "A4" in res.calculated_value

def test_a2_depression_emotional():
    # Paciente A2: TFEQ-EMOTIONAL=3.2, PHQ-9=14
    enc = _build_encounter(tfeq_emo=3.2, phq9=14)
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {})
    
    assert res.metadata["code"] == "A2"
    assert "A2" in res.calculated_value
    assert res.confidence == 1.0

def test_a1_uncontrolled_isolated():
    # Paciente A1: TFEQ-UNCONTROLLED=2.8, GAD-7=4 (sin ansiedad)
    enc = _build_encounter(tfeq_unc=2.8, gad7=4)
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {})
    
    assert res.metadata["code"] == "A1"
    assert "A1" in res.calculated_value

def test_a1_acosta_dominant():
    enc = _build_encounter()
    acosta_res = AdjudicationResult(
        calculated_value="Cerebro Hambriento",
        confidence=0.8,
        estado_ui="CONFIRMED_ACTIVE",
        metadata={"phenotype_scores": {"cerebro_hambriento": 0.85, "intestino_hambriento": 0.4}}
    )
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {"AcostaPhenotypeMotor": acosta_res})
    
    assert res.metadata["code"] == "A1"
    assert "Acosta" in res.calculated_value

def test_a3_slow_burn():
    # Paciente A3: quema_lenta=0.80, sin TFEQ patológico
    enc = _build_encounter()
    acosta_res = AdjudicationResult(
        calculated_value="Quema Lenta",
        confidence=0.8,
        estado_ui="CONFIRMED_ACTIVE",
        metadata={"phenotype_scores": {"quema_lenta": 0.80}}
    )
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {"AcostaPhenotypeMotor": acosta_res})
    
    assert res.metadata["code"] == "A3"
    assert "A3" in res.calculated_value

def test_a0_acosta_indeterminate():
    # Paciente A0: Acosta indeterminate
    enc = _build_encounter()
    acosta_res = AdjudicationResult(
        calculated_value="Indeterminado",
        confidence=0.4,
        estado_ui="INDETERMINATE_LOCKED",
        metadata={"phenotype_scores": {}}
    )
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {"AcostaPhenotypeMotor": acosta_res})
    
    assert res.metadata["code"] == "A0"
    assert res.estado_ui == "INDETERMINATE_LOCKED"
    assert res.confidence == 0.0

def test_conflict_a2_a4():
    # Conflicto A2/A4: TFEQ-EMOTIONAL=3.0 Y GAD-7=11 → debe resolver A4 por prioridad
    # Wait, the prompt says TFEQ-EMOTIONAL=3.0 Y GAD-7=11 -> A4.
    # But A4 rule is: TFEQ-UNCONTROLLED > 2.5 Y GAD-7 >= 10.
    # If the patient has TFEQ-EMOTIONAL=3.0, TFEQ-UNCONTROLLED=3.0, and GAD-7=11, it goes to A4.
    # Let's ensure the user meant TFEQ-UNCONTROLLED is also high, or if A4 only requires GAD-7+UNC?
    # Prompt: "Reglas en orden de prioridad... A4 -> TFEQ-UNCONTROLLED > 2.5 Y GAD-7 >= 10. A2 -> TFEQ-EMO > 2.5 Y PHQ9 >= 10... Conflicto A2/A4: TFEQ-EMOTIONAL=3.0 Y GAD-7=11 -> debe resolver A4"
    # Actually if TFEQ-UNCONTROLLED is not >2.5, it wouldn't match A4. I will add TFEQ-UNC > 2.5 to the test to trigger the conflict properly.
    enc = _build_encounter(tfeq_unc=3.0, tfeq_emo=3.0, gad7=11, phq9=12)
    motor = ATaxonomyMotor()
    res = motor.compute(enc, {})
    
    assert res.metadata["code"] == "A4"
    assert "A4" in res.calculated_value
