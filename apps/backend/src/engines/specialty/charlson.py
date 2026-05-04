from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class CharlsonMotor(BaseClinicalMotor):
    """
    Charlson Comorbidity Index (CCI) — 10-year mortality predictor.

    Weights 19 conditions by their association with 10-year mortality.
    Score 0: 10y survival ~98%
    Score 1-2: 10y survival ~86%
    Score 3-4: 10y survival ~77%
    Score 5-6: 10y survival ~53%
    Score >=7: 10y survival ~21%

    Charlson et al., 1987. Updated 2011 (ICD-10).

    This motor maps ICD-10 codes from encounter.conditions to CCI weights.

    REQUIREMENT_ID: CHARLSON-CCI
    """

    REQUIREMENT_ID = "CHARLSON-CCI"

    ICD10_MAP = {
        "I21": 1,
        "I22": 1,
        "I25": 1,
        "I50": 1,
        "I63": 1,
        "I64": 1,
        "G45": 1,
        "J44": 1,
        "J43": 1,
        "J42": 1,
        "J41": 1,
        "M05": 1,
        "M06": 1,
        "M31.5": 1,
        "M32": 1,
        "M33": 1,
        "M34": 1,
        "K70": 1,
        "K71": 1,
        "K73": 1,
        "K74": 1,
        "K76.0": 1,
        "E10": 1,
        "E11": 1,
        "N18.3": 2,
        "N18.4": 3,
        "N18.5": 4,
        "N18.6": 6,
        "C00-C75": 2,
        "B20": 6,
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.conditions:
            return False, "No conditions coded. CCI requires ICD-10 conditions."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        score = 0
        conditions_found = []

        for cond in encounter.conditions:
            code = cond.code.upper()
            for icd_pattern, weight in self.ICD10_MAP.items():
                if code.startswith(icd_pattern.replace("-", "")) or code == icd_pattern:
                    score += weight
                    conditions_found.append(f"{code} (+{weight})")
                    break

        if score == 0:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Charlson CCI: 0 (sin comorbilidades significativas)"
            explanation = "CCI=0. Supervivencia estimada a 10 anos: ~98%."
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif score <= 2:
            estado = "PROBABLE_WARNING"
            verdict = f"Charlson CCI: {score} (comorbilidad leve-moderada)"
            explanation = (
                f"CCI={score}. Supervivencia estimada a 10 anos: ~86%. "
                f"Condiciones: {', '.join(conditions_found)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif score <= 4:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Charlson CCI: {score} (comorbilidad moderada-alta)"
            explanation = (
                f"CCI={score}. Supervivencia estimada a 10 anos: ~77%. "
                f"Condiciones: {', '.join(conditions_found)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif score <= 6:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Charlson CCI: {score} (comorbilidad alta)"
            explanation = (
                f"CCI={score}. Supervivencia estimada a 10 anos: ~53%. "
                f"Condiciones: {', '.join(conditions_found)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Charlson CCI: {score} (comorbilidad muy alta)"
            explanation = (
                f"CCI={score}. Supervivencia estimada a 10 anos: ~21%. "
                f"Condiciones: {', '.join(conditions_found)}"
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="CHARLSON-CCI",
                    value=score,
                    threshold="0",
                    display="Charlson Comorbidity Index",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={"cci_score": score, "conditions": conditions_found},
        )
