from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

class EndocrinePrecisionMotor(BaseClinicalMotor):
    """
    Thyroid and Adrenal (Cushing) screening.
    """

    REQUIREMENT_ID = "ENDOCRINE-PRECISION"
    CODES = {
        "TSH": "11579-0",
        "FT4": "FT4-001",
        "FT3": "FT3-001",
        "RT3": "RT3-001",
        "SHBG": "SHBG-001",
        "CORTISOL_AM": "CORT-AM"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Needs at least TSH and FT4 for basic thyroid vision
        if not encounter.get_observation(self.CODES["TSH"]) and \
           not encounter.get_observation(self.CODES["FT4"]):
            return False, "Missing core thyroid markers (TSH/FT4)"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        tsh = encounter.get_observation(self.CODES["TSH"])
        ft4 = encounter.get_observation(self.CODES["FT4"])
        ft3 = encounter.get_observation(self.CODES["FT3"])
        rt3 = encounter.get_observation(self.CODES["RT3"])
        shbg = encounter.get_observation(self.CODES["SHBG"])
        cort = encounter.get_observation(self.CODES["CORTISOL_AM"])
        
        findings = []
        evidence = []
        
        # 1. Clasificación Tiroidea Estándar
        if tsh:
            if tsh.value > 4.5:
                if ft4 and ft4.value < 0.8:
                    findings.append("Hipotiroidismo Primario Franco")
                else:
                    findings.append("Hipotiroidismo Subclínico")
                evidence.append(ClinicalEvidence(type="Observation", code="TSH", value=tsh.value, display="TSH", threshold=">4.5"))

        # 2. Visión 360: Conversión y Efecto Tisular
        if ft3 and rt3 and rt3.value > 0:
            ratio = ft3.value / rt3.value
            # Ajuste de threshold: 0.10 es más sensible para detectar falla de deiodinación 
            if ratio < 0.10: 
                findings.append("Disfunción de Conversión T4->T3 (rT3 elevado)")
                evidence.append(ClinicalEvidence(type="Calculation", code="FT3/rT3", value=round(ratio, 4), display="Ratio T3/rT3", threshold="<0.10"))

        if shbg:
            findings.append(f"Efecto Tisular Periférico (SHBG: {shbg.value} nmol/L)")
            evidence.append(ClinicalEvidence(type="Observation", code="SHBG", value=shbg.value, display="SHBG (marcador tisular)"))

        # 3. Adrenal Screen
        if cort and cort.value > 20: # High AM Cortisol
            findings.append("Hipercortisolismo Matutino (Sugerido)")
            evidence.append(ClinicalEvidence(type="Observation", code="CORT-AM", value=cort.value, threshold=">20"))

        return AdjudicationResult(
            calculated_value=" | ".join(findings) if findings else "Balance Endocrino Normal",
            confidence=0.9,
            evidence=evidence
        )
