from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple
import math


class FLIMotor(BaseClinicalMotor):
    """
    Fatty Liver Index (FLI) — Bedogni et al., 2006.

    Validates >100,000 patients for NAFLD detection.
    FLI = (e^(0.953*log(TG) + 0.139*BMI + 0.718*log(GGT) + 0.053*waist - 15.745)
           / (1 + e^(...))) × 100

    FLI < 30: NAFLD ruled out
    FLI 30-60: Equivocal
    FLI > 60: NAFLD likely

    REQUIREMENT_ID: FLI-2006
    """

    REQUIREMENT_ID = "FLI-2006"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        tg = encounter.cardio_panel.triglycerides_mg_dl
        bmi = encounter.bmi
        ggt_obs = encounter.get_observation("GGT-001")
        ggt = (
            safe_float(ggt_obs.value) if ggt_obs else encounter.metabolic_panel.ggt_u_l
        )
        waist = encounter.get_observation("WAIST-001")
        if not all([tg, bmi, ggt, waist]):
            return False, "FLI requires: Triglycerides, BMI, GGT, Waist circumference."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        tg = encounter.cardio_panel.triglycerides_mg_dl
        bmi = encounter.bmi
        ggt_obs = encounter.get_observation("GGT-001")
        ggt = (
            safe_float(ggt_obs.value) if ggt_obs else encounter.metabolic_panel.ggt_u_l
        )
        waist = safe_float(encounter.get_observation("WAIST-001").value)

        linear = (
            0.953 * math.log(tg)
            + 0.139 * bmi
            + 0.718 * math.log(ggt)
            + 0.053 * waist
            - 15.745
        )
        fli = (math.exp(linear) / (1 + math.exp(linear))) * 100
        fli = round(fli, 1)

        if fli < 30:
            estado = "INDETERMINATE_LOCKED"
            verdict = "NAFLD descartado (FLI < 30)"
            explanation = f"FLI: {fli}. Riesgo bajo de esteatosis hepatica."
            confidence = 0.86
        elif fli <= 60:
            estado = "PROBABLE_WARNING"
            verdict = "NAFLD equivoco (FLI 30-60)"
            explanation = (
                f"FLI: {fli}. Zona gris. Considerar ecografia hepatica o FibroScan."
            )
            confidence = 0.65
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = "NAFLD probable (FLI > 60)"
            explanation = (
                f"FLI: {fli}. Alta probabilidad de esteatosis hepatica. "
                f"Indicada evaluacion de fibrosis (FIB-4, NFS)."
            )
            confidence = 0.84

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="FLI",
                    value=fli,
                    threshold="<30",
                    display="Fatty Liver Index",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "fli": fli,
                "category": "low" if fli < 30 else "equivocal" if fli <= 60 else "high",
            },
        )
