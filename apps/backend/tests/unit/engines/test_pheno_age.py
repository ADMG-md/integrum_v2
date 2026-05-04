import pytest
from src.engines.specialty.bio_age import BiologicalAgeMotor, PhenoAgeLevineInput
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema, MetabolicPanelSchema
from datetime import datetime

def test_encounter_phenoage_input_assembly():
    # Test that Encounter correctly assembles the DTO
    demographics = DemographicsSchema(age_years=50, gender="male")
    metabolic = MetabolicPanelSchema(
        albumin_g_dl=4.5,
        creatinine_mg_dl=0.9,
        glucose_mg_dl=90,
        hs_crp_mg_l=1.0,
        lymphocyte_percent=30,
        mcv_fl=90,
        rdw_percent=13,
        alkaline_phosphatase_u_l=75,
        wbc_k_ul=6.5
    )
    cardio = MetabolicPanelSchema()
    
    encounter = Encounter(
        id="test-1",
        demographics=demographics,
        metabolic_panel=metabolic,
        cardio_panel=cardio
    )
    
    dto = encounter.phenoage_input
    assert dto is not None
    assert isinstance(dto, PhenoAgeLevineInput)
    assert dto.chronological_age_years == 50
    assert dto.albumin_g_dl == 4.5

def test_encounter_phenoage_input_missing_marker():
    # Test that missing markers return None DTO
    demographics = DemographicsSchema(age_years=50)
    metabolic = MetabolicPanelSchema(albumin_g_dl=4.5) # Missing others
    cardio = MetabolicPanelSchema()
    
    encounter = Encounter(
        id="test-2",
        demographics=demographics,
        metabolic_panel=metabolic,
        cardio_panel=cardio
    )
    
    assert encounter.phenoage_input is None

# @pytest.mark.xfail(reason="Formula activated")
def test_pheno_age_motor_execution():
    motor = BiologicalAgeMotor()
    data = PhenoAgeLevineInput(
        chronological_age_years=50,
        albumin_g_dl=4.5,
        creatinine_mg_dl=0.9,
        glucose_mg_dl=90,
        hs_crp_mg_l=1.0,
        lymphocyte_percent=30,
        mcv_fl=90,
        rdw_percent=13,
        alkaline_phosphatase_u_l=75,
        wbc_k_ul=6.5
    )
    # This should raise NotImplementedError, which is marked as xfail
    result = motor(data)
    assert result.status == "ok"
    assert result.biological_age_years is not None
