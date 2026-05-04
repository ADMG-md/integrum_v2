from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple
import math


class FreeTestosteroneMotor(BaseClinicalMotor):
    """
    Free Testosterone Calculator — Vermeulen Method (1999).

    Calculates bioavailable and free testosterone from:
    - Total testosterone
    - SHBG
    - Albumin

    Free T is more clinically relevant than total T,
    especially in obesity where SHBG is often low.

    Vermeulen et al., 1999. J Clin Endocrinol Metab.

    REQUIREMENT_ID: FREE-TESTO-VERMEULEN
    """

    REQUIREMENT_ID = "FREE-TESTO-VERMEULEN"

    KA_SHBG = 1.0e9
    KA_ALB = 3.6e4
    ALBUMIN_G_L_DEFAULT = 43.0

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        testo_obs = encounter.get_observation("TESTO-001")
        testo_panel = encounter.metabolic_panel.testosterone_total_ng_dl
        shbg = encounter.metabolic_panel.shbg_nmol_l
        testo = safe_float(testo_obs.value) if testo_obs else testo_panel
        if not testo or not shbg:
            return False, "Free T requires: Total Testosterone and SHBG."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        testo_obs = encounter.get_observation("TESTO-001")
        testo_panel = encounter.metabolic_panel.testosterone_total_ng_dl
        total_t_ng_dl = safe_float(testo_obs.value) if testo_obs else testo_panel
        shbg = encounter.metabolic_panel.shbg_nmol_l
        albumin_g_dl = (
            encounter.metabolic_panel.albumin_g_dl or self.ALBUMIN_G_L_DEFAULT / 10
        )

        if total_t_ng_dl is None or shbg is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes.",
            )

        total_t_nmol = total_t_ng_dl * 0.0347
        albumin_mol = (albumin_g_dl * 10) / 69000

        # Vermeulen quadratic solution for free testosterone
        # (T) = (-b + sqrt(b^2 - 4ac)) / 2a
        # where a = KA_SHBG, b = 1 + KA_SHBG*SHBG + KA_ALB*Alb - KA_SHBG*T
        # Simplified: free T is the small root

        ka_shbg = self.KA_SHBG
        ka_alb = self.KA_ALB

        b = 1 + ka_shbg * shbg + ka_alb * albumin_mol - ka_shbg * total_t_nmol
        c = -ka_shbg * total_t_nmol

        free_t_nmol = (-b + math.sqrt(b * b - 4 * ka_shbg * c)) / (2 * ka_shbg)
        free_t_pg_ml = free_t_nmol * 288.4

        # Bioavailable = free + albumin-bound
        bioavailable_nmol = free_t_nmol * (1 + ka_alb * albumin_mol)
        bioavailable_t_ng_dl = bioavailable_nmol * 28.84

        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]

        if is_male:
            free_t_low = free_t_pg_ml < 50
            ref_range = "50-210 pg/mL"
        else:
            free_t_low = free_t_pg_ml < 7
            ref_range = "7-10 pg/mL"

        free_t_rounded = round(free_t_pg_ml, 1)

        if free_t_low:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Testosterona libre BAJA ({free_t_rounded} pg/mL)"
            explanation = (
                f"Free T: {free_t_rounded} pg/mL (ref: {ref_range}). "
                f"Bioavailable T: {round(bioavailable_t_ng_dl, 1)} ng/dL. "
                f"Total T: {total_t_ng_dl} ng/dL, SHBG: {shbg} nmol/L."
            )
            confidence = CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]  # Vermeulen method
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = f"Testosterona libre dentro de rango ({free_t_rounded} pg/mL)"
            explanation = (
                f"Free T: {free_t_rounded} pg/mL (ref: {ref_range}). "
                f"Bioavailable T: {round(bioavailable_t_ng_dl, 1)} ng/dL."
            )
            confidence = CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="FREE-T",
                    value=free_t_rounded,
                    threshold=ref_range,
                    display="Free Testosterone (Vermeulen)",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "free_t_pg_ml": free_t_rounded,
                "bioavailable_t_ng_dl": round(bioavailable_t_ng_dl, 1),
                "total_t_ng_dl": total_t_ng_dl,
                "shbg": shbg,
                "is_male": is_male,
            },
        )
