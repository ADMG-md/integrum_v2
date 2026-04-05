from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

class HypertensionSecondaryMotor(BaseClinicalMotor):
    """
    Screens for secondary causes of hypertension (e.g., Primary Aldosteronism).
    """
    REQUIREMENT_ID = "HTN-SEC-2024"
    CODES = {
        "ALDOSTERONE": "1762-0",
        "RENIN": "2889-4",
        "SYSTOLIC_BP": "8480-6",
        "HTN_CONDITION": "I10"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Active if patient has HTN or high BP reading
        has_htn = encounter.has_condition(self.CODES["HTN_CONDITION"])
        bp = encounter.get_observation(self.CODES["SYSTOLIC_BP"])
        has_high_bp = bp and bp.value >= 140
        
        if not (has_htn or has_high_bp):
            return False, "Patient is not hypertensive"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        aldo = encounter.get_observation(self.CODES["ALDOSTERONE"])
        renin = encounter.get_observation(self.CODES["RENIN"])
        
        confidence = 0.7
        evidence = []
        status = "No secondary HTA screening data"

        if aldo and renin and renin.value > 0:
            arr = aldo.value / renin.value
            if arr > 30 and aldo.value > 15:
                status = "High risk of Primary Aldosteronism (ARR > 30)"
                confidence = 0.9
                evidence.append(ClinicalEvidence(
                    type="Observation",
                    code="ARR",
                    value=round(arr, 2),
                    threshold=">30",
                    display="Aldosterone/Renin Ratio"
                ))
            else:
                status = "Screening for PA: Negative"
        
        return AdjudicationResult(
            calculated_value=status,
            confidence=confidence,
            evidence=evidence
        )
