from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class ApoBApoA1Motor(BaseClinicalMotor):
    """
    ApoB/ApoA1 Ratio — Best lipid predictor of CVD (INTERHEART study).

    ApoB reflects total atherogenic particle number.
    ApoA1 reflects reverse cholesterol transport capacity.
    The ratio integrates both sides of the atherogenic equation.

    Thresholds:
    < 0.6: Low risk
    0.6-0.8: Moderate risk
    0.8-1.0: High risk
    > 1.0: Very high risk

    REQUIREMENT_ID: APORATIO-INTERHEART
    """

    REQUIREMENT_ID = "APORATIO-INTERHEART"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        apob = encounter.metabolic_panel.apob_mg_dl
        apoa1 = encounter.metabolic_panel.apoa1_mg_dl
        if not apob or not apoa1:
            return False, "ApoB/ApoA1 requires: ApoB and ApoA1 values."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        apob = encounter.metabolic_panel.apob_mg_dl
        apoa1 = encounter.metabolic_panel.apoa1_mg_dl

        ratio = round(apob / apoa1, 3)

        if ratio < 0.6:
            risk_level = "Bajo"
            estado = "INDETERMINATE_LOCKED"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]
        elif ratio < 0.8:
            risk_level = "Moderado"
            estado = "PROBABLE_WARNING"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]
        elif ratio < 1.0:
            risk_level = "Alto"
            estado = "CONFIRMED_ACTIVE"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]
        else:
            risk_level = "Muy Alto"
            estado = "CONFIRMED_ACTIVE"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER]

        explanation = (
            f"ApoB/ApoA1: {ratio}. Riesgo lipoproteico: {risk_level}. "
            f"(ApoB: {apob}, ApoA1: {apoa1}). "
            f"INTERHEART: mejor predictor lipidico de IAM que LDL-C solo."
        )

        return AdjudicationResult(
            calculated_value=f"Riesgo Lipoproteico: {risk_level}",
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="ApoB/ApoA1",
                    value=ratio,
                    threshold="<0.6",
                    display="ApoB/ApoA1 Ratio",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "ratio": ratio,
                "risk_level": risk_level,
                "apob": apob,
                "apoa1": apoa1,
            },
        )
