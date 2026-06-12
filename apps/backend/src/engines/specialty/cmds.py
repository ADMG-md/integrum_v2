"""
CMDSStagingMotor — Cardiometabolic Disease Staging Motor
Calculates CMDS Stage (E0-E4) based on 5 components of Metabolic Syndrome and chronic conditions.

REQUIREMENT_ID: CMDS-STAGING
SOURCE: ALAD (Waist), ATP III / AHA (MetS adapted)
"""

from typing import Tuple, List, Optional
from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel

# Simple fuzzy matchers for drug classes
BP_DRUG_KEYWORDS = [
    "pril", "sartan", "dipina", "dipine", "tiazida", "thiazide", "furosemida", 
    "furosemide", "lol", "clonidina", "clonidine", "espironolactona", "spironolactone",
    "amlodipino", "enalapril", "losartan", "valsartan", "hidroclorotiazida"
]

TG_DRUG_KEYWORDS = [
    "fibrato", "fibrate", "gemfibrozil", "fenofibrato", "omega", "epa", "dha",
    "icosapento", "vascepa", "lovaza", "omacor"
]

def _is_taking_bp_med(encounter: Encounter) -> bool:
    for med in encounter.medications:
        if not med.is_active:
            continue
        name_lower = med.name.lower()
        if any(kw in name_lower for kw in BP_DRUG_KEYWORDS):
            return True
    return False

def _is_taking_tg_med(encounter: Encounter) -> bool:
    for med in encounter.medications:
        if not med.is_active:
            continue
        name_lower = med.name.lower()
        if any(kw in name_lower for kw in TG_DRUG_KEYWORDS):
            return True
    return False


