import pytest
from src.engines.domain import Encounter, ClinicalHistory, MetabolicPanelSchema, MetabolicPanelSchema, Observation, DemographicsSchema
from src.engines.specialty.pharmacogenomics import PharmacogenomicProxyMotor

@pytest.fixture
def base_encounter():
    demo = DemographicsSchema(age_years=45, gender="female", weight_kg=70.0, height_cm=165.0)
    return Encounter(
        id="PGX-001",
        demographics=demo,
        history=ClinicalHistory(),
        metabolic_panel=MetabolicPanelSchema()
    )

def test_mthfr_proxy(base_encounter):
    # Homocysteine > 15 and MCV > 95
    base_encounter.observations.append(Observation(code="HCY-001", value=16.0))
    base_encounter.observations.append(Observation(code="MCV-001", value=96.0))
    
    motor = PharmacogenomicProxyMotor()
    result = motor.compute(base_encounter)
    
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert any("MTHFR" in find for find in result.calculated_value.split(" | "))
    actions = [a.task for a in result.action_checklist]
    assert any("L-Metilfolato" in task for task in actions)

def test_slco1b1_proxy_statin_intolerance(base_encounter):
    base_encounter.history.has_statin_myalgia = True
    
    motor = PharmacogenomicProxyMotor()
    result = motor.compute(base_encounter)
    
    assert "Miopatía por estatinas" in result.calculated_value
    assert any("Estatinas Hidrofílicas" in a.task for a in result.action_checklist)

def test_cyp1a2_proxy_caffeine(base_encounter):
    base_encounter.history.caffeine_anxiety_insomnia = True
    
    motor = PharmacogenomicProxyMotor()
    result = motor.compute(base_encounter)
    
    assert "Cafeína" in result.calculated_value
    assert any("VETAR suplementos térmicos" in a.task for a in result.action_checklist)

def test_vdr_proxy_refractory_vitd(base_encounter):
    base_encounter.observations.append(Observation(code="VIT-D-25OH", value=20.0))
    base_encounter.history.taking_otc_vitd = True
    
    motor = PharmacogenomicProxyMotor()
    result = motor.compute(base_encounter)
    
    assert "Resistencia a Vitamina D" in result.calculated_value
    assert any("Vitamina D3 Micelizada" in a.task for a in result.action_checklist)

def test_no_proxies_found(base_encounter):
    motor = PharmacogenomicProxyMotor()
    result = motor.compute(base_encounter)
    
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "Ausencia" in result.calculated_value
    assert len(result.action_checklist) == 0
