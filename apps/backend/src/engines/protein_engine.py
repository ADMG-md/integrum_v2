from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple

class ProteinEngineMotor(BaseClinicalMotor):
    """
    Unbiased Protein Engine (MAESTRO V2.2).
    Calculates precision protein targets with Nephro-Shield and Urate-Shield.
    """
    REQUIREMENT_ID = "KDIGO-2024 / PROT-V2"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.fat_free_mass:
            return False, "Skipping Protein Engine: Missing Fat Free Mass (FFM) data."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence = []
        recs = []
        limiters = []
        
        ffm = encounter.fat_free_mass
        ibw = encounter.ideal_body_weight
        egfr = encounter.egfr_ckd_epi
        if not egfr:
            egfr_obs = encounter.get_observation("33914-3")
            if egfr_obs:
                egfr = float(egfr_obs.value)
                
        uacr = encounter.uacr
        uric = encounter.uric_acid
        
        # 1. Base Target Calculation (1.0 - 1.2 g/kg over FFM)
        target_factor = 1.1
        total_protein = ffm * target_factor
        
        # 2. Nephro-Shield (KDIGO 2024 / Auditor Correction)
        renal_risk = False
        if (egfr and egfr < 60) or (uacr and uacr >= 30):
            renal_risk = True
            # AUDITOR RULE: Renal restriction is strictly over IBW to avoid malnutrition or overload
            target_factor = 0.8
            total_protein = ibw * target_factor
            limiters.append(f"ERC / Albuminuria Detectada - Prioridad Renal (0.8g/kg IBW)")
        
        evidence.append(ClinicalEvidence(
            type="Calculation",
            code="FFM",
            value=round(ffm, 1),
            display="Masa Libre de Grasa (kg)"
        ))
        
        if egfr:
            evidence.append(ClinicalEvidence(
                type="Observation",
                code="eGFR",
                value=round(egfr, 1),
                threshold=">60",
                display="Tasa Filtración Glomerular"
            ))

        # 3. Pharmacological Shield (iSGLT2 / ARA2)
        has_isglt2 = encounter.has_medication("ISGLT2") or encounter.has_medication("SGLT2-I")
        has_raas = encounter.has_medication("IECA") or encounter.has_medication("ARA2")
        
        if renal_risk:
            if not has_isglt2:
                recs.append("Iniciar iSGLT2 (Dapagliflozina/Empagliflozina) como escudo renal")
            if not has_raas:
                recs.append("Evaluar inicio de ARA2/IECA para control de albuminuria")

        # 4. Urate-Shield
        calidad = "Estándar"
        if uric and uric > 7.0:
            calidad = "Baja en purinas animales (Hiperuricemia Activa)"
            limiters.append("Ácido Úrico > 7.0 - Modificación de Calidad")

        explanation = (
            f"Objetivo de {round(total_protein, 1)}g de proteína diaria ({target_factor}g/kg FFM). "
            f"Calidad sugerida: {calidad}."
        )

        return AdjudicationResult(
            calculated_value=f"{round(total_protein, 1)}g Prot/Día",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE],  # KDIGO guidelines
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="CONFIRMED_ACTIVE" if not renal_risk else "PROBABLE_WARNING",
            explanation=explanation,
            recomendacion_farmacologica=recs,
            metadata={
                "target_grams": round(total_protein, 1),
                "factor_ffm": target_factor,
                "limitadores": limiters,
                "calidad_sugerida": calidad
            }
        )
