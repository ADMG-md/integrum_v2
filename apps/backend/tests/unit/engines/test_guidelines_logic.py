"""
Clinical Decision Support Tests: ClinicalGuidelinesMotor (Layer 6 Action Engine)
================================================================================
Verification of Guideline Compliance and Action Item Generation.
Test IDs: T-GUI-01 through T-GUI-03 (Traceability Matrix).
"""
import pytest
from src.engines.specialty.guidelines import ClinicalGuidelinesMotor
from src.engines.domain import Encounter, Observation, MedicationStatement
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return ClinicalGuidelinesMotor()

def _make_encounter(medications=None, observations=None, ldl=None, glucose=None, insulin=None):
    """Helper: creates a valid Encounter for guideline auditing."""
    mp = MetabolicPanelSchema(
        glucose_mg_dl=glucose,
        insulin_mu_u_ml=insulin,
        ldl_mg_dl=ldl
    )
    return Encounter(
        id="test-enc",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=mp,
        medications=medications or [],
        observations=observations or [],
        metadata={"age": 55, "sex": "male"}
    )

def test_guidelines_htn_omission_sr_gui_01(motor):
    """T-GUI-01: Detects HTN Stage 2 omission when BP >= 140/90 and no meds."""
    # SBP 150, DBP 95
    obs = [
        Observation(code="8480-6", value=150, unit="mmHg"),
        Observation(code="8462-4", value=95, unit="mmHg")
    ]
    enc = _make_encounter(observations=obs)
    
    result = motor.compute(enc)
    
    assert "Hipertensión Estadio 2" in result.calculated_value
    # Check for ActionItem
    assert any(a.task == "Iniciar terapia antihipertensiva dual" for a in result.action_checklist)
    # Check for MedicationGap
    assert any(g.gap_type == "OMISSION" and "Antihipertensivos" in g.drug_class for g in result.critical_omissions)

def test_guidelines_htn_controlled(motor):
    """Verifies that it doesn't trigger omission if patient is on meds."""
    obs = [
        Observation(code="8480-6", value=150, unit="mmHg"),
        Observation(code="8462-4", value=95, unit="mmHg")
    ]
    meds = [MedicationStatement(code="ACEI", name="Enalapril", is_active=True)]
    enc = _make_encounter(observations=obs, medications=meds)
    
    result = motor.compute(enc)
    
    assert "Hipertensión No Controlada" in result.calculated_value
    assert any("Intensificar terapia" in a.task for a in result.action_checklist)
    # Should not be an OMISSION gap
    assert not any(g.gap_type == "OMISSION" and "Antihipertensivos" in g.drug_class for g in result.critical_omissions)

def test_guidelines_lipidic_omission_sr_gui_02(motor):
    """T-GUI-02: Detects Lipidic Inertia/Omission based on risk-category goal."""
    # Context: very_high risk (Goal < 55)
    # LDL: 100 
    enc = _make_encounter(ldl=100)
    context = {"cvd_risk_category": "very_high"}
    
    result = motor.compute(enc, context)
    
    assert "Inercia Clínica en Lípidos" in result.calculated_value
    assert any("Iniciar estatinas" in a.task for a in result.action_checklist)
    assert any(g.gap_type == "OMISSION" and "Estatinas" in g.drug_class for g in result.critical_omissions)

def test_guidelines_homa_b_preservation_sr_gui_03(motor):
    """T-GUI-03: Suggests GLP-1 for beta-cell preservation if HOMA-B < 50%."""
    # HOMA-B = (360 * insulin) / (glucose - 63)
    # glucose=100, insulin=5 -> HOMA-B = (1800)/(37) = 48.6%
    enc = _make_encounter(glucose=100, insulin=5)
    
    result = motor.compute(enc)
    
    assert "Reserva Pancreática Comprometida" in result.calculated_value
    assert any("Priorizar análogos GLP-1" in a.task for a in result.action_checklist)
    assert any(g.drug_class == "Análogos GLP-1" and g.gap_type == "OMISSION" for g in result.critical_omissions)

def test_guidelines_safe_data_partial(motor):
    """Checks resilience with minimal data."""
    # Only SBP, no DBP or Lipids
    obs = [Observation(code="8480-6", value=120)]
    enc = _make_encounter(observations=obs)
    
    # Needs both SBP and DBP for HTN audit in current logic
    result = motor.compute(enc)
    assert result.action_checklist == []
    assert result.critical_omissions == []
