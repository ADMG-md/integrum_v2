from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class PulsePressureMotor(BaseClinicalMotor):
    """
    Pulse Pressure (PP) and Mean Arterial Pressure (MAP) assessment.

    PP = SBP - DBP. PP > 60 mmHg = independent CVD risk factor (>50 years).
    MAP = DBP + 1/3(PP). MAP < 65 = organ hypoperfusion risk.

    Wide pulse pressure reflects arterial stiffness and is an
    independent predictor of cardiovascular events, especially
    in patients over 50.

    Evidence:
    - Domanski et al., 1999. JAMA 281(11): 1007-1012.
      PP is an independent predictor of CVD mortality in >300,000 patients.
    - Franklin et al., 1999. Hypertension 33(1): 374-380.
      PP > 60 mmHg is the best BP predictor of CVD in adults > 50 years.
    - Rivers et al., 2002. Crit Care Med 30(6): S186-S191.
      MAP < 65 mmHg threshold for organ perfusion in sepsis (adopted broadly).

    REQUIREMENT_ID: PP-HEMODYNAMIC
    """

    REQUIREMENT_ID = "PP-HEMODYNAMIC"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        sbp = encounter.get_observation("8480-6")
        dbp = encounter.get_observation("8462-4")
        if not sbp or not dbp:
            return False, "Pulse Pressure requires: SBP and DBP."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        pp = encounter.pulse_pressure
        map_val = encounter.mean_arterial_pressure

        if pp is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes para calcular presion de pulso.",
            )

        findings = []
        evidence = [
            ClinicalEvidence(
                type="Calculation",
                code="PP",
                value=pp,
                threshold="<60",
                display="Pulse Pressure",
            )
        ]

        if pp > 60:
            findings.append(f"Presion de pulso amplia ({pp} mmHg) = rigidez arterial")
            estado = "CONFIRMED_ACTIVE"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]
        elif pp > 50:
            findings.append(f"Presion de pulso limtrofe ({pp} mmHg)")
            estado = "PROBABLE_WARNING"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]
        else:
            estado = "INDETERMINATE_LOCKED"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]

        if map_val is not None:
            evidence.append(
                ClinicalEvidence(
                    type="Calculation",
                    code="MAP",
                    value=map_val,
                    threshold=">=65",
                    display="Mean Arterial Pressure",
                )
            )
            if map_val < 65:
                findings.append(f"MAP baja ({map_val} mmHg) = riesgo de hipoperfusion")

        verdict = f"PP: {pp} mmHg"
        if map_val is not None:
            verdict += f", MAP: {map_val} mmHg"

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation="; ".join(findings)
            if findings
            else "Presion de pulso dentro de rango normal.",
            metadata={"pulse_pressure": pp, "map": map_val},
        )
