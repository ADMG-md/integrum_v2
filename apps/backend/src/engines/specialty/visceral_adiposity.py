from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple


class VAIMotor(BaseClinicalMotor):
    """
    Visceral Adiposity Index (VAI) — Amato et al., 2010.

    Sex-specific formula using waist, BMI, TG, HDL.
    Predicts visceral adipose dysfunction and cardiovascular risk
    independently of BMI.

    Male: (WC / (39.68 + 1.88*BMI)) × (TG / 1.03) × (1.31 / HDL)
    Female: (WC / (36.58 + 1.89*BMI)) × (TG / 0.81) × (1.52 / HDL)

    VAI > 2.0 (M) or > 1.5 (F) = high visceral adiposity dysfunction

    REQUIREMENT_ID: VAI-2010
    """

    REQUIREMENT_ID = "VAI-2010"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        bmi = encounter.bmi
        wc = encounter.get_observation("WAIST-001")
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        hdl = encounter.metabolic_panel.hdl_mg_dl
        if not all([bmi, wc, tg, hdl]):
            return False, "VAI requires: Waist, BMI, Triglycerides, HDL."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        bmi = encounter.bmi
        wc = safe_float(encounter.get_observation("WAIST-001").value)
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        hdl = encounter.metabolic_panel.hdl_mg_dl

        if is_male:
            vai = (wc / (39.68 + 1.88 * bmi)) * (tg / 1.03) * (1.31 / hdl)
            threshold = 2.0
        else:
            vai = (wc / (36.58 + 1.89 * bmi)) * (tg / 0.81) * (1.52 / hdl)
            threshold = 1.5

        vai = round(vai, 2)
        is_high = vai > threshold

        if is_high:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Disfuncion de Adiposidad Visceral (VAI elevado)"
            explanation = (
                f"VAI: {vai} (umbral: {threshold}). "
                f"Indicador de disfuncion del tejido adiposo visceral. "
                f"Riesgo cardiometabolico independiente del BMI."
            )
            confidence = 0.88
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Adiposidad Visceral dentro de rango"
            explanation = (
                f"VAI: {vai} (umbral: {threshold}). Sin disfuncion visceral detectada."
            )
            confidence = 0.80

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="VAI",
                    value=vai,
                    threshold=f"<{threshold}",
                    display="Visceral Adiposity Index",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={"vai": vai, "threshold": threshold, "is_high": is_high},
        )
