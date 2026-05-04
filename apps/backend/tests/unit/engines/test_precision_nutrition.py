import pytest
from src.engines.domain import Encounter, ClinicalHistory, MetabolicPanelSchema, MetabolicPanelSchema, Observation, DemographicsSchema
from src.engines.specialty.precision_nutrition import PrecisionNutritionMotor

@pytest.fixture
def base_encounter():
    demo = DemographicsSchema(age_years=35, gender="male", weight_kg=80.0, height_cm=175.0)
    return Encounter(
        id="NUTRI-001",
        demographics=demo,
        history=ClinicalHistory(),
        metabolic_panel=MetabolicPanelSchema(),
        bmi=26.1
    )

def test_missing_bmi():
    demo = DemographicsSchema(age_years=35, gender="male") # no height/weight
    encounter_no_bmi = Encounter(
        id="NUTRI-002",
        demographics=demo,
        history=ClinicalHistory(),
        metabolic_panel=MetabolicPanelSchema()
    )
    motor = PrecisionNutritionMotor()
    valid, msg = motor.validate(encounter_no_bmi)
    assert not valid
    assert "Missing BMI" in msg

def test_apoe4_proxy(base_encounter):
    base_encounter.metabolic_panel.ldl_mg_dl = 165.0
    base_encounter.metabolic_panel.triglycerides_mg_dl = 65.0
    
    motor = PrecisionNutritionMotor()
    result = motor.compute(base_encounter)
    
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    actions = [a.task for a in result.action_checklist]
    assert any("ApoE4" in task or "Restricción Severa de Grasa Saturada" in task for task in actions)
    assert any("Proxy ApoE4+" in p for p in result.metadata["phenotypes"])

def test_amy1_carb_intolerance_proxy(base_encounter):
    # Setting Glucose and Insulin to generate HOMA-IR = ~3.0 (i.e. > 2.5)
    base_encounter.metabolic_panel.glucose_mg_dl = 100.0
    base_encounter.metabolic_panel.insulin_mu_u_ml = 12.5
    base_encounter.metabolic_panel.triglycerides_mg_dl = 160.0
    base_encounter.metabolic_panel.hdl_mg_dl = 35.0
    
    motor = PrecisionNutritionMotor()
    result = motor.compute(base_encounter)
    
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    actions = [a.task for a in result.action_checklist]
    assert any("Carbohidratos" in task for task in actions)
    assert any("Proxy AMY1/IRS1" in p for p in result.metadata["phenotypes"])

def test_standard_nutrition(base_encounter):
    motor = PrecisionNutritionMotor()
    result = motor.compute(base_encounter)
    
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "Perfil Nutricional Estándar" in result.calculated_value