class CMDSStagingMotor(BaseClinicalMotor):
    """
    Cardiometabolic Disease Staging Motor (CMDS_v0.1).
    Stages E0 to E4 based on 5 risk components (Waist, BP, Glu, TG, HDL).
    Runs parallel to EOSS.
    """

    REQUIREMENT_ID = "CMDS-STAGING"
    ENGINE_NAME = "CMDSStagingMotor"
    ENGINE_VERSION = "0.1.0"

    def get_version_hash(self) -> str:
        return f"{self.ENGINE_NAME}-v{self.ENGINE_VERSION}"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence: List[ClinicalEvidence] = []
        
        # 1. Inputs
        gender = encounter.demographics.gender
        waist_obs = encounter.get_observation("ANTHRO-004")
        waist_cm = safe_float(waist_obs.value) if waist_obs else None
        
        sbp_obs = encounter.get_observation("BP-001")
        dbp_obs = encounter.get_observation("BP-002")
        sbp = safe_float(sbp_obs.value) if sbp_obs else None
        dbp = safe_float(dbp_obs.value) if dbp_obs else None
        
        glucose = encounter.glucose_mg_dl
        hba1c = encounter.hba1c
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        hdl = encounter.metabolic_panel.hdl_mg_dl
        egfr = encounter.egfr_ckd_epi
        
        has_dm2 = encounter.has_condition("E11") or (encounter.history and encounter.history.has_type2_diabetes)
        
        # CVD check
        # Looking for I20-I25 (Ischemic heart disease) or I60-I69 (Cerebrovascular) in condition codes
        has_cvd = False
        if encounter.history and (encounter.history.has_coronary_disease or encounter.history.has_stroke or encounter.history.has_heart_failure):
            has_cvd = True
        for cond in encounter.conditions:
            code = cond.code.upper()
            if code.startswith("I2") or code.startswith("I6") or code.startswith("I50"):
                has_cvd = True
                
        is_taking_bp = _is_taking_bp_med(encounter)
        is_taking_tg = _is_taking_tg_med(encounter)
        
        # 2. Compute SM Components
        missing_components = []
        
        # SM_waist
        sm_waist: Optional[int] = None
        if waist_cm is not None and gender is not None:
            if gender == "male":
                sm_waist = 1 if waist_cm >= 90 else 0
            elif gender == "female":
                sm_waist = 1 if waist_cm >= 80 else 0
        else:
            missing_components.append("Waist")
            
        # SM_bp
        sm_bp: Optional[int] = None
        if is_taking_bp:
            sm_bp = 1
        elif sbp is not None and dbp is not None:
            sm_bp = 1 if (sbp >= 130 or dbp >= 85) else 0
        elif sbp is not None:
            sm_bp = 1 if sbp >= 130 else 0
        elif dbp is not None:
            sm_bp = 1 if dbp >= 85 else 0
        else:
            missing_components.append("BP")

        # SM_glu (only if NOT DM2)
        sm_glu: Optional[int] = None
        if has_dm2:
            sm_glu = 0
        elif glucose is not None or hba1c is not None:
            sm_glu = 0
            if glucose is not None and 100 <= glucose <= 125:
                sm_glu = 1
            if hba1c is not None and 5.7 <= hba1c <= 6.4:
                sm_glu = 1
        else:
            missing_components.append("Glucose/HbA1c")
            
        # SM_tg
        sm_tg: Optional[int] = None
        if is_taking_tg:
            sm_tg = 1
        elif tg is not None:
            sm_tg = 1 if tg >= 150 else 0
        else:
            missing_components.append("Triglycerides")
            
        # SM_hdl
        sm_hdl: Optional[int] = None
        if hdl is not None and gender is not None:
            if gender == "male":
                sm_hdl = 1 if hdl < 40 else 0
            elif gender == "female":
                sm_hdl = 1 if hdl < 50 else 0
        else:
            missing_components.append("HDL")
            
        # SM_count
        sm_components = [v for v in [sm_waist, sm_bp, sm_glu, sm_tg, sm_hdl] if v is not None]
        sm_count = sum(sm_components)
        
        # 3. Determine completeness
        completeness_status = "complete"
        if len(missing_components) == 5:
            # If all components are missing, and no DM2/CVD, we might be indeterminate
            # But DM2/CVD can still trigger E4 regardless of missing labs.
            if not has_dm2 and not has_cvd and egfr is None and glucose is None and hba1c is None:
                completeness_status = "indeterminate"
            else:
                completeness_status = "partial"
        elif len(missing_components) > 0:
            completeness_status = "partial"
            
        # E4 Check
        is_e4 = False
        if has_dm2:
            is_e4 = True
            evidence.append(ClinicalEvidence(type="Condition", code="E11", value="DM2", display="Diabetes Mellitus Tipo 2 detectada"))
        if not is_e4 and glucose is not None and glucose >= 126:
            is_e4 = True
            evidence.append(ClinicalEvidence(type="Lab", code="GLUCOSE", value=glucose, display=f"Glucosa ≥ 126 ({glucose})"))
        if not is_e4 and hba1c is not None and hba1c >= 6.5:
            is_e4 = True
            evidence.append(ClinicalEvidence(type="Lab", code="HBA1C", value=hba1c, display=f"HbA1c ≥ 6.5% ({hba1c})"))
        if not is_e4 and has_cvd:
            is_e4 = True
            evidence.append(ClinicalEvidence(type="Condition", code="CVD", value="CVD", display="Enfermedad Cardiovascular Establecida"))
        if not is_e4 and egfr is not None and egfr < 30:
            is_e4 = True
            evidence.append(ClinicalEvidence(type="Lab", code="EGFR", value=egfr, display=f"eGFR < 30 ({egfr})"))
            
        # E3 Check
        is_e3 = False
        if not is_e4:
            if egfr is not None and 30 <= egfr <= 59:
                is_e3 = True
                evidence.append(ClinicalEvidence(type="Lab", code="EGFR", value=egfr, display=f"eGFR 30-59 ({egfr})"))
            elif sm_count >= 3 and sm_glu == 1:
                is_e3 = True
                evidence.append(ClinicalEvidence(type="Composite", code="SM", value=sm_count, display=f"SM count={sm_count} + Prediabetes"))
                
        # E2 Check
        is_e2 = False
        if not is_e4 and not is_e3:
            if sm_count >= 3:
                is_e2 = True
                evidence.append(ClinicalEvidence(type="Composite", code="SM", value=sm_count, display=f"SM count={sm_count}"))
            elif sm_glu == 1: # isolated prediabetes
                is_e2 = True
                evidence.append(ClinicalEvidence(type="Lab", code="GLUCOSE_HBA1C", value=sm_glu, display="Prediabetes aislada"))
                
        # E1 Check
        is_e1 = False
        if not is_e4 and not is_e3 and not is_e2:
            if sm_count in (1, 2):
                is_e1 = True
                evidence.append(ClinicalEvidence(type="Composite", code="SM", value=sm_count, display=f"SM count={sm_count}"))
                
        # E0 Check
        is_e0 = False
        if not is_e4 and not is_e3 and not is_e2 and not is_e1:
            if completeness_status == "complete":
                # strict E0
                if sm_count == 0 and (glucose is not None and glucose < 100) and (hba1c is not None and hba1c < 5.7) and (egfr is not None and egfr >= 90):
                    is_e0 = True
                    evidence.append(ClinicalEvidence(type="Composite", code="SM", value=0, display="0 risk factors, healthy"))
                else:
                    # technically should be E0 if partial but no risks found?
                    # let's be conservative: if complete and zero, it's E0.
                    pass
            if sm_count == 0 and not has_dm2 and not has_cvd:
                 # if partial but zero risks found, we can assign E0 provisionally
                 is_e0 = True
                 evidence.append(ClinicalEvidence(type="Composite", code="SM", value=0, display="0 detected risk factors"))

        # Final Assignment
        if is_e4:
            stage = "Stage 4"
            estado_ui = "CONFIRMED_ACTIVE"
        elif is_e3:
            stage = "Stage 3"
            estado_ui = "CONFIRMED_ACTIVE"
        elif is_e2:
            stage = "Stage 2"
            estado_ui = "PROBABLE_WARNING"
        elif is_e1:
            stage = "Stage 1"
            estado_ui = "PROBABLE_WARNING"
        elif is_e0:
            stage = "Stage 0"
            estado_ui = "NORMAL_CLEAR"
        else:
            stage = "Indeterminate"
            estado_ui = "INDETERMINATE_LOCKED"
            
        if completeness_status == "indeterminate":
            stage = "Indeterminate"
            estado_ui = "INDETERMINATE_LOCKED"
            
        metadata = {
            "sm_waist": sm_waist,
            "sm_bp": sm_bp,
            "sm_glu": sm_glu,
            "sm_tg": sm_tg,
            "sm_hdl": sm_hdl,
            "sm_count": sm_count,
            "missing_components": missing_components,
            "completeness_status": completeness_status
        }
        
        return AdjudicationResult(
            calculated_value=stage,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE] if completeness_status == "complete" else CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER],
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado_ui,
            metadata=metadata,
            dato_faltante=", ".join(missing_components) if missing_components else None
        )
