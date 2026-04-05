from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple


class BodyCompositionTrendMotor(BaseClinicalMotor):
    """
    Body Composition Trend Engine — Lean Mass Loss Rate During Therapy.

    Tracks the proportion of weight loss that comes from lean tissue vs fat.
    Critical during GLP-1/GIP therapy where rapid weight loss can cause
    excessive muscle loss (sarcopenic obesity).

    Thresholds:
    - <15% of weight loss as lean mass: Acceptable
    - 15-25%: Moderate concern — increase protein, add resistance training
    - >25%: High concern — consider dose reduction, intensive intervention

    Based on:
    - Wilding et al., 2021 (STEP 1 trial — semaglutide body composition)
    - Jastreboff et al., 2022 (SURMOUNT-1 — tirzepatide body composition)
    - EWGSOP2 2019 (sarcopenia criteria)

    REQUIREMENT_ID: BODY-COMP-TREND
    """

    REQUIREMENT_ID = "BODY-COMP-TREND"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        prev_weight = encounter.metadata.get("prev_weight_kg")
        prev_muscle = encounter.metadata.get("prev_muscle_mass_kg")
        if not prev_weight or not prev_muscle:
            return False, (
                "BodyCompositionTrend requires: prev_weight_kg and "
                "prev_muscle_mass_kg in encounter metadata."
            )
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        prev_weight = encounter.metadata["prev_weight_kg"]
        prev_muscle = encounter.metadata["prev_muscle_mass_kg"]

        w_obs = encounter.get_observation("29463-7")
        current_weight = safe_float(w_obs.value) if w_obs else None

        mm_obs = encounter.get_observation("MMA-001") or encounter.get_observation(
            "MUSCLE-KG"
        )
        current_muscle = safe_float(mm_obs.value) if mm_obs else None

        if not current_weight or not current_muscle:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Se requieren peso actual y masa muscular actual.",
            )

        weight_delta = prev_weight - current_weight
        muscle_delta = prev_muscle - current_muscle

        if weight_delta <= 0:
            return AdjudicationResult(
                calculated_value="Sin pérdida de peso detectada",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation=f"Peso actual ({current_weight:.1f}kg) >= previo ({prev_weight:.1f}kg).",
            )

        # Calculate lean mass loss as percentage of total weight loss
        lean_loss_pct = (muscle_delta / weight_delta) * 100 if weight_delta > 0 else 0
        lean_loss_pct = round(lean_loss_pct, 1)

        weight_loss_pct = ((prev_weight - current_weight) / prev_weight) * 100
        weight_loss_pct = round(weight_loss_pct, 1)

        findings = []
        actions = []

        if lean_loss_pct > 25:
            estado = "CONFIRMED_ACTIVE"
            verdict = (
                f"Pérdida excesiva de masa magra ({lean_loss_pct}% del peso perdido)"
            )
            findings.append(
                f"ALERTA: {lean_loss_pct}% de la pérdida de peso es masa magra "
                f"(umbral: >25%)"
            )
            findings.append(
                f"Peso: {prev_weight:.1f} → {current_weight:.1f} kg "
                f"({weight_loss_pct}% pérdida total)"
            )
            findings.append(
                f"Masa muscular: {prev_muscle:.1f} → {current_muscle:.1f} kg "
                f"({muscle_delta:.1f} kg pérdida)"
            )
            actions.append(
                ActionItem(
                    category="lifestyle",
                    priority="critical",
                    task="Aumentar ingesta proteica a 1.2-1.5 g/kg/día + entrenamiento de resistencia",
                    rationale=f"{lean_loss_pct}% de pérdida es masa magra. Riesgo de sarcopenia.",
                )
            )
            actions.append(
                ActionItem(
                    category="pharmacological",
                    priority="high",
                    task="Considerar reducción de dosis de GLP-1/GIP",
                    rationale="Pérdida excesiva de masa magra sugiere dosis demasiado agresiva.",
                )
            )
            confidence = 0.90
        elif lean_loss_pct > 15:
            estado = "PROBABLE_WARNING"
            verdict = (
                f"Pérdida moderada de masa magra ({lean_loss_pct}% del peso perdido)"
            )
            findings.append(
                f"{lean_loss_pct}% de la pérdida de peso es masa magra "
                f"(umbral de preocupación: >15%)"
            )
            findings.append(
                f"Peso: {prev_weight:.1f} → {current_weight:.1f} kg "
                f"({weight_loss_pct}% pérdida total)"
            )
            actions.append(
                ActionItem(
                    category="lifestyle",
                    priority="high",
                    task="Aumentar ingesta proteica a 1.0-1.2 g/kg/día + ejercicio de fuerza",
                    rationale=f"{lean_loss_pct}% de pérdida es masa magra.",
                )
            )
            confidence = 0.85
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = f"Composición corporal aceptable ({lean_loss_pct}% masa magra)"
            findings.append(
                f"Solo {lean_loss_pct}% de la pérdida de peso es masa magra "
                f"(aceptable: <15%)"
            )
            confidence = 0.88

        explanation = "; ".join(findings)

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="LEAN-LOSS-PCT",
                    value=lean_loss_pct,
                    threshold="<15%",
                    display="Porcentaje de Masa Magra Perdida",
                ),
                ClinicalEvidence(
                    type="Calculation",
                    code="WEIGHT-LOSS-PCT",
                    value=weight_loss_pct,
                    threshold="0.5-1.0 kg/week",
                    display="Porcentaje de Pérdida de Peso Total",
                ),
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "lean_loss_pct": lean_loss_pct,
                "weight_loss_pct": weight_loss_pct,
                "weight_delta_kg": round(weight_delta, 1),
                "muscle_delta_kg": round(muscle_delta, 1),
                "prev_weight_kg": prev_weight,
                "current_weight_kg": current_weight,
                "prev_muscle_kg": prev_muscle,
                "current_muscle_kg": current_muscle,
            },
        )
