from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple
import math

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class NFSMotor(BaseClinicalMotor):
    """
    NAFLD Fibrosis Score (NFS) — Angulo et al., 2007.

    Predicts advanced liver fibrosis in NAFLD patients.
    NFS = -1.675 + 0.037*age + 0.094*BMI + 1.13*diabetes
          + 0.99*AST/ALT ratio - 0.013*platelets - 0.66*albumin

    NFS < -1.455: Advanced fibrosis unlikely
    NFS -1.455 to 0.676: Indeterminate
    NFS > 0.676: Advanced fibrosis likely

    Validated in >700 patients with biopsy-proven NAFLD.
    NPV 93% for ruling out advanced fibrosis.

    REQUIREMENT_ID: NFS-2007
    """

    REQUIREMENT_ID = "NFS-2007"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        age = encounter.get_observation("AGE-001")
        bmi = encounter.bmi
        ast = encounter.get_observation("AST-001") or encounter.metabolic_panel.ast_u_l
        alt = encounter.get_observation("ALT-001") or encounter.metabolic_panel.alt_u_l
        plt = (
            encounter.get_observation("PLT-001")
            or encounter.metabolic_panel.platelets_k_u_l
        )
        albumin = encounter.metabolic_panel.albumin_g_dl

        if not all([age, bmi, ast, alt, plt, albumin]):
            return False, ("NFS requires: Age, BMI, AST, ALT, Platelets, Albumin.")
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        age_obs = encounter.get_observation("AGE-001")
        age = safe_float(age_obs.value) if age_obs else encounter.demographics.age_years
        bmi = encounter.bmi
        ast_obs = encounter.get_observation("AST-001")
        ast_val = (
            safe_float(ast_obs.value) if ast_obs else encounter.metabolic_panel.ast_u_l
        )
        alt_obs = encounter.get_observation("ALT-001")
        alt_val = (
            safe_float(alt_obs.value) if alt_obs else encounter.metabolic_panel.alt_u_l
        )
        plt_obs = encounter.get_observation("PLT-001")
        plt_val = (
            safe_float(plt_obs.value)
            if plt_obs
            else encounter.metabolic_panel.platelets_k_u_l
        )
        albumin = encounter.metabolic_panel.albumin_g_dl

        if not all([age, bmi, ast_val, alt_val, plt_val, albumin]) or alt_val == 0:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes para calcular NFS.",
            )

        # NFS Formula Coefficients (Angulo et al., 2007)
        INTERCEPT = -1.675
        COEFF_AGE = 0.037
        COEFF_BMI = 0.094
        COEFF_DM = 1.13
        COEFF_AST_ALT = 0.99
        COEFF_PLT = 0.013
        COEFF_ALB = 0.66

        nfs = (
            INTERCEPT
            + COEFF_AGE * age
            + COEFF_BMI * bmi
            + (COEFF_DM if has_dm else 0)
            + COEFF_AST_ALT * (ast_val / alt_val)
            - COEFF_PLT * plt_val
            - COEFF_ALB * albumin
        )
        nfs = round(nfs, 3)

        if nfs < -1.455:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Fibrosis hepatica avanzada descartada (NFS bajo)"
            explanation = (
                f"NFS: {nfs}. Baja probabilidad de fibrosis avanzada (NPV 93%)."
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]
        elif nfs <= 0.676:
            estado = "PROBABLE_WARNING"
            verdict = "Fibrosis hepatica indeterminada (NFS zona gris)"
            explanation = (
                f"NFS: {nfs}. Zona indeterminada. "
                f"Considerar elastografia hepatica (FibroScan) o biopsia."
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Fibrosis hepatica avanzada probable (NFS alto)"
            explanation = (
                f"NFS: {nfs}. Alta probabilidad de fibrosis avanzada (F3-F4). "
                f"Indicada referencia a hepatologia y elastografia."
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="NFS",
                    value=nfs,
                    threshold="<-1.455",
                    display="NAFLD Fibrosis Score",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "nfs": nfs,
                "category": "low"
                if nfs < -1.455
                else "indeterminate"
                if nfs <= 0.676
                else "high",
                "has_diabetes": has_dm,
            },
        )
