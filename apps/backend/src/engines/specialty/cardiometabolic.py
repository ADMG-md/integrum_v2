from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple


class CMIMotor(BaseClinicalMotor):
    """
    Cardiometabolic Index (CMI).

    CMI = (Waist / Height) × (TG / HDL)

    Integrates central adiposity + atherogenic dyslipidemia.
    Superior to BMI for CVD risk prediction.

    High CMI: > 0.7 (M) or > 0.5 (F)

    REQUIREMENT_ID: CMI-2015
    """

    REQUIREMENT_ID = "CMI-2015"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        waist = encounter.get_observation("WAIST-001")
        height = encounter.get_observation("8302-2")
        tg = encounter.cardio_panel.triglycerides_mg_dl
        hdl = encounter.cardio_panel.hdl_mg_dl
        if not all([waist, height, tg, hdl]):
            return False, "CMI requires: Waist, Height, TG, HDL."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        waist = safe_float(encounter.get_observation("WAIST-001").value)
        height = safe_float(encounter.get_observation("8302-2").value)
        tg = encounter.cardio_panel.triglycerides_mg_dl
        hdl = encounter.cardio_panel.hdl_mg_dl

        if not all([waist, height, tg, hdl]) or height == 0 or hdl == 0:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes para calcular CMI.",
            )

        cmi = (waist / height) * (tg / hdl)
        cmi = round(cmi, 3)

        threshold = 0.7 if is_male else 0.5
        is_high = cmi > threshold

        if is_high:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Indice Cardiometabolico ELEVADO (CMI > {threshold})"
            explanation = (
                f"CMI: {cmi} (umbral: {threshold}). "
                f"Riesgo cardiometabolico por adiposidad central + dislipidemia."
            )
            confidence = 0.85
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = f"Indice Cardiometabolico dentro de rango"
            explanation = f"CMI: {cmi} (umbral: {threshold})."
            confidence = 0.78

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="CMI",
                    value=cmi,
                    threshold=f"<{threshold}",
                    display="Cardiometabolic Index",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={"cmi": cmi, "threshold": threshold, "is_high": is_high},
        )
