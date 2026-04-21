from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence, ActionItem
from typing import Tuple, List, Dict

class PrecisionNutritionMotor(BaseClinicalMotor):
    """
    Abordaje Nutricional de Precisión basado en Fenotipos (Acosta + Metabólico).
    Traduce señales clínicas (órgano-específicas y psicométricas) en un plan dietario.
    """
    REQUIREMENT_ID = "NUTRITION-PRECISION-2026"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.bmi:
            return False, "Skipping Precision Nutrition: Missing BMI."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence = []
        action_checklist = []
        phenotypes_detected = []
        
        # 1. Hungry Brain (Saciedad Tardía)
        tfeq_unc = encounter.get_observation("TFEQ-UNCONTROLLED")
        is_hungry_brain = False
        if tfeq_unc and float(tfeq_unc.value) >= 2.5:
            is_hungry_brain = True
            phenotypes_detected.append("Hungry Brain")
            evidence.append(ClinicalEvidence(type="Observation", code="TFEQ-UNC", value=tfeq_unc.value, display="Falta de Control (TFEQ)"))
            
            action_checklist.append(ActionItem(
                category="lifestyle", priority="high",
                task="Dieta de Baja Densidad Calórica y Alto Volumen",
                rationale="Fenotipo Hungry Brain detectado. Maximizar saciedad precoz con alta proteína (≥1.6 g/kg) y fibras voluminosas. Evitar buffets."
            ))

        # 2. Hungry Gut (Saciedad Corta)
        st = encounter.get_observation("ST-001")
        is_hungry_gut = False
        if st and float(st.value) > 0:
            is_hungry_gut = True
            phenotypes_detected.append("Hungry Gut")
            evidence.append(ClinicalEvidence(type="Observation", code="ST-001", value=st.value, display="Vaciado Rápido/Hambre Prematura"))
            
            action_checklist.append(ActionItem(
                category="lifestyle", priority="high",
                task="Estructuración de Tiempos + Snacks Proteicos Densos",
                rationale="Fenotipo Hungry Gut. Prolongar curva de saciedad con 3 comidas + 1-2 snacks altos en fibra/proteína. Evitar CHO rápidos aislados."
            ))

        # 3. Emotional / Hedónico
        tfeq_emo = encounter.get_observation("TFEQ-EMOTIONAL")
        gad7 = encounter.get_observation("GAD7-SCORE")
        is_emotional = False
        if (tfeq_emo and float(tfeq_emo.value) >= 2.5) or (gad7 and float(gad7.value) >= 8):
            is_emotional = True
            phenotypes_detected.append("Hedónico / Emocional")
            evidence.append(ClinicalEvidence(type="Psychometric", code="TFEQ-EMO/GAD7", value="Presente", display="Conducta Alimentaria Emocional"))
            
            action_checklist.append(ActionItem(
                category="referral", priority="high",
                task="Psiconutrición y Control de Entorno (TCC/ACT)",
                rationale="Comida no homeostática. Requiere planeación de 'snacks seguros', evitar dietas hiperrestrictivas y manejo de estrés."
            ))

        # 4. IR Hepática (NAFLD-like Profile)
        tg = encounter.cardio_panel.triglycerides_mg_dl if encounter.cardio_panel else None
        alt = encounter.metabolic_panel.alt_u_l if encounter.metabolic_panel else None
        waist_obs = encounter.get_observation("WAIST-001")
        waist = float(waist_obs.value) if waist_obs else 0.0
        is_hepatic_ir = False
        
        hepatic_markers = 0
        if tg and tg >= 150: hepatic_markers += 1
        if alt and alt > 30: hepatic_markers += 1
        if waist and waist > 94: hepatic_markers += 1
        
        if hepatic_markers >= 2:
            is_hepatic_ir = True
            phenotypes_detected.append("Insulino Resistencia Hepática")
            evidence.append(ClinicalEvidence(type="Metabolic", code="HEP-IR", value=f"{hepatic_markers} marcadores", display="Esteatosis / IR Hepática"))
            
            action_checklist.append(ActionItem(
                category="lifestyle", priority="high",
                task="Restricción Severa de Fructosa y CHO Simples",
                rationale="IR Hepática/Visceral dominante. Déficit calórico moderado, patrón mediterráneo (DASH adaptado). Cero jugos/alcohol."
            ))

        # 5. IR Muscular / Slow Burn
        # Proxy: Prediabetes/DM2 + Low Muscle Mass (Sarcopenia risk)
        hba1c = encounter.hba1c
        weight_obs = encounter.get_observation("29463-7")
        height_obs = encounter.get_observation("8302-2")
        muscle_obs = encounter.get_observation("BIA-MUSCLE-KG") or encounter.get_observation("MMA-001")
        
        smi = None
        if muscle_obs and height_obs:
            h_m = float(height_obs.value) / 100
            smi = float(muscle_obs.value) / (h_m * h_m)

        is_muscle_ir = False
        
        if (hba1c and hba1c >= 5.7) and (smi and smi < 7.0):
            is_muscle_ir = True
            phenotypes_detected.append("IR Muscular / Slow Burn")
            evidence.append(ClinicalEvidence(type="Metabolic", code="MUSCLE-IR", value=smi, display="SMI Bajo + Disglucemia"))
            
            action_checklist.append(ActionItem(
                category="lifestyle", priority="high",
                task="Sincronización de CHO post-entrenamiento (Nutrición Deportiva Clínica)",
                rationale="IR Muscular / Bajo Gasto. Sincronizar ingesta de CHO complejos con actividad física. Priorizar densidad proteica. Ejercicio de fuerza obligatorio."
            ))

        if not phenotypes_detected:
            return AdjudicationResult(
                calculated_value="Perfil Nutricional Estándar",
                confidence=1.0,
                estado_ui="CONFIRMED_ACTIVE",
                explanation="No se detectaron sub-fenotipos conductuales o metabólicos dominantes.",
                action_checklist=[ActionItem(
                    category="lifestyle", priority="medium",
                    task="Patrón Mediterráneo Base",
                    rationale="Ausencia de desvíos fenotípicos severos. Mantener balance macronutricional estándar."
                )]
            )

        status = "CONFIRMED_ACTIVE"
        confidence = 0.85
        headline = " + ".join(phenotypes_detected)
        
        return AdjudicationResult(
            calculated_value=headline,
            confidence=confidence,
            evidence=evidence,
            estado_ui=status,
            requirement_id=self.REQUIREMENT_ID,
            action_checklist=action_checklist,
            explanation=f"Se identificaron los siguientes patrones dietarios óptimos: {headline}.",
            metadata={"phenotypes": phenotypes_detected}
        )
