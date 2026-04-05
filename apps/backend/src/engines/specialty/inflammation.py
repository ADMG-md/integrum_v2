from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple


class InflammationMotor(BaseClinicalMotor):
    """
    Calculates Meta-Inflammation Score (hs-CRP, NLR).

    Evidence:
    - Pearson et al., 2003. Circulation 107: 363-372.
      AHA/CDC Scientific Statement: hs-CRP risk categories (<1, 1-3, >3 mg/L).
    - Zahorec R, 2001. Bratisl Lek Listy 102(12): 521-524.
      NLR as marker of systemic inflammatory stress. NLR > 2.5 = elevated.
    - de Jager et al., 2013. Atherosclerosis 229(1): 229-235.
      NLR independently predicts CVD events and all-cause mortality.

    REQUIREMENT_ID: INFLAMMATION
    """

    REQUIREMENT_ID = "INFLAMMATION"
    CODES = {
        "HS_CRP": "30522-7",
        "NEUTROPHILS": "26499-4",
        "LYMPHOCYTES": "26474-7",
        "FERRITIN": "2276-4",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.get_observation(self.CODES["HS_CRP"]):
            return False, "Missing hs-CRP for inflammation audit"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        crp = encounter.get_observation(self.CODES["HS_CRP"])
        neu = encounter.get_observation(self.CODES["NEUTROPHILS"])
        lym = encounter.get_observation(self.CODES["LYMPHOCYTES"])

        findings = []
        evidence = []

        # 1. HS-CRP Assessment
        if crp.value > 3.0:
            findings.append("Systemic Meta-inflammation (High risk)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation", code="hs-CRP", value=crp.value, threshold=">3.0"
                )
            )

        # 2. Neutrophil-to-Lymphocyte Ratio (NLR)
        if neu and lym and lym.value > 0:
            nlr = neu.value / lym.value
            if nlr > 2.5:
                findings.append("Elevated NLR (Chronic Inflammatory stress)")
                evidence.append(
                    ClinicalEvidence(
                        type="Observation",
                        code="NLR",
                        value=round(nlr, 2),
                        threshold=">2.5",
                    )
                )

        return AdjudicationResult(
            calculated_value=" | ".join(findings)
            if findings
            else "Low Inflammatory Profile",
            confidence=0.9,
            evidence=evidence,
        )
