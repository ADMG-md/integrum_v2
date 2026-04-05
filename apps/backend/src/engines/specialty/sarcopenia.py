from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, Observation, AdjudicationResult, ClinicalEvidence
from typing import List, Optional

class SarcopeniaPrecisionMotor(BaseClinicalMotor):
    """
    Sarcopenia Detection Motor.
    Calculates ASMI and flags critical muscle loss as a Hard Stop 
    for GLP-1/GIP therapy.
    """
    
    def validate(self, encounter: Encounter):
        muscle_obs = encounter.get_observation("BIA-MUSCLE-KG")
        height_obs = encounter.get_observation("8302-2")
        
        if not muscle_obs or not height_obs:
            return False, "Faltan datos de Bioimpedancia (Masa Muscular) o Talla."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        muscle_kg = float(encounter.get_observation("BIA-MUSCLE-KG").value)
        height_cm = float(encounter.get_observation("8302-2").value)
        is_male = encounter.metadata.get("sex", "M").upper() in ["M", "MALE"]
        
        # ASMI Calculation
        height_m = height_cm / 100
        asmi = (muscle_kg * 0.75) / (height_m ** 2)
        
        # Renal Safety Check (The Auditor's Pushback)
        egfr = encounter.egfr_ckd_epi
        renal_warning = ""
        if egfr and egfr < 45:
            renal_warning = " [!] PRECAUCIÓN: eGFR < 45. Ajustar aporte proteico según función renal."
        
        # Thresholds
        is_severe = (is_male and asmi < 7.0) or (not is_male and asmi < 5.5)
        is_at_risk = (is_male and asmi < 7.5) or (not is_male and asmi < 6.0)
        
        status = "NORMAL"
        explanation = f"Masa muscular conservada (ASMI: {asmi:.1f} kg/m²).{renal_warning}"
        evidence = [
            ClinicalEvidence(type="Observation", code="ASMI", value=round(asmi, 2), display="Índice de Masa Apendicular")
        ]
        
        if is_severe:
            status = "CONTRAINDICACIÓN: SARCOPENIA SEVERA"
            explanation = f"¡ALERTA DE SEGURIDAD! ASMI crítico ({asmi:.1f} kg/m²). Riesgo de fragilidad extrema con análogos GLP-1.{renal_warning}"
        elif is_at_risk:
            status = "RIESGO DE SARCOPENIA"
            explanation = f"Masa muscular limítrofe ({asmi:.1f} kg/m²). Titular GLP-1 con cautela extrema.{renal_warning}"
            
        return AdjudicationResult(
            calculated_value=status,
            explanation=explanation,
            confidence=0.90,
            evidence=evidence
        )
