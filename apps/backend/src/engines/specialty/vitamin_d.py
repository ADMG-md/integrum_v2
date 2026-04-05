from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple


class VitaminDMotor(BaseClinicalMotor):
    """
    Vitamin D (25-OH) Status and Clinical Action Engine.

    >80% of obese patients are deficient.
    Vitamin D affects: bone health, immunity, mood, insulin sensitivity,
    cardiovascular risk, cancer risk.

    Endocrine Society 2011 guidelines:
    <10 ng/mL: Severe deficiency
    10-20 ng/mL: Deficiency
    20-30 ng/mL: Insufficiency
    30-100 ng/mL: Sufficient
    >100 ng/mL: Potential toxicity
    >150 ng/mL: Toxicity

    REQUIREMENT_ID: VITD-STATUS
    """

    REQUIREMENT_ID = "VITD-STATUS"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        vitd_obs = encounter.get_observation("VITD-001")
        vitd_panel = encounter.metabolic_panel.vitamin_d_ng_ml
        if not vitd_obs and not vitd_panel:
            return False, "Vitamin D requires: 25-OH Vitamin D level."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        vitd_obs = encounter.get_observation("VITD-001")
        vitd_panel = encounter.metabolic_panel.vitamin_d_ng_ml

        vitd = None
        if vitd_obs:
            vitd = safe_float(vitd_obs.value)
        elif vitd_panel:
            vitd = vitd_panel

        if vitd is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes.",
            )

        if vitd < 10:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Deficiencia SEVERA de Vitamina D ({vitd} ng/mL)"
            explanation = (
                f"25-OH Vit D: {vitd} ng/mL. Deficiencia severa. "
                f"Indicada suplementacion con 50,000 UI semanal x 8 semanas."
            )
            confidence = 0.95
        elif vitd < 20:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Deficiencia de Vitamina D ({vitd} ng/mL)"
            explanation = (
                f"25-OH Vit D: {vitd} ng/mL. Deficiencia. "
                f"Indicada suplementacion con 2000-4000 UI/dia."
            )
            confidence = 0.92
        elif vitd < 30:
            estado = "PROBABLE_WARNING"
            verdict = f"Insuficiencia de Vitamina D ({vitd} ng/mL)"
            explanation = (
                f"25-OH Vit D: {vitd} ng/mL. Insuficiencia. "
                f"Considerar suplementacion con 1000-2000 UI/dia."
            )
            confidence = 0.88
        elif vitd <= 100:
            estado = "INDETERMINATE_LOCKED"
            verdict = f"Vitamina D suficiente ({vitd} ng/mL)"
            explanation = f"25-OH Vit D: {vitd} ng/mL. Nivel adecuado."
            confidence = 0.90
        elif vitd <= 150:
            estado = "PROBABLE_WARNING"
            verdict = f"Vitamina D elevada ({vitd} ng/mL)"
            explanation = (
                f"25-OH Vit D: {vitd} ng/mL. Nivel elevado. "
                f"Reducir o suspender suplementacion."
            )
            confidence = 0.85
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Posible toxicidad de Vitamina D ({vitd} ng/mL)"
            explanation = (
                f"25-OH Vit D: {vitd} ng/mL. Posible toxicidad. "
                f"Suspender suplementacion. Solicitar calcio serico y PTH."
            )
            confidence = 0.90

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Observation",
                    code="VITD-001",
                    value=vitd,
                    threshold="30-100 ng/mL",
                    display="25-OH Vitamin D",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={"vitd_ng_ml": vitd},
        )
