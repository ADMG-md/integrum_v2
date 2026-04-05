from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple


class PulsePressureMotor(BaseClinicalMotor):
    """
    Pulse Pressure (PP) and Mean Arterial Pressure (MAP) assessment.

    PP = SBP - DBP. PP > 60 mmHg = independent CVD risk factor (>50 years).
    MAP = DBP + 1/3(PP). MAP < 65 = organ hypoperfusion risk.

    Wide pulse pressure reflects arterial stiffness and is an
    independent predictor of cardiovascular events, especially
    in patients over 50.

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
            confidence = 0.85
        elif pp > 50:
            findings.append(f"Presion de pulso limtrofe ({pp} mmHg)")
            estado = "PROBABLE_WARNING"
            confidence = 0.75
        else:
            estado = "INDETERMINATE_LOCKED"
            confidence = 0.80

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
