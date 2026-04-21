import pytest
from src.engines.specialty_runner import SpecialtyRunner
from src.domain.models import Encounter, ClinicalHistory, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema, CardioPanelSchema

def test_full_stack_pharmacogenomics():
    """
    Simula el pipeline interno T1-T4 alimentado por payload de Frontend
    """
    encounter_base = Encounter(
        id="M8-001",
        demographics=DemographicsSchema(age_years=40, gender="male", weight_kg=85.0, height_cm=170.0),
        history=ClinicalHistory(
            has_statin_myalgia=True,
            caffeine_anxiety_insomnia=True, 
            taking_ppi_chronically=True,
            taking_otc_vitd=True
        ),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=105.0, insulin_mu_u_ml=15.0),
        cardio_panel=CardioPanelSchema(ldl_mg_dl=175.0, hdl_mg_dl=30.0, triglycerides_mg_dl=50.0),
        observations=[
            Observation(code="29463-7", value=85.0, unit="kg"),
            Observation(code="8302-2", value=170.0, unit="cm"),
            Observation(code="VIT-D-25OH", value=20.0, unit="ng/mL")
        ]
    )
    
    runner = SpecialtyRunner()
    results = runner.run_all(encounter_base)
    
    # Extract
    pharma = results.get("PharmacogenomicProxyMotor")
    nutri = results.get("PrecisionNutritionMotor")
    
    assert pharma is not None, "El Proxy Farmacogenómico no se encuentra registrado en el runner global."
    assert nutri is not None, "El Motor de Nutrición de Precisión no se encuentra registrado."
    
    # Assert
    nutri_phenotypes = nutri.metadata.get("phenotypes", [])
    assert any("ApoE4" in p for p in nutri_phenotypes), "Error de Detección: Patrón ApoE4 (LMHR) no se decodificó."
    
    pharma_findings = pharma.calculated_value
    assert "SLCO1B1" in pharma_findings, "Proxy Estatinas falló."
    assert "CYP1A2" in pharma_findings, "Proxy Cafeína falló."
    assert "VDR" in pharma_findings, "Proxy VitD / IBP falló."

    print("\n✅ End-to-End validado: Intercepción Exitosa de Proxy Farmacogenómico y ApoE4 en Pipeline Analítico.")

if __name__ == "__main__":
    test_full_stack_pharmacogenomics()
