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


class TyGBMIMotor(BaseClinicalMotor):
    """
    TyG-BMI Index with Insulin Resistance Staging.

    TyG-BMI = ln(TG × glucose / 2) × BMI

    Superior to HOMA-IR for IR detection in primary care.
    Validated in >10,000 subjects across multiple ethnicities.

    Staging (sex-specific, from validation studies):
    Male:
      <230: Low IR
      230-260: Moderate IR
      >260: Severe IR
    Female:
      <220: Low IR
      220-250: Moderate IR
      >250: Severe IR

    REQUIREMENT_ID: TYGBMI-STAGING
    """

    REQUIREMENT_ID = "TYGBMI-STAGING"

    THRESHOLDS_MALE = (230, 260)
    THRESHOLDS_FEMALE = (220, 250)

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        glu = encounter.glucose_mg_dl
        bmi = encounter.bmi
        if not all([tg, glu, bmi]):
            return False, "TyG-BMI requires: Triglycerides, Glucose, BMI."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        glu = encounter.glucose_mg_dl
        bmi = encounter.bmi

        if tg is None or glu is None or bmi is None or tg <= 0 or glu <= 0:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes o invalidos.",
            )

        tyg = encounter.tyg_index
        if tyg is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="No se pudo calcular el índice TyG.",
            )

        tyg_bmi = round(tyg * bmi, 2)

        thresholds = self.THRESHOLDS_MALE if is_male else self.THRESHOLDS_FEMALE

        if tyg_bmi < thresholds[0]:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Resistencia a insulina BAJA"
            explanation = f"TyG-BMI: {tyg_bmi} (umbral bajo: <{thresholds[0]})."
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]
        elif tyg_bmi <= thresholds[1]:
            estado = "PROBABLE_WARNING"
            verdict = "Resistencia a insulina MODERADA"
            explanation = (
                f"TyG-BMI: {tyg_bmi} (rango: {thresholds[0]}-{thresholds[1]})."
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Resistencia a insulina SEVERA"
            explanation = (
                f"TyG-BMI: {tyg_bmi} (>{thresholds[1]}). "
                f"Alta probabilidad de IR significativa. "
                f"Considerar metformina si no contraindicada."
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="TYG-BMI",
                    value=tyg_bmi,
                    threshold=f"<{thresholds[0]}",
                    display="TyG-BMI Index",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "tyg_bmi": tyg_bmi,
                "tyg": round(tyg, 3),
                "category": "low"
                if tyg_bmi < thresholds[0]
                else "moderate"
                if tyg_bmi <= thresholds[1]
                else "severe",
                "thresholds": thresholds,
            },
        )
