"""
Shared test fixtures for Integrum V2 clinical engine tests.
"""

import pytest
from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)
from src.domain.models import ClinicalHistory, TraumaHistory, MedicationStatement
from src.schemas.encounter import MedicationSchema
from src.services.clinical_engine_service import ClinicalIntelligenceBridge
from src.engines.specialty_runner import SpecialtyRunner


@pytest.fixture
def bridge():
    return ClinicalIntelligenceBridge()


@pytest.fixture
def runner():
    return SpecialtyRunner()


@pytest.fixture
def empty_encounter():
    """Minimal encounter with no clinical data."""
    return Encounter(
        id="test-empty",
        demographics=DemographicsSchema(),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
    )


@pytest.fixture
def minimal_encounter():
    """Encounter with basic demographics and metabolic panel."""
    return Encounter(
        id="test-minimal",
        demographics=DemographicsSchema(age_years=45.0, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=100.0,
            creatinine_mg_dl=1.0,
            hba1c_percent=5.7,
            albumin_g_dl=4.0,
            alkaline_phosphatase_u_l=80.0,
            mcv_fl=90.0,
            rdw_percent=13.0,
            wbc_k_ul=7.0,
            lymphocyte_percent=30.0,
            neutrophil_percent=60.0,
            ferritin_ng_ml=100.0,
            hs_crp_mg_l=1.5,
        ),
        cardio_panel=CardioPanelSchema(
            total_cholesterol_mg_dl=200.0,
            ldl_mg_dl=130.0,
            hdl_mg_dl=45.0,
            triglycerides_mg_dl=150.0,
            apob_mg_dl=100.0,
            lpa_mg_dl=30.0,
        ),
        observations=[
            Observation(code="29463-7", value=85.0, unit="kg"),  # Weight
            Observation(code="8302-2", value=170.0, unit="cm"),  # Height
            Observation(code="8480-6", value=135.0, unit="mmHg"),  # SBP
            Observation(code="8462-4", value=85.0, unit="mmHg"),  # DBP
            Observation(code="WAIST-001", value=95.0, unit="cm"),  # Waist
            Observation(code="AGE-001", value=45.0),  # Age
        ],
        metadata={"sex": "male"},
    )


@pytest.fixture
def full_encounter():
    """Encounter with comprehensive clinical data for integration testing."""
    return Encounter(
        id="test-full",
        demographics=DemographicsSchema(age_years=52.0, gender="female"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=110.0,
            creatinine_mg_dl=0.9,
            hba1c_percent=6.2,
            insulin_mu_u_ml=15.0,
            albumin_g_dl=3.8,
            alkaline_phosphatase_u_l=75.0,
            mcv_fl=88.0,
            rdw_percent=13.5,
            wbc_k_ul=6.5,
            lymphocyte_percent=28.0,
            neutrophil_percent=62.0,
            ferritin_ng_ml=80.0,
            hs_crp_mg_l=3.5,
            tsh_uIU_ml=5.2,
            ft4_ng_dl=0.7,
        ),
        cardio_panel=CardioPanelSchema(
            total_cholesterol_mg_dl=240.0,
            ldl_mg_dl=160.0,
            hdl_mg_dl=38.0,
            triglycerides_mg_dl=200.0,
            apob_mg_dl=120.0,
            lpa_mg_dl=50.0,
        ),
        observations=[
            Observation(code="29463-7", value=92.0, unit="kg"),
            Observation(code="8302-2", value=162.0, unit="cm"),
            Observation(code="8480-6", value=148.0, unit="mmHg"),
            Observation(code="8462-4", value=92.0, unit="mmHg"),
            Observation(code="WAIST-001", value=102.0, unit="cm"),
            Observation(code="AGE-001", value=52.0),
            Observation(code="11579-0", value=5.2),  # TSH
            Observation(code="FT4-001", value=0.7),  # FT4
            Observation(code="30522-7", value=4.2),  # hs-CRP
            Observation(code="26499-4", value=5.5),  # Neutrophils
            Observation(code="26474-7", value=1.8),  # Lymphocytes
        ],
        metadata={"sex": "female"},
    )


