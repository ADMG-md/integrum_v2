from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class HypertensionSecondaryMotor(BaseClinicalMotor):
    """
    Screens for secondary causes of hypertension (e.g., Primary Aldosteronism).

    Evidence:
    - Funder et al., 2016. JCEM 101(5): 1889-1916.
      Endocrine Society Clinical Practice Guideline for Primary Aldosteronism.
      ARR > 30 (ng/dL per ng/mL/h) + aldosterone > 15 ng/dL = positive screen.
    - Williams et al., 2018. Eur Heart J 39(17): 1531-1556.
      ESC/ESH Guidelines: secondary HTA screening in resistant or early-onset HTN.
    - Prevalence of PA: 5-10% of all hypertensives, up to 20% in resistant HTN.

    REQUIREMENT_ID: HTN-SEC-2024
    """

    REQUIREMENT_ID = "HTN-SEC-2024"
    CODES = {
        "ALDOSTERONE": "1762-0",
        "RENIN": "2889-4",
        "SYSTOLIC_BP": "8480-6",
        "HTN_CONDITION": "I10",
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

        confidence = CONFIDENCE_VALUES[ConfidenceLevel.INDIRECT_EVIDENCE]  # No ARR data
        evidence = []
        status = "No secondary HTA screening data"

        if aldo and renin and renin.value > 0:
            arr = aldo.value / renin.value
            if arr > 30 and aldo.value > 15:
                status = "High risk of Primary Aldosteronism (ARR > 30)"
                confidence = CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]  # Funder et al., 2016
                evidence.append(
                    ClinicalEvidence(
                        type="Observation",
                        code="ARR",
                        value=round(arr, 2),
                        threshold=">30",
                        display="Aldosterone/Renin Ratio",
                    )
                )
            else:
                status = "Screening for PA: Negative"

        return AdjudicationResult(
            calculated_value=status, confidence=confidence, evidence=evidence
        )
