from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class FriedFrailtyMotor(BaseClinicalMotor):
    """
    Fried Frailty Phenotype — Fried et al., 2001.

    5 criteria:
    1. Unintentional weight loss (>=5% in past year)
    2. Exhaustion (PHQ-9 items 1-2 or self-reported)
    3. Low grip strength (sex/BMI-specific cutoffs)
    4. Slow gait speed (<=0.8 m/s or 5xSTS >15s)
    5. Low physical activity (<150 min/week)

    0 = Robust
    1-2 = Pre-frail
    3-5 = Frail

    Cardiovascular Health Study, >5000 adults >=65 years.
    Frail patients have 2x hospitalization, 3x falls risk.

    REQUIREMENT_ID: FRIED-FRAILTY
    """

    REQUIREMENT_ID = "FRIED-FRAILTY"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        has_any = (
            encounter.get_observation("GRIP-STR-R")
            or encounter.get_observation("GRIP-STR-L")
            or encounter.get_observation("GAIT-SPEED")
            or encounter.get_observation("5XSTS-SEC")
            or encounter.get_observation("29463-7")
            or encounter.metabolic_panel.glucose_mg_dl is not None
        )
        if not has_any:
            return (
                False,
                "Fried requires at least: grip, gait, weight, or activity data.",
            )
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        criteria = 0
        findings = []

        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]

        # 1. Unintentional weight loss (>=5% if prev_weight available)
        prev_weight = encounter.metadata.get("prev_weight_kg")
        w_obs = encounter.get_observation("29463-7")
        current_weight = safe_float(w_obs.value) if w_obs else None
        if prev_weight and current_weight and prev_weight > 0:
            loss_pct = ((prev_weight - current_weight) / prev_weight) * 100
            if loss_pct >= 5:
                criteria += 1
                findings.append(f"Perdida de peso no intencional ({loss_pct:.1f}%)")

        # 2. Exhaustion (PHQ-9 items 1-2 >= 2, or PHQ-9 total >= 10)
        phq9_obs = encounter.get_observation("PHQ9-SCORE")
        phq9_panel = None
        if hasattr(encounter, "psychometrics") and encounter.psychometrics:
            phq9_panel = encounter.psychometrics.phq9_score
        phq9 = safe_float(phq9_obs.value) if phq9_obs else phq9_panel
        if phq9 is not None and phq9 >= 10:
            criteria += 1
            findings.append(f"Agotamiento (PHQ-9: {phq9})")

        # 3. Low grip strength
        grip_r = encounter.get_observation("GRIP-STR-R")
        grip_l = encounter.get_observation("GRIP-STR-L")
        grip_values = []
        for g in [grip_r, grip_l]:
            if g:
                gv = safe_float(g.value)
                if gv:
                    grip_values.append(gv)
        if grip_values:
            best_grip = max(grip_values)
            # EWGSOP2 cutoffs
            grip_threshold = 27.0 if is_male else 16.0
            if best_grip < grip_threshold:
                criteria += 1
                findings.append(
                    f"Fuerza de presa baja ({best_grip:.1f}kg < {grip_threshold}kg)"
                )

        # 4. Slow gait speed
        gait_obs = encounter.get_observation("GAIT-SPEED")
        if gait_obs:
            gs = safe_float(gait_obs.value)
            if gs is not None and gs <= 0.8:
                criteria += 1
                findings.append(f"Velocidad de marcha lenta ({gs:.2f} m/s)")

        # Alternative: 5xSTS >15s as gait speed proxy
        if not gait_obs:
            sts_obs = encounter.get_observation("5XSTS-SEC")
            if sts_obs:
                sts = safe_float(sts_obs.value)
                if sts is not None and sts > 15:
                    criteria += 1
                    findings.append(f"5xSTS lento ({sts:.1f}s > 15s)")

        # 5. Low physical activity (<150 min/week)
        pa_obs = encounter.get_observation("PA-MIN-WEEK")
        pa_lifestyle = None
        if hasattr(encounter, "lifestyle") and encounter.lifestyle:
            pa_lifestyle = encounter.lifestyle.physical_activity_min_week
        pa = safe_float(pa_obs.value) if pa_obs else pa_lifestyle
        if pa is not None and pa < 150:
            criteria += 1
            findings.append(f"Actividad fisica baja ({pa} min/sem < 150)")

        # Classification
        if criteria >= 3:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Fragilidad confirmada ({criteria}/5 criterios)"
            explanation = (
                f"Fenotipo de Fried: {criteria}/5 criterios positivos. "
                f"Riesgo 2x de hospitalizacion, 3x de caidas. "
                f"Hallazgos: {'; '.join(findings)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif criteria >= 1:
            estado = "PROBABLE_WARNING"
            verdict = f"Pre-fragilidad ({criteria}/5 criterios)"
            explanation = (
                f"Fenotipo de Fried: {criteria}/5 criterios. "
                f"Ventana de oportunidad para intervencion. "
                f"Hallazgos: {'; '.join(findings)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Robusto (0/5 criterios)"
            explanation = "Sin criterios de fragilidad de Fried."
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="FRIED-FRAILTY",
                    value=criteria,
                    threshold="0",
                    display="Fried Frailty Phenotype",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "fried_score": criteria,
                "category": "frail"
                if criteria >= 3
                else "pre-frail"
                if criteria >= 1
                else "robust",
                "findings": findings,
            },
        )