@pytest.fixture
def encounter_with_metabolic_data():
    """Full metabolic data for FLI, VAI, LAP, HSI, NFS, CMI, QUICKI, Allostatic."""
    return Encounter(
        id="test-metabolic",
        demographics=DemographicsSchema(age_years=55.0, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=110.0,
            insulin_mu_u_ml=15.0,
            creatinine_mg_dl=1.0,
            albumin_g_dl=4.2,
            alkaline_phosphatase_u_l=85.0,
            mcv_fl=90.0,
            rdw_percent=13.5,
            hs_crp_mg_l=4.5,
            wbc_k_ul=7.5,
            lymphocyte_percent=28.0,
            ast_u_l=35.0,
            alt_u_l=45.0,
            ggt_u_l=65.0,
            platelets_k_u_l=220.0,
            hba1c_percent=6.2,
        ),
        cardio_panel=CardioPanelSchema(
            total_cholesterol_mg_dl=245.0,
            ldl_mg_dl=160.0,
            hdl_mg_dl=35.0,
            triglycerides_mg_dl=250.0,
            apob_mg_dl=120.0,
            apoa1_mg_dl=110.0,
        ),
        observations=[
            Observation(code="29463-7", value=95.0, unit="kg"),
            Observation(code="8302-2", value=175.0, unit="cm"),
            Observation(code="WAIST-001", value=108.0, unit="cm"),
            Observation(code="8480-6", value=145.0, unit="mmHg"),
            Observation(code="8462-4", value=92.0, unit="mmHg"),
            Observation(code="AGE-001", value=55.0),
        ],
        metadata={"sex": "male"},
    )


@pytest.fixture
def encounter_with_glp1_therapy(encounter_with_metabolic_data):
    """Encounter with active GLP-1 therapy for monitoring."""
    enc = encounter_with_metabolic_data
    enc.medications = [
        MedicationSchema(
            name="SEMAGLUTIDE",
            code="SEMAGLUTIDE",
            dose="1.0mg",
            frequency="weekly",
        )
    ]
    enc.metadata.update(
        {
            "prev_weight_kg": 105.0,
            "prev_muscle_mass_kg": 65.0,
            "glp1_weeks": 16,
        }
    )
    enc.observations.append(Observation(code="MMA-001", value=58.0, unit="kg"))
    return enc


@pytest.fixture
def encounter_with_metformin(encounter_with_metabolic_data):
    """Encounter with metformin for B12 monitoring."""
    enc = encounter_with_metabolic_data
    enc.medications = [
        MedicationSchema(
            name="METFORMIN",
            code="METFORMIN",
            dose="1000mg",
            frequency="bid",
        )
    ]
    enc.observations.append(Observation(code="VITB12-001", value=180.0, unit="pg/mL"))
    return enc


@pytest.fixture
def encounter_with_ace_high(encounter_with_metabolic_data):
    """Encounter with high ACE score."""
    enc = encounter_with_metabolic_data
    enc.history = ClinicalHistory(
        has_type2_diabetes=True,
        trauma=TraumaHistory(ace_score=7),
    )
    return enc


@pytest.fixture
def encounter_with_t2dm_ckd(encounter_with_metabolic_data):
    """Encounter with T2DM + CKD for SGLT2i benefit assessment."""
    enc = encounter_with_metabolic_data
    enc.history = ClinicalHistory(
        has_type2_diabetes=True,
        has_ckd=True,
    )
    enc.observations.append(Observation(code="UACR-001", value=150.0, unit="mg/g"))
    return enc


@pytest.fixture
def encounter_with_hypertensive_med(encounter_with_metabolic_data):
    """Encounter with hypertensive/obesogenic medications."""
    enc = encounter_with_metabolic_data
    enc.medications = [
        MedicationSchema(
            name="AMLODIPINE",
            code="AMLODIPINE",
            dose="10mg",
            frequency="daily",
        ),
        MedicationSchema(
            name="PAROXETINE",
            code="PAROXETINE",
            dose="20mg",
            frequency="daily",
        ),
    ]
    return enc
