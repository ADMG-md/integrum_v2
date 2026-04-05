"""
Domain models for Integrum V2 clinical engine.

This module contains the core domain entities that represent clinical concepts.
These are pure Pydantic models with no API/HTTP concerns — they belong to the
domain layer of Clean Architecture.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime, date
from enum import Enum
import structlog

logger = structlog.get_logger()


# --- Utility ---


def safe_float(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# --- Clinical Evidence & Adjudication (from base_models) ---


class ClinicalEvidence(BaseModel):
    type: str
    code: str
    display: Optional[str] = None
    value: Any = None
    threshold: Optional[str] = None


class ActionItem(BaseModel):
    category: Literal["pharmacological", "lifestyle", "referral", "diagnostic"]
    priority: Literal["low", "medium", "high", "critical"]
    task: str
    rationale: str
    status: str = "pending"


class MedicationGap(BaseModel):
    drug_class: str
    gap_type: Literal["OMISSION", "UNDERDOSED", "CONTRAINDICATED"]
    severity: Literal["low", "medium", "high", "critical"]
    clinical_rationale: str


class AdjudicationResult(BaseModel):
    calculated_value: str
    confidence: float = Field(ge=0, le=1)
    evidence: List[ClinicalEvidence] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)
    log_id: Optional[str] = None
    requirement_id: Optional[str] = None
    explanation: Optional[str] = None
    estado_ui: str = "INDETERMINATE_LOCKED"
    dato_faltante: Optional[str] = None
    recomendacion_farmacologica: List[str] = []
    action_checklist: List[ActionItem] = []
    critical_omissions: List[MedicationGap] = []


# --- History & Clinical Context ---


class ObesityOnsetTrigger(str, Enum):
    CHILDHOOD = "childhood"
    PUBERTY = "puberty"
    PREGNANCY = "pregnancy"
    MENOPAUSE = "menopause"
    SMOKING_CESSATION = "smoking_cessation"
    MEDICATION_INDUCED = "medication"
    INJURY_IMMOBILITY = "injury"
    STRESS_TRAUMA = "stress"
    UNKNOWN = "unknown"


class DrugEntry(BaseModel):
    drug_name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    is_obesity_inducing: bool = False


class TraumaHistory(BaseModel):
    ace_score: Optional[int] = Field(None, ge=0, le=10)
    has_history_of_abuse: bool = False
    emotional_impact_score: Optional[int] = Field(None, ge=0, le=10)


class ClinicalHistory(BaseModel):
    onset_trigger: Optional[ObesityOnsetTrigger] = None
    age_of_onset: Optional[int] = None
    max_weight_ever_kg: Optional[float] = None

    current_medications: List[DrugEntry] = []
    previous_medications: List[DrugEntry] = []

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
    has_glaucoma: bool = False
    has_seizures_history: bool = False
    has_eating_disorder_history: bool = False
    family_history_thyroid_cancer: bool = False

    # GLP-1/GIP contraindication screening (FDA labeling)
    has_history_medullary_thyroid_carcinoma: bool = False
    has_history_men2: bool = False
    has_history_pancreatitis: bool = False
    has_gastroparesis: bool = False

    # Suicide risk gate (FDA Black Box Warning for bupropion)
    phq9_item_9_score: Optional[int] = None

    has_ckd: bool = False
    has_heart_failure: bool = False
    has_coronary_disease: bool = False
    has_stroke: bool = False
    has_retinopathy: bool = False
    has_neuropathy: bool = False

    smoking_status: str = "never"
    alcohol_intake: str = "none"

    # Women's health
    pregnancy_status: str = "unknown"
    menopausal_status: str = "unknown"
    last_menstrual_period: Optional[date] = None
    cycle_regularity: str = "unknown"
    has_endometriosis: bool = False
    has_history_preeclampsia: bool = False
    has_history_gestational_diabetes: bool = False
    contraception_method: Optional[str] = None
    on_hrt: bool = False
    ferriman_gallwey_score: Optional[int] = None

    # Men's health
    has_erectile_dysfunction: bool = False
    iief5_score: Optional[int] = None
    has_prostate_issues: bool = False
    has_male_pattern_baldness: bool = False
    has_gynecomastia: bool = False


# --- Core Domain Entities ---


class Observation(BaseModel):
    code: str
    value: Any
    unit: Optional[str] = None
    category: str = "Clinical"
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class Condition(BaseModel):
    code: str
    title: str
    system: str = "CIE-10"


class MedicationStatement(BaseModel):
    code: str
    name: str
    is_active: bool = True


# --- Clinical Panels (pure domain data — moved from schemas/) ---


class DemographicsSchema(BaseModel):
    age_years: Optional[float] = Field(None, ge=0, le=125)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    zip_code: Optional[str] = None


class MetabolicPanelSchema(BaseModel):
    model_config = {"populate_by_name": True}

    glucose_mg_dl: Optional[float] = Field(None, ge=40, le=600)
    creatinine_mg_dl: Optional[float] = Field(None, ge=0.2, le=10.0)
    hba1c_percent: Optional[float] = Field(None, ge=3.0, le=18.0)
    insulin_mu_u_ml: Optional[float] = None

    albumin_g_dl: Optional[float] = Field(None, ge=2.0, le=6.0)
    alkaline_phosphatase_u_l: Optional[float] = Field(None, ge=20, le=1000)
    mcv_fl: Optional[float] = Field(None, ge=60, le=120)
    rdw_percent: Optional[float] = Field(None, ge=8, le=30)
    wbc_k_ul: Optional[float] = Field(None, ge=1, le=100)
    lymphocyte_percent: Optional[float] = Field(None, ge=1, le=80)
    neutrophil_percent: Optional[float] = Field(None, ge=10, le=95)
    ferritin_ng_ml: Optional[float] = Field(None, ge=5, le=2000)
    hs_crp_mg_l: Optional[float] = Field(None, ge=0.0, le=50.0)

    # Thyroid — accept both naming conventions
    tsh_uIU_ml: Optional[float] = Field(None, alias="tsh_u_iu_ml")
    ft4_ng_dl: Optional[float] = None
    ft3_pg_ml: Optional[float] = None
    rt3_ng_dl: Optional[float] = Field(None, alias="rt3_ngdl")
    shbg_nmol_l: Optional[float] = Field(None, alias="shbg_nmolL")
    cortisol_am_mcg_dl: Optional[float] = Field(None, alias="cortisol_am_mcgdl")

    # Extended metabolic
    c_peptide_ng_ml: Optional[float] = None
    gada_antibodies: Optional[bool] = None
    uric_acid_mg_dl: Optional[float] = Field(None, alias="uric_acid_mgdl")
    platelets_k_u_l: Optional[float] = Field(None, alias="platelets_k_uL")
    ast_u_l: Optional[float] = Field(None, alias="ast_uL")
    alt_u_l: Optional[float] = Field(None, alias="alt_uL")
    ggt_u_l: Optional[float] = Field(None, alias="ggt_uL")

    # Hypertension workup
    aldosterone_ng_dl: Optional[float] = Field(None, alias="aldosterone_ngdL")
    renin_ng_ml_h: Optional[float] = Field(None, alias="renin_ngmLh")

    # Sprint 1: Micronutrients (critical in metabolic patients)
    vitamin_d_ng_ml: Optional[float] = Field(None, alias="vitd_ngml")
    vitamin_b12_pg_ml: Optional[float] = Field(None, alias="vitb12_pgml")
    homocysteine_umol_l: Optional[float] = Field(None, alias="homocys_umolL")
    tpo_antibodies_iu_ml: Optional[float] = Field(None, alias="tpoab_iuml")

    # Sprint 6: Reproductive hormones
    testosterone_total_ng_dl: Optional[float] = Field(None, alias="testo_ngdl")
    amh_ng_ml: Optional[float] = Field(None, alias="amh_ngml")
    lh_u_l: Optional[float] = Field(None, alias="lh_uL")
    fsh_u_l: Optional[float] = Field(None, alias="fsh_uL")
    estradiol_pg_ml: Optional[float] = Field(None, alias="estradiol_pgml")
    prolactin_ng_ml: Optional[float] = Field(None, alias="prolactin_ngml")
    dhea_s_mcg_dl: Optional[float] = Field(None, alias="dheas_mcgdl")
    psa_ng_ml: Optional[float] = Field(None, alias="psa_ngml")


class CardioPanelSchema(BaseModel):
    model_config = {"populate_by_name": True}

    total_cholesterol_mg_dl: Optional[float] = Field(None, ge=70, le=400)
    ldl_mg_dl: Optional[float] = Field(None, ge=0, le=400)
    hdl_mg_dl: Optional[float] = Field(None, ge=0, le=150)
    triglycerides_mg_dl: Optional[float] = Field(None, ge=0, le=1200)
    apob_mg_dl: Optional[float] = Field(None, ge=0, le=300)
    lpa_mg_dl: Optional[float] = Field(None, ge=0, le=300)
    vldl_mg_dl: Optional[float] = Field(None, alias="vldl_mgdl")
    apoa1_mg_dl: Optional[float] = Field(None, alias="apoa1_mgdl")


# --- Aggregate Root: Encounter ---


class Encounter(BaseModel):
    id: str
    demographics: DemographicsSchema
    metabolic_panel: MetabolicPanelSchema
    cardio_panel: CardioPanelSchema
    conditions: List[Condition] = []
    observations: List[Observation] = []
    medications: List[MedicationStatement] = []
    history: Optional[ClinicalHistory] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    reason_for_visit: Optional[str] = None
    personal_history: Optional[str] = None
    family_history: Optional[str] = None

    def has_condition(self, code: str) -> bool:
        return any(c.code == code for c in self.conditions)

    def has_medication(self, code: str) -> bool:
        return any(m.code == code and m.is_active for m in self.medications)

    def get_observation(self, code: str) -> Optional[Observation]:
        matching = [o for o in self.observations if o.code == code]
        if not matching:
            return None
        return sorted(matching, key=lambda x: x.timestamp, reverse=True)[0]

    def get_pillar_observations(self, category: str) -> List[Observation]:
        return [o for o in self.observations if o.category == category]

    # --- Delegated Calculators (SRP compliance) ---
    # Each calculator is a value object that encapsulates one domain of computation.
    # Properties below delegate to these for single-source-of-truth formulas.

    _renal: Optional[Any] = None
    _lipid: Optional[Any] = None
    _metabolic: Optional[Any] = None
    _anthro: Optional[Any] = None
    _hemodynamics: Optional[Any] = None
    _context: Optional[Any] = None
    _proxies: Optional[Any] = None

    def _get_renal(self):
        if self._renal is None:
            from src.engines.calculators import RenalFunction

            self._renal = RenalFunction.from_encounter(self)
        return self._renal

    def _get_lipid(self):
        if self._lipid is None:
            from src.engines.calculators import LipidProfile

            self._lipid = LipidProfile.from_encounter(self)
        return self._lipid

    def _get_metabolic(self):
        if self._metabolic is None:
            from src.engines.calculators import MetabolicIndices

            self._metabolic = MetabolicIndices.from_encounter(self)
        return self._metabolic

    def _get_anthro(self):
        if self._anthro is None:
            from src.engines.calculators import AnthropometricData

            self._anthro = AnthropometricData.from_encounter(self)
        return self._anthro

    def _get_hemodynamics(self):
        if self._hemodynamics is None:
            from src.engines.calculators import Hemodynamics

            self._hemodynamics = Hemodynamics.from_encounter(self)
        return self._hemodynamics

    def _get_context(self):
        if self._context is None:
            from src.engines.calculators import ClinicalContext

            self._context = ClinicalContext.from_encounter(self)
        return self._context

    def _get_proxies(self):
        if self._proxies is None:
            from src.engines.calculators import ProxyValues

            self._proxies = ProxyValues.from_encounter(self)
        return self._proxies

    # --- Simple pass-through properties ---

    @property
    def hs_crp_mg_l_value(self) -> Optional[float]:
        return self.metabolic_panel.hs_crp_mg_l

    @property
    def apob_mg_dl_value(self) -> Optional[float]:
        return self.cardio_panel.apob_mg_dl

    @property
    def lpa_mg_dl_value(self) -> Optional[float]:
        return self.cardio_panel.lpa_mg_dl

    # --- Delegated computed properties (backward compatible) ---

    @property
    def phenoage_input(self) -> Optional[Any]:
        from src.engines.specialty.bio_age import PhenoAgeLevineInput

        mp = self.metabolic_panel
        d = self.demographics
        age = d.age_years
        if age is None:
            return None
        albumin = mp.albumin_g_dl
        if albumin is None:
            return None
        creatinine = mp.creatinine_mg_dl
        if creatinine is None:
            return None
        glucose = mp.glucose_mg_dl
        if glucose is None:
            return None
        hs_crp = mp.hs_crp_mg_l
        if hs_crp is None:
            return None
        lymphocyte = mp.lymphocyte_percent
        if lymphocyte is None:
            return None
        mcv = mp.mcv_fl
        if mcv is None:
            return None
        rdw = mp.rdw_percent
        if rdw is None:
            return None
        alk_phos = mp.alkaline_phosphatase_u_l
        if alk_phos is None:
            return None
        wbc = mp.wbc_k_ul
        if wbc is None:
            return None

        return PhenoAgeLevineInput(
            chronological_age_years=age,
            albumin_g_dl=albumin,
            creatinine_mg_dl=creatinine,
            glucose_mg_dl=glucose,
            hs_crp_mg_l=hs_crp,
            lymphocyte_percent=lymphocyte,
            mcv_fl=mcv,
            rdw_percent=rdw,
            alkaline_phosphatase_u_l=alk_phos,
            wbc_k_ul=wbc,
        )

    @property
    def homa_ir(self) -> Optional[float]:
        return self._get_metabolic().homa_ir

    @property
    def homa_b(self) -> Optional[float]:
        return self._get_metabolic().homa_b

    @property
    def tyg_index(self) -> Optional[float]:
        return self._get_metabolic().tyg_index

    @property
    def mets_ir(self) -> Optional[float]:
        return self._get_metabolic().mets_ir

    @property
    def bmi(self) -> Optional[float]:
        return self._get_anthro().bmi

    @property
    def glucose_mg_dl(self) -> Optional[float]:
        return self._get_proxies().glucose_mg_dl

    @property
    def creatinine_mg_dl(self) -> Optional[float]:
        return self._get_proxies().creatinine_mg_dl

    @property
    def hba1c(self) -> Optional[float]:
        return self._get_proxies().hba1c

    @property
    def waist_to_height(self) -> Optional[float]:
        return self._get_anthro().waist_to_height

    @property
    def waist_to_hip(self) -> Optional[float]:
        return self._get_anthro().waist_to_hip

    @property
    def body_roundness_index(self) -> Optional[float]:
        return self._get_anthro().body_roundness_index

    @property
    def egfr_ckd_epi(self) -> Optional[float]:
        return self._get_renal().egfr_ckd_epi

    @property
    def uacr(self) -> Optional[float]:
        return self._get_renal().uacr

    @property
    def uric_acid(self) -> Optional[float]:
        return self._get_proxies().uric_acid

    @property
    def remnant_cholesterol(self) -> Optional[float]:
        return self._get_lipid().remnant_cholesterol

    @property
    def fat_free_mass(self) -> Optional[float]:
        return self._get_anthro().fat_free_mass

    @property
    def ideal_body_weight(self) -> Optional[float]:
        return self._get_anthro().ideal_body_weight

    @property
    def pulse_pressure(self) -> Optional[float]:
        return self._get_hemodynamics().pulse_pressure

    @property
    def mean_arterial_pressure(self) -> Optional[float]:
        return self._get_hemodynamics().mean_arterial_pressure

    @property
    def tyg_bmi(self) -> Optional[float]:
        return self._get_metabolic().tyg_bmi

    @property
    def aip(self) -> Optional[float]:
        return self._get_lipid().aip

    @property
    def castelli_index_i(self) -> Optional[float]:
        return self._get_lipid().castelli_index_i

    @property
    def castelli_index_ii(self) -> Optional[float]:
        return self._get_lipid().castelli_index_ii

    @property
    def apob_apoa1_ratio(self) -> Optional[float]:
        return self._get_lipid().apob_apoa1_ratio

    @property
    def non_hdl_cholesterol(self) -> Optional[float]:
        return self._get_lipid().non_hdl_cholesterol

    @property
    def ace_score(self) -> Optional[int]:
        return self._get_context().ace_score
