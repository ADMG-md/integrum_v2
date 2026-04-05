from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple, List
import math

class LipidRiskPrecisionMotor(BaseClinicalMotor):
    """
    Motor de Riesgo Cardiovascular y Lípidos (Guías ACC/AHA 2026).
    Implementa metas de LDL-C basadas en riesgo y análisis de Colesterol Remanente.
    """
    
    CODES = {
        "LDL": "18262-6",
        "TOTAL_CHOL": "2093-3",
        "HDL": "2085-9",
        "TRIGLY": "2571-8",
        "SBP": "8480-6",
        "CREA": "2160-0",
        "AGE": "AGE-001"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.get_observation(self.CODES["LDL"]) or not encounter.get_observation(self.CODES["TOTAL_CHOL"]):
            return False, "Se requiere Perfil Lipídico (LDL, Col. Total) para auditoría de riesgo."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        ldl = float(encounter.get_observation(self.CODES["LDL"]).value)
        remnant = encounter.remnant_cholesterol
        egfr = encounter.egfr_ckd_epi
        
        findings = []
        evidence = []
        
        # 1. Determinación de Riesgo PREVENT (Aproximación por Criterios Clínicos 2026)
        # En una versión real, aquí se usarían los coeficientes completos de PREVENT.
        # Por ahora, usamos los "Risk Enhancers" definidos en la guía.
        risk_level = "Intermedio" # Default for analysis
        
        is_very_high_risk = False
        if encounter.has_condition("I25.1") or encounter.has_condition("I21"): # CAD / MI
            is_very_high_risk = True
            risk_level = "Muy Alto"
        elif egfr and egfr < 60:
            risk_level = "Alto (ERC)"
        
        # 2. Adjudicación de Meta LDL (Target v2026)
        target = 100
        if is_very_high_risk:
            target = 55
        elif risk_level == "Alto (ERC)":
            target = 70
        
        if ldl > target:
            findings.append(f"LDL fuera de meta (Meta <{target} mg/dL para riesgo {risk_level})")
        else:
            findings.append(f"LDL en meta óptima (<{target} mg/dL)")

        # 3. Colesterol Remanente (Aterogénesis Oculta)
        if remnant and remnant > 30:
            findings.append(f"Elevado Colesterol Remanente ({round(remnant, 1)} mg/dL)")
            explanation = "Riesgo cardiovascular residual por partículas ricas en triglicéridos."
        else:
            explanation = "Perfil lipídico evaluado bajo estándares ACC/AHA 2026."

        evidence.append(ClinicalEvidence(type="Observation", code="LDL", value=ldl, display="LDL-C", threshold=f"<{target}"))
        if remnant:
            evidence.append(ClinicalEvidence(type="Calculation", code="Remnant-C", value=round(remnant, 1), display="Col. Remanente", threshold="<30"))

        return AdjudicationResult(
            calculated_value=f"Riesgo {risk_level} | LDL Target: {target}",
            confidence=0.85,
            evidence=evidence,
            explanation=" | ".join(findings)
        )
