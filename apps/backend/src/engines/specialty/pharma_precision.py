from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence, ActionItem, MedicationGap
from typing import Tuple, List, Optional

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel

class PharmaPrecisionMotor(BaseClinicalMotor):
    """
    Master Pharmacological Prescriber V2.
    Balanced for Safety (Sarcopenia/Hard Stops) and Precision (Phenotype/Organ Benefit).
    """
    REQUIREMENT_ID = "PHARMA-PRECISION-2026-V2"
    
    # Clinical Thresholds (with citations)
    SMI_MALE_SARCOPENIA_THRESHOLD = 7.0  # EWGSOP2
    GRIP_STRENGTH_FRAILTY_THRESHOLD = 26.0 # kg
    TFEQ_PHENOTYPE_THRESHOLD = 2.5 # Scale 1-4

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.bmi:
            return False, "Skipping Pharma Precision: Missing BMI."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence = []
        action_checklist = []
        critical_omissions = []
        
        # --- 0. ESTADO MUSCULAR (MODIFICADOR DE RIESGO DE SEGURIDAD) ---
        height_obs = encounter.get_observation("8302-2")
        muscle_obs = encounter.get_observation("BIA-MUSCLE-KG") or encounter.get_observation("MMA-001")
        grip_obs = encounter.get_observation("GRIP-STR-R")
        
        smi = None
        if muscle_obs and height_obs:
            h_m = float(height_obs.value) / 100
            smi = float(muscle_obs.value) / (h_m * h_m)

        is_sarcopenic = False
        is_muscle_at_risk = False
        
        if smi and smi < self.SMI_MALE_SARCOPENIA_THRESHOLD:
            is_sarcopenic = True
        if grip_obs and float(grip_obs.value) < self.GRIP_STRENGTH_FRAILTY_THRESHOLD:
            is_muscle_at_risk = True

        # --- 1. SEGURIDAD (HARD STOPS) ---
        has_ic = encounter.history.has_heart_failure if hasattr(encounter.history, "has_heart_failure") else False
        if has_ic:
            evidence.append(ClinicalEvidence(type="History", code="HF-DETECTED", value="Positive", display="Insuficiencia Cardíaca Detectada"))

        has_mtc = encounter.history.has_history_medullary_thyroid_carcinoma if hasattr(encounter.history, "has_history_medullary_thyroid_carcinoma") else False
        if has_mtc:
            critical_omissions.append(MedicationGap(
                drug_class="Agonistas GLP-1 / Duales",
                gap_type="CONTRAINDICATED",
                severity="critical",
                clinical_rationale="Contraindicación absoluta: Historia de Cáncer Medular de Tiroides / MEN2."
            ))

        # --- 2. BENEFICIO DE ÓRGANO (CARDIO-RENAL-METABÓLICO) ---
        egfr = encounter.egfr_ckd_epi
        uacr = encounter.uacr
        has_metabolic_priority = False
        
        if (egfr and egfr < 60) or (uacr and uacr >= 30) or has_ic:
            has_metabolic_priority = True
            action_checklist.append(ActionItem(
                category="pharmacological", priority="high",
                task="Priorizar iSGLT2 (Dapagliflozina / Empagliflozina)",
                rationale=f"Perfil Cardiorrenal detectado (eGFR: {egfr if egfr else 'N/A'}, Albuminuria: {uacr if uacr else 'N/A'}). Protección de órgano diana mandataria."
            ))
            evidence.append(ClinicalEvidence(type="Metabolic", code="CARDIORENAL-BENEFIT", value="High", display="Prioridad de Protección Renal/CV"))

        # --- 3. SELECCIÓN POR FENOTIPO (EL CEREBRO DEL TRATAMIENTO) ---
        tfeq_unc = encounter.get_observation("TFEQ-UNCONTROLLED")
        tfeq_emo = encounter.get_observation("TFEQ-EMOTIONAL")
        st = encounter.get_observation("ST-001")
        bmi = encounter.bmi

        # A. Fenotipo Central (GLP-1/GIP) - Con MODIFICADOR MUSCULAR
        bmi_ok = bmi is not None and (bmi >= 30 or (bmi >= 27 and has_metabolic_priority))
        if bmi_ok or (tfeq_unc and float(tfeq_unc.value) >= self.TFEQ_PHENOTYPE_THRESHOLD):
            
            if is_sarcopenic or is_muscle_at_risk:
                action_checklist.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Precaución: GLP-1/GIP con Vigilancia de Masa Magra",
                    rationale="Estado muscular comprometido (Sarcopenia/Fragilidad detectada). Si se inicia terapia incretínica (Semaglutida/Tirzepatida), es obligatorio asegurar ingesta de proteína ≥1.5g/kg y entrenamiento de fuerza para evitar deterioro funcional."
                ))
            else:
                action_checklist.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Considerar Agonista GLP-1 / GIP (Liraglutida / Semaglutida / Tirzepatida)",
                    rationale="Indicación por IMC + Comorbilidad / Fenotipo Hungry Brain. Máxima eficacia en control de peso y beneficio metabólico."
                ))
            
            evidence.append(ClinicalEvidence(type="Phenotype", code="INCRETIN-CANDIDATE", value=True, display="Candidato a Terapia Incretínica"))
[diff_block_start]
        # B. Fenotipo Emocional / Hedónico
        if tfeq_emo and float(tfeq_emo.value) >= self.TFEQ_PHENOTYPE_THRESHOLD:
            action_checklist.append(ActionItem(
                category="referral", priority="high",
                task="Priorizar Abordaje de Comida Emocional (Psiconutrición)",
                rationale="Fenotipo Emocional detectado (TFEQ-Emotional). El éxito farmacológico es limitado sin manejo conductual concurrente. Considerar Naltrexona/Bupropión (en formulación magistral o separada si disponible)."
            ))

        # C. Fenotipo Hungry Gut (Vaciado Gástrico)
        if st and float(st.value) > 0:
            action_checklist.append(ActionItem(
                category="pharmacological", priority="medium",
                task="Optimizar timing de comidas y Fibra Viscosa",
                rationale="Fenotipo Hungry Gut. Considerar Liraglutida (impacto en vaciado) o adición de fibra viscosa (psyllium/glucomanano) para prolongar saciedad posprandial."
            ))

        # --- 4. AJUSTE DE DOSIS Y SEGURIDAD METABÓLICA ---
        if egfr and egfr < 45 and egfr >= 30:
            action_checklist.append(ActionItem(
                category="pharmacological", priority="medium",
                task="Limitación de Metformina (Max 1000mg/día)",
                rationale=f"Disfunción renal Estadio G3b (eGFR: {egfr:.1f})."
            ))

        status = "CONFIRMED_ACTIVE"
        if critical_omissions:
            status = "PROBABLE_WARNING"

        return AdjudicationResult(
            calculated_value="Perfil de Prescripción de Precisión",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED],
            evidence=evidence,
            estado_ui=status,
            requirement_id=self.REQUIREMENT_ID,
            action_checklist=action_checklist,
            critical_omissions=critical_omissions,
            explanation=f"Recomendación balanceada. Sarcopenia: {is_sarcopenic}. Prioridad Metabólica: {has_metabolic_priority}."
        )
