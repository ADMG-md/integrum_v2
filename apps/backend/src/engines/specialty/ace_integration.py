from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple


class ACEScoreEngine(BaseClinicalMotor):
    """
    ACE Score Clinical Integration Engine.

    The ACE score exists in the data model but was NEVER used by any engine.
    This engine integrates ACE as a clinical modifier across multiple domains:

    ACE >= 4: 2x risk of metabolic disease, 3x risk of depression
    ACE >= 6: 20 year reduction in life expectancy
    ACE >= 8: 3x risk of autoimmune disease

    This engine generates clinical recommendations based on ACE score.

    Felitti et al., 1998 (Kaiser-CDC study).

    REQUIREMENT_ID: ACE-INTEGRATION
    """

    REQUIREMENT_ID = "ACE-INTEGRATION"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        ace = encounter.ace_score
        if ace is None:
            return False, "ACE score not available in clinical history."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        ace = encounter.ace_score
        findings = []
        actions = []

        if ace >= 8:
            findings.append(f"ACE score MUY ALTO ({ace}/10)")
            findings.append("Riesgo 3x de enfermedad autoinmune")
            findings.append("Reduccion estimada de 20 anos en expectativa de vida")
            actions.append(
                ActionItem(
                    category="referral",
                    priority="critical",
                    task="Referir a psicologia/psiquiatria para trauma complejo",
                    rationale=f"ACE={ace}. Trauma severo requiere intervencion especializada.",
                )
            )
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Screening autoinmune ampliado (ANA, TPO, anti-TTG)",
                    rationale="ACE>=8 triplica riesgo de enfermedad autoinmune.",
                )
            )
            estado = "CONFIRMED_ACTIVE"
            confidence = 0.95
        elif ace >= 6:
            findings.append(f"ACE score ALTO ({ace}/10)")
            findings.append("Reduccion estimada de 20 anos en expectativa de vida")
            actions.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task="Evaluar necesidad de terapia de trauma (EMDR, TF-CBT)",
                    rationale=f"ACE={ace}. Impacto significativo en salud a largo plazo.",
                )
            )
            estado = "CONFIRMED_ACTIVE"
            confidence = 0.92
        elif ace >= 4:
            findings.append(f"ACE score MODERADO-ALTO ({ace}/10)")
            findings.append("Riesgo 2x de enfermedad metabolica")
            findings.append("Riesgo 3x de depresion")
            actions.append(
                ActionItem(
                    category="lifestyle",
                    priority="high",
                    task="Integrar evaluacion de trauma en plan de tratamiento",
                    rationale=f"ACE={ace}. El trauma afecta adherencia y respuesta metabolica.",
                )
            )
            estado = "PROBABLE_WARNING"
            confidence = 0.90
        elif ace >= 2:
            findings.append(f"ACE score MODERADO ({ace}/10)")
            findings.append("Riesgo elevado de enfermedad cronica")
            estado = "PROBABLE_WARNING"
            confidence = 0.85
        else:
            findings.append(f"ACE score BAJO ({ace}/10)")
            estado = "INDETERMINATE_LOCKED"
            confidence = 0.80

        explanation = (
            f"ACE Score: {ace}/10. "
            f"El trauma infantil tiene relacion dosis-respuesta con enfermedad metabolica. "
            f"{'; '.join(findings)}"
        )

        return AdjudicationResult(
            calculated_value=f"ACE Score: {ace}/10",
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="ACE-SCORE",
                    value=ace,
                    threshold="<4",
                    display="Adverse Childhood Experiences",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={"ace_score": ace, "findings": findings},
        )
