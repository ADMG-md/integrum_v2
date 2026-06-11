import pytest
from datetime import datetime, timedelta
from src.engines.c_state import CStateMachineMotor
from src.domain.models import Encounter, LongitudinalEncounterEntry, DemographicsSchema, MetabolicPanelSchema
import uuid

def create_mock_encounter(history: list[LongitudinalEncounterEntry]) -> Encounter:
    return Encounter(
        id=str(uuid.uuid4()),
        demographics=DemographicsSchema(age_years=40, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        longitudinal_encounters=history
    )

def create_entry(days_ago: int, weight: float, ffm: float = None) -> LongitudinalEncounterEntry:
    return LongitudinalEncounterEntry(
        encounter_id=str(uuid.uuid4()),
        encounter_date=datetime.now() - timedelta(days=days_ago),
        weight_kg=weight,
        ffm_kg=ffm
    )

def test_indeterminate_single_encounter():
    motor = CStateMachineMotor()
    enc = create_mock_encounter([
        create_entry(0, 100.0)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "indeterminate"
    assert result.dato_faltante == "Se requiere al menos un encounter previo"

def test_c1_responder():
    motor = CStateMachineMotor()
    # Baseline 100kg 28 days ago (4 weeks). Current 95.2kg (loss of 4.8kg / 4 = 1.2kg/wk)
    enc = create_mock_encounter([
        create_entry(28, 100.0),
        create_entry(0, 95.2)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C1"
    assert "Respondedor" in result.metadata["label"]
    assert result.metadata["audit_payload"]["weekly_rate_kg"] == 1.2

def test_c2_suboptimal():
    motor = CStateMachineMotor()
    # Baseline 100kg 28 days ago (4 weeks). Current 98.8kg (loss of 1.2kg / 4 = 0.3kg/wk)
    enc = create_mock_encounter([
        create_entry(28, 100.0),
        create_entry(0, 98.8)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C2"
    assert "Respuesta subóptima" in result.metadata["label"]
    assert result.metadata["audit_payload"]["weekly_rate_kg"] == 0.3

def test_c3_weight_gain():
    motor = CStateMachineMotor()
    # Baseline 100kg 28 days ago. Current 102kg (gain)
    enc = create_mock_encounter([
        create_entry(28, 100.0),
        create_entry(0, 102.0)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C3"
    assert "No respondedor" in result.metadata["label"]

def test_c4_abandonment():
    motor = CStateMachineMotor()
    # 70 days since last encounter
    enc = create_mock_encounter([
        create_entry(70, 100.0),
        create_entry(0, 95.0)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C4"
    assert "posible abandono" in result.metadata["label"]
    assert result.metadata["audit_payload"]["days_since_last_encounter"] == 70

def test_c_reentry():
    motor = CStateMachineMotor()
    # 3 encounters. E1 at 100 days. E2 at 20 days (gap 80 days -> C4). E3 at 0 days.
    enc = create_mock_encounter([
        create_entry(100, 100.0),
        create_entry(20, 98.0),
        create_entry(0, 97.0)
    ])
    result = motor.evaluate(enc)
    # The gap between E1 and E2 was 80 days. So the current encounter (E3) is reentry.
    assert result.calculated_value == "C_reentry"
    assert "Reingreso" in result.metadata["label"]

def test_sarcopenic_risk():
    motor = CStateMachineMotor()
    # Baseline 100kg, FFM 60kg. 28 days ago.
    # Current 90kg (loss 10kg), FFM 56kg (loss 4kg). 4/10 = 0.4 > 0.25 -> Risk!
    enc = create_mock_encounter([
        create_entry(28, 100.0, ffm=60.0),
        create_entry(0, 90.0, ffm=56.0)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C1" # Great weight loss rate
    assert "Riesgo sarcopénico" in result.metadata["label"]
    assert result.metadata["audit_payload"]["sarcopenic_flag"] is True

def test_missing_weight_returns_indeterminate():
    motor = CStateMachineMotor()
    enc = create_mock_encounter([
        create_entry(28, 100.0),
        create_entry(0, None)
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "indeterminate"
    assert "Falta peso" in result.dato_faltante

def test_partial_completeness_without_ffm():
    motor = CStateMachineMotor()
    enc = create_mock_encounter([
        create_entry(28, 100.0, ffm=60.0),
        create_entry(0, 95.0, ffm=None) # missing FFM
    ])
    result = motor.evaluate(enc)
    assert result.calculated_value == "C1"
    assert result.metadata["completeness"] == "partial"
    assert result.metadata["audit_payload"]["sarcopenic_flag"] is False
