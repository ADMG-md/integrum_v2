from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import List

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class AnthropometryPrecisionMotor(BaseClinicalMotor):
    """
    Motor especializado en la interpretación de antropometría avanzada.
    Analiza la distribución de grasa y riesgo cardiometabólico mediante variables subrogadas.

    Evidence:
    - WHtR > 0.5: Browning et al., 2010. Obesity Reviews 11(8): 545-555.
    - WHR: WHO STEPwise approach, 2008.
    - BRI: Thomas et al., 2013. PLoS ONE 8(1): e53100.

    REQUIREMENT_ID: ANTHRO-PRECISION
    """

    REQUIREMENT_ID = "ANTHRO-PRECISION"

    def validate(self, encounter: Encounter) -> List:
        # Require at least Waist and Height for basic indices
        waist = encounter.get_observation("WAIST-001")
        height = encounter.get_observation("8302-2")
        if not waist or not height:
            return False, "Se requiere Cintura y Talla para el análisis antropométrico."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        findings = []
        evidence = []

        # 1. Ratio Cintura/Altura (WHtR) - El 'Termómetro' de Riesgo
        whtr = encounter.waist_to_height
        if whtr:
            if whtr > 0.5:
                findings.append(
                    f"Aumento de Riesgo Cardiometabólico (WHtR {round(whtr, 2)})"
                )
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="WHtR",
                    value=round(whtr, 2),
                    display="R. Cintura/Altura",
                    threshold=">0.5",
                )
            )

        # 2. Ratio Cintura/Cadera (WHR) - Fenotipo de Distribución
        whr = encounter.waist_to_hip
        if whr:
            # Umbrales simplificados (M > 0.90, F > 0.85)
            is_male = encounter.metadata.get("sex", "").lower() == "male"
            threshold = 0.90 if is_male else 0.85
            if whr > threshold:
                findings.append("Fenotipo de Distribución Androide (Grasa Central)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="WHR",
                    value=round(whr, 2),
                    display="R. Cintura/Cadera",
                    threshold=f">{threshold}",
                )
            )

        # 3. BRI (Body Roundness Index)
        bri = encounter.body_roundness_index
        if bri:
            if bri > 5:
                findings.append("Elevada Adiposidad Visceral Estrecha (BRI)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="BRI",
                    value=round(bri, 2),
                    display="Body Roundness Index",
                    threshold=">5",
                )
            )

        # Síntesis
        status = (
            "Distribución de Grasa de Alto Riesgo"
            if any("Riesgo" in f or "Androide" in f for f in findings)
            else "Composición Antropométrica de Bajo Riesgo"
        )

        explanation = "Análisis de distribución de grasa: " + (
            "; ".join(findings)
            if findings
            else "Métricas dentro de límites de bajo riesgo."
        )

        return AdjudicationResult(
            calculated_value=status,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.VALIDATED_BIOMARKER] if whtr and whr else 0.7,
            evidence=evidence,
            explanation=explanation,
        )
