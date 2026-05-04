from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class MetforminB12Motor(BaseClinicalMotor):
    """
    Metformin B12 Deficiency Monitoring Engine.

    Metformin reduces B12 absorption by 20-30% via calcium-dependent
    ileal absorption interference.

    ADA Standards of Care 2024: Annual B12 screening in metformin users.

    B12 deficiency in metformin users:
    - Prevalence: 6-30% depending on dose and duration
    - Risk factors: dose >1500mg/day, duration >4 years, PPI co-use
    - Consequences: neuropathy (masks/worsens diabetic neuropathy),
      anemia, cognitive decline

    REQUIREMENT_ID: METFORMIN-B12
    """

    REQUIREMENT_ID = "METFORMIN-B12"

    METFORMIN_CODES = {
        "METFORMIN",
        "GLUCOPHAGE",
        "METFORMINA",
        "MET-500",
        "MET-850",
        "MET-1000",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        on_metformin = any(
            med.name.upper().replace(" ", "") in self.METFORMIN_CODES
            or med.code in self.METFORMIN_CODES
            for med in encounter.medications
        )
        if not on_metformin:
            return False, "No metformin therapy detected. Skipping B12 monitoring."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        b12_obs = encounter.get_observation("VITB12-001")
        b12_panel = encounter.metabolic_panel.vitamin_b12_pg_ml

        b12 = None
        if b12_obs:
            from src.engines.domain import safe_float

            b12 = safe_float(b12_obs.value)
        elif b12_panel:
            b12 = b12_panel

        findings = []
        actions = []

        if b12 is not None:
            if b12 < 200:
                findings.append(f"Deficiencia de B12 ({b12} pg/mL)")
                actions.append(
                    ActionItem(
                        category="pharmacological",
                        priority="critical",
                        task="Iniciar suplementacion de B12 (cianocobalamina 1000 mcg IM o oral)",
                        rationale=f"B12={b12} pg/mL. Deficiencia confirmada en paciente con metformina.",
                    )
                )
                estado = "CONFIRMED_ACTIVE"
                confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
            elif b12 < 300:
                findings.append(f"B12 limtrofe ({b12} pg/mL)")
                actions.append(
                    ActionItem(
                        category="diagnostic",
                        priority="high",
                        task="Solicitar acido metilmalonico (MMA) y homocisteina para confirmar deficiencia funcional",
                        rationale=f"B12={b12} pg/mL. Nivel limtrofe requiere confirmacion funcional.",
                    )
                )
                estado = "PROBABLE_WARNING"
                confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
            else:
                findings.append(f"B12 adecuado ({b12} pg/mL)")
                estado = "INDETERMINATE_LOCKED"
                confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            findings.append("B12 no disponible")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Solicitar vitamina B12 serica (screening anual obligatorio en metformina)",
                    rationale="ADA recomienda screening anual de B12 en pacientes con metformina.",
                )
            )
            estado = "PROBABLE_WARNING"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        explanation = (
            f"Monitoreo B12 en metformina: {'; '.join(findings)}. "
            f"La metformina reduce absorcion de B12 en 20-30%."
        )

        return AdjudicationResult(
            calculated_value=" | ".join(findings),
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Observation",
                    code="VITB12-001",
                    value=b12 if b12 else "N/A",
                    threshold=">300 pg/mL",
                    display="Vitamina B12",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={"b12_value": b12, "findings": findings},
        )
