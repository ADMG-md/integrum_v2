from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
)
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple


class SarcopeniaMonitorMotor(BaseClinicalMotor):
    """
    Sarcopenia & Catabolism Monitor (MISSION 13 / MAESTRO).
    Calculates ASMI and RPL (Rate of Protein Loss).

    R-02 Fix (H-014): Uses appendicular lean mass proxy when DXA/ALM
    is unavailable. The proxy coefficient (0.75) is derived from
    population-level BIA-to-ALM ratios (Kim et al., 2014).
    TODO: Replace with direct ALM measurement when available.
    """

    REQUIREMENT_ID = "EWGSOP-2019"

    # R-02: Proxy coefficient for Total MM → Appendicular Lean Mass
    # Population range: 0.73–0.80 (Kim et al., 2014; Sergi et al., 2015)
    # Conservative midpoint used until site-specific calibration.
    APPENDICULAR_PROXY_COEFF = 0.75

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Needs BIA data (Muscle Mass) and Weight
        mm = encounter.get_observation("MMA-001") or encounter.get_observation(
            "MUSCLE-KG"
        )
        height = encounter.get_observation("8302-2")
        if not mm or not height:
            return False, "Skipping Sarcopenia: Missing Muscle Mass or Height."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence: list[ClinicalEvidence] = []
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]

        # 1. ASMI (Absolute)
        mm_obs = encounter.get_observation("MMA-001") or encounter.get_observation(
            "MUSCLE-KG"
        )
        h_obs = encounter.get_observation("8302-2")

        if not mm_obs or not h_obs:
            return AdjudicationResult(
                calculated_value="ERROR",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Missing muscle mass or height data.",
            )

        mm_total = float(mm_obs.value)
        h_m = float(h_obs.value) / 100

        # R-02 Fix (H-014): Convert total muscle mass to appendicular proxy
        appendicular_mm = mm_total * self.APPENDICULAR_PROXY_COEFF
        asmi = appendicular_mm / (h_m**2)

        threshold = 7.0 if is_male else 5.5
        is_sarcopenic = asmi < threshold

        evidence.append(
            ClinicalEvidence(
                type="Observation",
                code="ASMI",
                value=round(asmi, 2),
                threshold=f">{threshold}",
                display="Índice ASMI",
            )
        )

        # 2. RPL (Rate of Protein Loss) - Dynamic
        # Requires historical data in metadata or previous encounter
        rpl = 0.0
        alerta_roja = False
        prev_mm = encounter.metadata.get("prev_muscle_mass_kg")
        prev_weight = encounter.metadata.get("prev_weight_kg")
        curr_weight = (
            encounter.bmi * ((h_m) ** 2) if encounter.bmi else None
        )  # Proxy or direct

        # Try to get weight from current observation
        weight_obs = encounter.get_observation("29463-7")
        if weight_obs:
            curr_weight = float(weight_obs.value)

        explanation = f"ASMI: {round(asmi, 2)}. "

        if prev_mm is not None and prev_weight is not None and curr_weight is not None:
            delta_weight = prev_weight - curr_weight
            delta_mm = prev_mm - mm_total

            # AUDITOR RULE: Only compute RPL if total weight loss > 2.0 kg
            if delta_weight > 2.0:
                rpl = (delta_mm / delta_weight) * 100
                if rpl > 35:
                    alerta_roja = True

                evidence.append(
                    ClinicalEvidence(
                        type="Calculation",
                        code="RPL",
                        value=round(rpl, 1),
                        threshold="<35%",
                        display="Tasa RPL (%)",
                    )
                )
            else:
                explanation += " (RPL no calculado: pérdida de peso < 2.0 kg)"

        status = "CONFIRMED_ACTIVE"
        if alerta_roja:
            status = "PROBABLE_WARNING"  # Or custom HIGH_ALERT
        elif is_sarcopenic:
            status = "PROBABLE_WARNING"

        if alerta_roja:
            explanation += f"ALERTA ROJA: RPL {round(rpl, 1)}% indica pérdida de peso predominantemente muscular."
        elif is_sarcopenic:
            explanation += "Criterio de Sarcopenia confirmado."
        else:
            explanation += "Masa muscular dentro de rangos de seguridad."

        return AdjudicationResult(
            calculated_value="Sarcopenia Screen"
            if not alerta_roja
            else "ALERTA CATABÓLICA",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE],  # EWGSOP2 criteria
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=status if not alerta_roja else "PROBABLE_WARNING",
            explanation=explanation,
            metadata={"rpl": rpl, "asmi": asmi, "alerta_roja": alerta_roja},
        )
