"""
API schemas for Integrum V2.

These are Pydantic models used for HTTP request/response serialization.
Domain types (ObesityOnsetTrigger, DrugEntry, panels, etc.) are re-exported
from src.domain.models to maintain a single source of truth.
"""

from typing import List, Optional, Any, Dict, Literal, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

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


ObservationValueType = Union[int, float, str, bool]


class ObservationSchema(BaseModel):
    code: str
    value: ObservationValueType = Field(
        ..., description="SaMD Observation value (Numerical or Categorical)"
    )
    unit: Optional[str] = None
    category: str = "Clinical"
    metadata_json: Dict[str, ObservationValueType] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("value")
    @classmethod
    def validate_biological_limits(
        cls, v: ObservationValueType, info: Any
    ) -> ObservationValueType:
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
    lbm_boer_kg: Optional[float] = Field(
        None, description="Lean Body Mass calculada con fórmula de Boer"
    )
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

    @model_validator(mode="after")
    def validate_biometric_coherence(self) -> "BiometricsSchema":
        """
        Cross-field coherence validation.
        Hard blocks: physically/logically impossible values that indicate data entry error.
        These run server-side as defense-in-depth (frontend also validates).
        """
        sbp = self.systolic_bp
        dbp = self.diastolic_bp
        wt = self.weight_kg
        ht = self.height_cm

        # Rule 1: Systolic BP must always exceed diastolic
        if sbp is not None and dbp is not None:
            if sbp <= dbp:
                raise ValueError(
                    f"Coherence error: systolic_bp ({sbp}) must be greater than diastolic_bp ({dbp}). "
                    f"Pulse pressure ≤ 0 is physiologically impossible."
                )

        # Rule 2: BMI < 10 is physiologically impossible — likely unit error (m vs cm)
        if wt is not None and ht is not None and ht > 0:
            bmi = wt / (ht / 100) ** 2
            if bmi < 10:
                raise ValueError(
                    f"Coherence error: resulting BMI ({bmi:.1f} kg/m²) is physiologically impossible. "
                    f"Likely height entered in meters instead of centimeters "
                    f"(weight={wt}kg, height={ht}cm → BMI={bmi:.1f})."
                )

        return self


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

    @model_validator(mode="after")
    def validate_metabolic_coherence(self) -> "MetabolicPanelInput":
        """
        Cross-field coherence for metabolic panel.
        Hard blocks for results that are logically/analytically impossible.
        Defense-in-depth: frontend validates first; backend catches API-direct calls.
        """
        tg = self.triglycerides_mg_dl
        hdl = self.hdl_mg_dl
        ldl = self.ldl_mg_dl
        vldl = self.vldl_mg_dl
        total_chol = self.total_cholesterol_mg_dl
        hba1c = self.hba1c_percent
        gluc = self.glucose_mg_dl

        # Rule: LDL > total cholesterol is logically impossible
        if ldl is not None and total_chol is not None and ldl > total_chol:
            raise ValueError(
                f"Coherence error: ldl_mg_dl ({ldl}) cannot exceed total_cholesterol_mg_dl ({total_chol}). "
                f"LDL is a fraction of total cholesterol."
            )

        # Rule: TG < VLDL — VLDL = TG/5 by definition, VLDL cannot exceed TG
        if tg is not None and vldl is not None and tg < vldl:
            raise ValueError(
                f"Coherence error: triglycerides_mg_dl ({tg}) cannot be less than vldl_mg_dl ({vldl}). "
                f"VLDL is estimated as TG/5 (Friedewald). Likely field inversion."
            )

        # Rule: TG > 400 + HbA1c — assay interference (ion exchange method)
        # TG > ~400 mg/dL invalidates HbA1c by ion exchange chromatography.
        if tg is not None and hba1c is not None and tg > 400:
            raise ValueError(
                f"Coherence error: triglycerides_mg_dl ({tg}) > 400 invalidates HbA1c by ion exchange assay "
                f"(most common method in Colombian labs). The HbA1c result of {hba1c}% is analytically unreliable. "
                f"Reconfirm HbA1c by HPLC or boronate affinity after normalizing TG, or remove HbA1c from this encounter."
            )

        # Rule: Glucose vs eAG discordance (Wheeler formula)
        # eAG (mg/dL) = 28.7 × HbA1c(%) − 46.7 [ADAG study, ADA 2008]
        # Threshold 120 mg/dL allows for postprandial vs fasting variation.
        if gluc is not None and hba1c is not None:
            eag = hba1c * 28.7 - 46.7
            if eag > 0 and abs(gluc - eag) > 120:
                raise ValueError(
                    f"Coherence error: glucose_mg_dl ({gluc}) deviates >120 mg/dL from eAG implied by hba1c_percent ({hba1c}%) "
                    f"[eAG = {eag:.0f} mg/dL, Wheeler formula]. "
                    f"Possible causes: unit error (mmol/L vs mg/dL), lab from different time period, "
                    f"or hemolytic anemia affecting HbA1c."
                )

        return self


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

    # Outcome tracking — optional, but critical for research dataset quality.
    # Captures what happened TO the patient at this visit / since last encounter.
    weight_current_kg: Optional[float] = Field(
        None,
        ge=20,
        le=500,
        description="Patient weight at this encounter (enables longitudinal delta)",
    )
    outcome_status: Optional[str] = Field(
        None, description="Physician global assessment: MEJORADO | ESTABLE | DETERIORO"
    )
    adverse_event: Optional[str] = Field(
        None,
        max_length=500,
        description="Adverse event since last encounter (hospitalization, CV event, severe side effect)",
    )
    medication_changed: Optional[bool] = Field(
        None, description="Prescription changed at this encounter"
    )
    adherence_reported: Optional[str] = Field(
        None, description="Patient-reported adherence: ALTA | MEDIA | BAJA"
    )
