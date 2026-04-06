"""
API schemas for Integrum V2.

These are Pydantic models used for HTTP request/response serialization.
Domain types (ObesityOnsetTrigger, DrugEntry, panels, etc.) are re-exported
from src.domain.models to maintain a single source of truth.
"""

from typing import List, Optional, Any, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# --- Re-export domain types (single source of truth) ---
from src.domain.models import (
    ObesityOnsetTrigger,
    DrugEntry,
    TraumaHistory,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


# --- API-specific schemas ---


class PatientCreate(BaseModel):
    external_id: str
    full_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class PatientRead(PatientCreate):
    id: str
    created_at: datetime


class ObservationSchema(BaseModel):
    code: str
    value: Any = Field(
        ..., description="SaMD Observation value (Numerical or Categorical)"
    )
    unit: Optional[str] = None
    category: str = "Clinical"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("value")
    @classmethod
    def validate_biological_limits(cls, v: Any, info: Any) -> Any:
        LIMITS = {
            "2339-0": (20, 600),
            "8480-6": (60, 250),
            "AGE-001": (0, 125),
            "29463-7": (2, 400),
            "8302-2": (30, 250),
            "WAIST-001": (30, 300),
            "APOB-001": (20, 500),
            "TSH-001": (0.01, 100),
            "FT4-001": (0.1, 10),
            "FT3-001": (1.0, 20),
            "HS-CRP-001": (0.01, 100),
            "ALB-001": (1.0, 10.0),
            "ALKPHOS-001": (10, 1000),
            "MCV-001": (50, 150),
            "RDW-001": (5, 30),
            "WBC-001": (1.0, 50.0),
            "GGT-001": (1, 2000),
            "FER-001": (1, 10000),
            "UA-001": (1, 20),
            "5XSTS-SEC": (3.0, 120.0),
            "GRIP-STR-R": (5.0, 80.0),
            "GRIP-STR-L": (5.0, 80.0),
            "GAIT-SPEED": (0.1, 3.0),
            "SARCF-SCORE": (0, 10),
            "VITD-001": (5.0, 150.0),
            "VITB12-001": (50.0, 2000.0),
            "HOMOCYS-001": (1.0, 50.0),
            "TPO-AB-001": (0.0, 5000.0),
            "UACR-001": (0.0, 3000.0),
            "LIPASE-001": (0.0, 5000.0),
            "AMYLASE-001": (0.0, 500.0),
        }

        code = info.data.get("code")
        if code in LIMITS:
            try:
                val = float(v)
                low, high = LIMITS[code]
                if not (low <= val <= high):
                    raise ValueError(
                        f"Value {val} for {code} is outside physiological limits ({low}-{high})"
                    )
                return val
            except (ValueError, TypeError):
                if code in ["2339-0", "8480-6", "AGE-001", "29463-7", "8302-2"]:
                    raise ValueError(f"Value for {code} must be a number")

        # Universal physiological guard: reject any numeric value outside human biology
        try:
            val = float(v)
            if val < -50 or val > 1000:
                raise ValueError(
                    f"Value {val} is outside universal physiological bounds (-50 to 1000)"
                )
            return val
        except ValueError:
            if isinstance(v, (int, float)):
                raise
        return v


class ClinicalHistorySchema(BaseModel):
    """Extended clinical history for API input — adds fields beyond the domain model."""

    onset_trigger: Optional[ObesityOnsetTrigger] = None
    age_of_onset: Optional[int] = Field(None, ge=0, le=100)
    max_weight_ever_kg: Optional[float] = Field(None, ge=20, le=500)

    current_medications: List[DrugEntry] = Field(default_factory=list)
    previous_medications: List[DrugEntry] = Field(default_factory=list)

    trauma: Optional[TraumaHistory] = None

    has_type2_diabetes: bool = False
    has_prediabetes: bool = False
    has_hypertension: bool = False
    has_dyslipidemia: bool = False
    has_nafld: bool = False
    has_gout: bool = False
    has_hypothyroidism: bool = False
    has_pcos: bool = False
    has_osa: bool = False
    has_gerd: bool = False
    has_ckd: bool = False

    has_heart_failure: bool = False
    has_coronary_disease: bool = False
    has_stroke: bool = False
    has_retinopathy: bool = False
    has_neuropathy: bool = False

    has_bariatric_surgery: bool = False
    bariatric_surgery_type: Optional[str] = None
    bariatric_surgery_date: Optional[str] = None
    other_surgeries: Optional[str] = ""

    allergies: Optional[str] = ""
    smoking_status: Literal["never", "former", "current"] = "never"
    alcohol_intake: Literal["none", "occasional", "frequent"] = "none"

    has_glaucoma: bool = False
    has_seizures_history: bool = False
    has_eating_disorder_history: bool = False
    family_history_thyroid_cancer: bool = False
    has_active_substance_abuse: bool = False

    # GLP-1/GIP contraindication screening (FDA labeling)
    has_history_medullary_thyroid_carcinoma: bool = False
    has_history_men2: bool = False
    has_history_pancreatitis: bool = False
    has_gastroparesis: bool = False


class BiometricsSchema(BaseModel):
    weight_kg: float = Field(..., ge=20, le=500)
    height_cm: float = Field(..., ge=30, le=250)
    waist_cm: Optional[float] = Field(None, ge=30, le=300)
    hip_cm: Optional[float] = Field(None, ge=30, le=300)
    neck_cm: Optional[float] = None
    systolic_bp: Optional[int] = Field(None, ge=60, le=300)
    diastolic_bp: Optional[int] = Field(None, ge=30, le=200)
    # BIA / Body Composition
    body_fat_percent: Optional[float] = None
    fat_mass_kg: Optional[float] = None
    lean_mass_kg: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    skeletal_muscle_index: Optional[float] = None
    visceral_fat_area_cm2: Optional[float] = None
    visceral_fat_level: Optional[int] = None
    basal_metabolic_rate: Optional[float] = None
    total_body_water_percent: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    # Anthropometry (sarcopenia screening)
    arm_circumference_cm: Optional[float] = Field(None, ge=10, le=60)
    calf_circumference_cm: Optional[float] = Field(None, ge=15, le=60)
    # Functional sarcopenia (EWGSOP2)
    grip_strength_right_kg: Optional[float] = Field(None, ge=5, le=80)
    grip_strength_left_kg: Optional[float] = Field(None, ge=5, le=80)
    gait_speed_m_s: Optional[float] = Field(None, ge=0.1, le=3.0)
    sarcf_score: Optional[int] = Field(None, ge=0, le=10)
    five_x_sts_seconds: Optional[float] = Field(None, ge=3.0, le=120.0)


class PsychometricsSchema(BaseModel):
    phq9_score: Optional[int] = Field(None, ge=0, le=27)
    phq9_item_9_score: Optional[int] = Field(
        None,
        ge=0,
        le=3,
        description="PHQ-9 Item 9: Suicidal ideation (0=not at all, 3=nearly every day). FDA Black Box Warning gate for bupropion/naltrexone.",
    )
    gad7_score: Optional[int] = Field(None, ge=0, le=21)
    atenas_insomnia_score: Optional[int] = Field(None, ge=0, le=24)
    tfeq_cognitive_restraint: Optional[float] = None
    tfeq_uncontrolled_eating: Optional[float] = None
    tfeq_emotional_eating: Optional[float] = None
    ace_total_score: Optional[int] = None

    phq9_responses: Optional[Dict[str, int]] = None
    gad7_responses: Optional[Dict[str, int]] = None
    atenas_responses: Optional[Dict[str, int]] = None

    fnq_intrusive_thoughts: Optional[int] = None
    fnq_control_difficulty: Optional[int] = None


class LifestyleSchema(BaseModel):
    sleep_hours: Optional[float] = None
    sleep_quality_score: Optional[int] = Field(None, ge=1, le=10)
    stress_level_vas: Optional[int] = Field(None, ge=1, le=10)
    physical_activity_min_week: Optional[int] = None
    ultra_processed_intake_score: Optional[int] = None
    first_meal_time: Optional[str] = None
    last_meal_time: Optional[str] = None


class MetabolicPanelInput(BaseModel):
    model_config = {"populate_by_name": True}

    glucose_mg_dl: Optional[float] = Field(None, ge=40, le=600, alias="glucose_mgdl")
    creatinine_mg_dl: Optional[float] = Field(
        None, ge=0.2, le=10.0, alias="creatinine_mgdl"
    )
    hba1c_percent: Optional[float] = Field(None, ge=3.0, le=18.0)
    insulin_mu_u_ml: Optional[float] = Field(
        None, ge=0.5, le=500, alias="insulin_muUml"
    )
    c_peptide_ng_ml: Optional[float] = Field(None, ge=0.1, le=50, alias="c_peptide")

    total_cholesterol_mg_dl: Optional[float] = Field(
        None, ge=70, le=400, alias="total_chol_mgdl"
    )
    triglycerides_mg_dl: Optional[float] = Field(
        None, ge=0, le=1200, alias="triglycerides_mgdl"
    )
    hdl_mg_dl: Optional[float] = Field(None, ge=0, le=150, alias="hdl_mgdl")
    ldl_mg_dl: Optional[float] = Field(None, ge=0, le=400, alias="ldl_mgdl")
    vldl_mg_dl: Optional[float] = Field(None, ge=0, le=300, alias="vldl_mgdl")
    apob_mg_dl: Optional[float] = Field(None, ge=0, le=300, alias="apob_mgdl")
    lpa_mg_dl: Optional[float] = Field(None, ge=0, le=300, alias="lpa_mgdl")
    apoa1_mg_dl: Optional[float] = Field(None, ge=0, le=300, alias="apoa1_mgdl")

    tsh_u_iu_ml: Optional[float] = Field(None, ge=0.01, le=100, alias="tsh_uIUmL")
    ft4_ng_dl: Optional[float] = Field(None, ge=0.1, le=10, alias="ft4_ngdL")
    ft3_pg_ml: Optional[float] = Field(None, ge=1.0, le=20, alias="ft3_pgmL")
    rt3_ng_dl: Optional[float] = Field(None, ge=5, le=200, alias="rt3_ngdL")
    shbg_nmol_l: Optional[float] = Field(None, ge=1, le=300, alias="shbg_nmolL")
    cortisol_am_mcg_dl: Optional[float] = Field(
        None, ge=1, le=100, alias="cortisol_am_mcgdl"
    )

    ast_u_l: Optional[float] = Field(None, ge=5, le=5000, alias="ast_uL")
    alt_u_l: Optional[float] = Field(None, ge=5, le=5000, alias="alt_uL")
    ggt_u_l: Optional[float] = Field(None, ge=1, le=2000, alias="ggt_uL")
    uric_acid_mg_dl: Optional[float] = Field(None, ge=1, le=20, alias="uric_acid_mgdl")
    platelets_k_u_l: Optional[float] = Field(
        None, ge=10, le=1000, alias="platelets_k_uL"
    )

    # Hypertension workup
    aldosterone_ng_dl: Optional[float] = Field(
        None, ge=1, le=200, alias="aldosterone_ngdL"
    )
    renin_ng_ml_h: Optional[float] = Field(None, ge=0.1, le=500, alias="renin_ngmLh")

    albumin_g_dl: Optional[float] = Field(None, ge=2.0, le=6.0, alias="albumin_gdl")
    alkaline_phosphatase_u_l: Optional[float] = Field(
        None, ge=20, le=1000, alias="alk_phos_ul"
    )
    mcv_fl: Optional[float] = Field(None, ge=60, le=120)
    rdw_percent: Optional[float] = Field(None, ge=8, le=30)
    wbc_k_ul: Optional[float] = Field(None, ge=1, le=100)
    lymphocyte_percent: Optional[float] = Field(None, ge=1, le=80)
    neutrophil_percent: Optional[float] = Field(None, ge=10, le=95)
    ferritin_ng_ml: Optional[float] = Field(None, ge=5, le=2000)
    hs_crp_mg_l: Optional[float] = Field(None, ge=0.0, le=50.0)
    gada_antibodies: Optional[bool] = None


class ConditionSchema(BaseModel):
    code: str
    title: str
    system: str = "CIE-10"
    clinical_status: Literal["active", "recurrence", "remission", "resolved"] = "active"
    verification_status: Literal[
        "confirmed", "provisional", "differential", "refuted"
    ] = "confirmed"
    severity: Optional[Literal["mild", "moderate", "severe"]] = None
    onset_date: Optional[str] = None
    notes: Optional[str] = None


class MedicationSchema(BaseModel):
    code: Optional[str] = "CUSTOM"
    name: str
    status: Literal["active", "completed", "on-hold", "stopped"] = "active"
    dose_amount: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = "oral"
    is_obesity_inducing: bool = False
    weight_effect: Optional[Literal["gain", "loss", "neutral"]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    prescriber: Optional[str] = None
    indication: Optional[str] = None
    notes: Optional[str] = None


class EncounterCreate(BaseModel):
    patient_id: str
    observations: List[ObservationSchema] = Field(default_factory=list)
    history: Optional[ClinicalHistorySchema] = None
    biometrics: Optional[BiometricsSchema] = None
    metabolic: Optional[MetabolicPanelInput] = None
    psychometrics: Optional[PsychometricsSchema] = None
    lifestyle: Optional[LifestyleSchema] = None

    reason_for_visit: str
    personal_history: Optional[str] = ""
    family_history: Optional[str] = ""
    conditions: List[ConditionSchema] = Field(default_factory=list)
    medications: List[MedicationSchema] = Field(default_factory=list)
    status: str = "DRAFT"


class EncounterRead(EncounterCreate):
    id: str
    created_at: datetime
    clinical_notes: Optional[str] = None
    plan_of_action: Optional[Dict[str, Any]] = None


class AdjudicationResultSchema(BaseModel):
    calculated_value: str
    confidence: float
    evidence: List[Dict[str, Any]] = []
    log_id: Optional[str] = None
    requirement_id: Optional[str] = None
    explanation: Optional[str] = None
    integrity_hash: Optional[str] = None

    estado_ui: Optional[str] = "INDETERMINATE_LOCKED"
    dato_faltante: Optional[str] = None
    recomendacion_farmacologica: List[str] = []

    action_checklist: List[Dict[str, Any]] = []
    critical_omissions: List[Dict[str, Any]] = []


class ProcessResponseSchema(BaseModel):
    encounter_id: str
    results: Dict[str, Any]  # Flexible: motors return different output types
    data_readiness: Optional[Dict[str, Any]] = (
        None  # ClinicalDataReadinessEngine output
    )


class EncounterFinalizeSchema(BaseModel):
    clinical_notes: Optional[str] = None
    plan_of_action: Optional[Dict[str, Any]] = None
    audit_payload: Optional[List[Dict[str, Any]]] = None
