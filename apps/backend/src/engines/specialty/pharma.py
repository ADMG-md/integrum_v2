from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

class PharmacologicalAuditMotor(BaseClinicalMotor):
    """
    Scans for medications that induce weight gain or sabotage metabolism.
    """
    OBESOGENIC_MEDS = {
        "RX-101": "Pregabalin (Neuropathic weight gain)",
        "RX-202": "Prednisone (Glucocorticoid induced weight gain)",
        "RX-303": "Atenolol (Beta-blocker induced metabolism slowing)",
        "RX-404": "Insulin (Anabolic weight gain)"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.medications:
            return False, "No medication statements to audit"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        findings = []
        evidence = []
        
        for med in encounter.medications:
            if med.code in self.OBESOGENIC_MEDS:
                findings.append(self.OBESOGENIC_MEDS[med.code])
                evidence.append(ClinicalEvidence(
                    type="Medication", code=med.code, display=med.name
                ))

        return AdjudicationResult(
            calculated_value="; ".join(findings) if findings else "Obese-Safe: No weight-inducing meds detected",
            confidence=1.0, # Fact-based check
            evidence=evidence
        )
