from pydantic import BaseModel, Field
from typing import List, Tuple, Any, Literal, Optional, TYPE_CHECKING, Dict
from src.engines.base_models import AdjudicationResult, ClinicalEvidence

if TYPE_CHECKING:
    from src.engines.domain import Encounter

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel

class PhenoAgeLevineInput(BaseModel):
    chronological_age_years: float
    albumin_g_dl: float
    creatinine_mg_dl: float
    glucose_mg_dl: float
    hs_crp_mg_l: float
    lymphocyte_percent: float
    mcv_fl: float
    rdw_percent: float
    alkaline_phosphatase_u_l: float
    wbc_k_ul: float

class PhenoAgeLevineOutput(AdjudicationResult):
    # R-05 Fix (H-007): Explicit status field replaces silent fallback
    status: Literal["ok", "error"] = "ok"
    biological_age_years: Optional[float] = None
    age_delta_years: Optional[float] = None
    mortality_score_10y: Optional[float] = None
    optimal_recommendations: List[str] = []
    
    # Overriding calculated_value and explanation as they are in AdjudicationResult
    calculated_value: str = "" 
    explanation: str = ""

class BiologicalAgeMotor:
    ENGINE_NAME = "PhenoAgeLevineMotor"
    ENGINE_VERSION = "0.2.0"
    REQUIREMENT_ID = "LEVINE-2018"  # DOI: 10.18632/aging.101414 (PhenoAge epigenetic clock)

    def get_version_hash(self) -> str:
        return "0.2.0"
  # Bumped for R-05 safety fix

    def validate(self, encounter: "Encounter") -> Tuple[bool, str]:
        # facultative check: run if we have at least 2 markers (e.g. Glucose + Albumin)
        # to show the user what is missing for a precision clock.
        markers_found = 0
        mp = encounter.metabolic_panel
        if mp.glucose_mg_dl: markers_found += 1
        if mp.albumin_g_dl: markers_found += 1
        if mp.hs_crp_mg_l: markers_found += 1
        
        if markers_found < 1:
            return False, "No bioage markers present."
        return True, ""

    def __call__(self, data: PhenoAgeLevineInput) -> PhenoAgeLevineOutput:
        # Wrapper for existing DTO-based calls
        return self._execute_calculation(data)

    def run(self, encounter: "Encounter", context: Dict[str, Any] = None) -> PhenoAgeLevineOutput:
        """Standardized interface (Mission 12 Hardening)"""
        return self.compute(encounter)

    def compute(self, encounter: "Encounter") -> PhenoAgeLevineOutput:
        # Extraction logic moved from domain.py to here for autonomy
        mp = encounter.metabolic_panel
        d = encounter.demographics
        
        required = {
            "chronological_age_years": d.age_years,
            "albumin_g_dl": mp.albumin_g_dl,
            "creatinine_mg_dl": mp.creatinine_mg_dl,
            "glucose_mg_dl": mp.glucose_mg_dl,
            "hs_crp_mg_l": mp.hs_crp_mg_l,
            "lymphocyte_percent": mp.lymphocyte_percent,
            "mcv_fl": mp.mcv_fl,
            "rdw_percent": mp.rdw_percent,
            "alkaline_phosphatase_u_l": mp.alkaline_phosphatase_u_l,
            "wbc_k_ul": mp.wbc_k_ul,
        }
        
        missing = [k for k, v in required.items() if v is None]
        
        if missing:
            return PhenoAgeLevineOutput(
                status="error",
                confidence=0.0,
                calculated_value="Reloj Incompleto",
                explanation=f"Faltan {len(missing)} biomarcadores facultativos para activar el Reloj Biológico PhenoAge.",
                dato_faltante=", ".join(missing),
                estado_ui="INDETERMINATE_LOCKED",
                evidence=[]
            )

        # All present, build DTO and execute
        input_dto = PhenoAgeLevineInput(**required)
        return self._execute_calculation(input_dto)

    def _execute_calculation(self, data: PhenoAgeLevineInput) -> PhenoAgeLevineOutput:
        try:
            bioage, mort_score = self._compute_phenoage_levine(data)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            # R-05 Fix: NEVER fall back to chronological age silently.
            return PhenoAgeLevineOutput(
                status="error",
                biological_age_years=None,
                age_delta_years=None,
                mortality_score_10y=None,
                confidence=0.0,
                calculated_value="ERROR_CALCULATION",
                explanation=(
                    f"Error en cálculo de PhenoAge (Levine 2018): {type(e).__name__}. "
                    f"Edad biológica marcada como INDETERMINATE. "
                ),
                optimal_recommendations=[],
                estado_ui="INDETERMINATE_LOCKED",
                evidence=[]
            )

        delta = bioage - data.chronological_age_years
        recs = self._build_optimal_recommendations(data)
        explanation = (
            f"PhenoAge calculada usando fórmula de Levine et al. 2018 "
            f"(9 biomarcadores sanguíneos + edad). ΔBioAge={delta:.1f} años."
        )
        return PhenoAgeLevineOutput(
            status="ok",
            biological_age_years=round(bioage, 1),
            age_delta_years=round(delta, 1),
            mortality_score_10y=round(mort_score, 3),
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.INDIRECT_EVIDENCE],
            calculated_value=f"PhenoAge: {round(bioage,1)}y",
            explanation=explanation,
            optimal_recommendations=recs,
            estado_ui="CONFIRMED_ACTIVE",
            evidence=[
                ClinicalEvidence(type="Observation", code="ALB-001", value=data.albumin_g_dl, display="Albumin"),
                ClinicalEvidence(type="Observation", code="2339-0", value=data.glucose_mg_dl, display="Glucose"),
                ClinicalEvidence(type="Observation", code="HS-CRP-001", value=data.hs_crp_mg_l, display="hs-CRP"),
            ]
        )

    def _compute_phenoage_levine(self, d: PhenoAgeLevineInput) -> Tuple[float, float]:
        """
        Implementation of the Levine (2018) PhenoAge Algorithm.
        Based on: 10.18632/aging.101414 (Corrected Supplement Constants)
        """
        import math
        
        # 1. SI Conversions for Regression
        age = d.chronological_age_years
        alb = d.albumin_g_dl * 10        # g/dL to g/L
        cre = d.creatinine_mg_dl * 88.42 # mg/dL to umol/L
        glu = d.glucose_mg_dl * 0.0555    # mg/dL to mmol/L
        crp = d.hs_crp_mg_l              # already in mg/L
        lym = d.lymphocyte_percent
        mcv = d.mcv_fl
        rdw = d.rdw_percent
        alp = d.alkaline_phosphatase_u_l
        wbc = d.wbc_k_ul

        # 2. Linear Predictor (xb) - Levine 2018 Elastic Net Coefficients
        # Reference Table S3 (NHANES III Training)
        # P0-6: CRP=0.0 is analytically valid (no detectable inflammation) but
        # math.log(0) = -inf which silently corrupts the Gompertz CDF.
        # Floor at 0.01 mg/L — below detection limit of any clinical analyzer.
        # SOURCE: Levine 2018 R implementation uses log(CRP) with CRP in mg/L.
        crp_safe = max(crp, 0.01)
        xb = -19.907 + \
             (-0.0336 * alb) + \
             (0.0095 * cre) + \
             (0.1953 * glu) + \
             (0.0954 * math.log(crp_safe)) + \
             (-0.0120 * lym) + \
             (0.0268 * mcv) + \
             (0.3306 * rdw) + \
             (0.0019 * alp) + \
             (0.0554 * wbc) + \
             (0.0804 * age)

        # 3. 10-Year Mortality Probability (Gompertz CDF)
        gamma = 0.0076927
        t = 120 # 120 months (10 years) following Levine R implementation
        factor = (math.exp(gamma * t) - 1) / gamma
        
        # Survival S = exp(-exp(xb) * factor)
        s_10 = math.exp(-math.exp(xb) * factor)
        mortality_score = 1 - s_10

        # 4. Final Biological Age Transformation
        # Using Corrected Table S6 Constants from "An epigenetic biomarker of aging..."
        # PhenoAge = 141.50225 + ln(-0.00553 * ln(S_10)) / 0.09165
        #
        # R-05: This is the critical calculation. If it fails due to extreme
        # inputs (e.g., S_10 <= 0 or S_10 >= 1), we MUST propagate the error
        # upward instead of silently returning chronological age.
        pheno_age = 141.50225 + math.log(-0.00553 * math.log(s_10)) / 0.09165
            
        return pheno_age, mortality_score

    def _build_optimal_recommendations(self, d: PhenoAgeLevineInput) -> List[str]:
        recs: List[str] = []
        if d.hs_crp_mg_l > 3.0:
            recs.append("Inflamación de bajo grado detectada; considerar evaluación metabólica.")
        if d.rdw_percent > 14.5:
            recs.append("RDW elevado; marcador inespecífico de fragilidad/inflamación.")
        return recs
