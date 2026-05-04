import re

with open('apps/backend/src/domain/models.py', 'r') as f:
    content = f.read()

# 1. Replace ClinicalHistory
history_schema_code = """class ClinicalHistory(BaseModel):
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

    has_statin_myalgia: bool = False
    caffeine_anxiety_insomnia: bool = False
    taking_otc_vitd: bool = False
    taking_ppi_chronically: bool = False

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
    
    # Suicide risk gate (FDA Black Box Warning for bupropion)
    phq9_item_9_score: Optional[int] = None
    
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
    has_gynecomastia: bool = False"""

content = re.sub(r'class ClinicalHistory\(BaseModel\):.*?# --- Core Domain Entities ---', history_schema_code + '\n\n\n# --- Core Domain Entities ---', content, flags=re.DOTALL)

# 2. Replace MetabolicPanelSchema and CardioPanelSchema
metabolic_schema_code = """class MetabolicPanelSchema(BaseModel):
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

    from pydantic import model_validator
    @model_validator(mode="after")
    def validate_metabolic_coherence(self) -> "MetabolicPanelSchema":
        tg = self.triglycerides_mg_dl
        hdl = self.hdl_mg_dl
        ldl = self.ldl_mg_dl
        vldl = self.vldl_mg_dl
        total_chol = self.total_cholesterol_mg_dl
        hba1c = self.hba1c_percent
        gluc = self.glucose_mg_dl

        if ldl is not None and total_chol is not None and ldl > total_chol:
            raise ValueError(f"Coherence error: ldl_mg_dl ({ldl}) cannot exceed total_cholesterol_mg_dl ({total_chol}).")
        if tg is not None and vldl is not None and tg < vldl:
            raise ValueError(f"Coherence error: triglycerides_mg_dl ({tg}) cannot be less than vldl_mg_dl ({vldl}).")
        if tg is not None and hba1c is not None and tg > 400:
            raise ValueError(f"Coherence error: triglycerides_mg_dl ({tg}) > 400 invalidates HbA1c.")
        if gluc is not None and hba1c is not None:
            eag = hba1c * 28.7 - 46.7
            if eag > 0 and abs(gluc - eag) > 120:
                raise ValueError(f"Coherence error: glucose_mg_dl ({gluc}) deviates >120 mg/dL from eAG.")
        return self"""

content = re.sub(r'class MetabolicPanelSchema\(BaseModel\):.*?# --- Aggregate Root: Encounter ---', metabolic_schema_code + '\n\n\n# --- Aggregate Root: Encounter ---', content, flags=re.DOTALL)

# 3. Update Encounter to remove cardio_panel
content = re.sub(r'    cardio_panel: CardioPanelSchema\n', '', content)

# 4. Update Encounter pass-through properties
content = content.replace('self.cardio_panel.apob_mg_dl', 'self.metabolic_panel.apob_mg_dl')
content = content.replace('self.cardio_panel.lpa_mg_dl', 'self.metabolic_panel.lpa_mg_dl')

with open('apps/backend/src/domain/models.py', 'w') as f:
    f.write(content)
