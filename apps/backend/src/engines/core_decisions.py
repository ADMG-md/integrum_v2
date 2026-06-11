from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence, ActionItem, DecisionContext, ClinicalRecommendation
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple, Dict, Any, List


class CoreClinicalDecisionEngine(BaseClinicalMotor):
    """
    Core Clinical Decision Engine.
    
    Translates abstract phenotypes (Axis A, B, C) via a strictly typed 
    DecisionContext into actionable, mandatory therapeutic decisions.
    
    REQUIREMENT_ID: CD-CORE-001
    """
    REQUIREMENT_ID = "CD-CORE-001"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # This engine validates based on context, not just the raw encounter
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        # Standard interface fallback, ideally this shouldn't be called directly without context
        return self.compute_from_context(encounter, DecisionContext())

    def compute_from_context(self, encounter: Encounter, ctx: DecisionContext) -> AdjudicationResult:
        """
        Computes therapeutic decisions based strictly on the typed DecisionContext.
        """
        recommendations: List[ClinicalRecommendation] = []
        actions: List[ActionItem] = []

        # 1. CD-CAL-01: Caloric Deficit
        if not ctx.can_compute_nutrition:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="DEFICIT_INDETERMINADO",
                domain="nutrition",
                recommendation_type="treatment",
                requirement_id="CD-CAL-01",
                priority="standard",
                status="suppressed",
                depends_on=[],
                trigger_summary=["Falta de clasificación fenotípica (Eje A)"],
                human_readable_basis="Datos insuficientes del Eje A para calcular déficit calórico seguro.",
                suppression_reason="Falta clasificación de fenotipo clínico (Eje A).",
                audit_payload={}
            ))
        elif ctx.is_slow_burn or ctx.has_sarcopenic_risk:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="DEFICIT_MODERADO",
                domain="nutrition",
                recommendation_type="treatment",
                requirement_id="CD-CAL-01",
                priority="high",
                depends_on=["SLOW_BURN", "SARCOPENIC_RISK"],
                trigger_summary=["Quema lenta o riesgo sarcopénico activo"],
                human_readable_basis="El fenotipo metabólico del paciente indica un alto riesgo de catabolismo muscular. Se restringe el déficit calórico a moderado (300-500 kcal) para preservar la masa libre de grasa.",
                evidence_note="Guias de manejo de obesidad sarcopénica.",
                audit_payload={"caloric_deficit_target_kcal": "300-500"}
            ))
        else:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="DEFICIT_AGRESIVO",
                domain="nutrition",
                recommendation_type="treatment",
                requirement_id="CD-CAL-01",
                priority="standard",
                depends_on=["NORMAL_BURN"],
                trigger_summary=["Ausencia de riesgo sarcopénico o quema lenta"],
                human_readable_basis="El paciente no presenta riesgos metabólicos o de composición corporal que contraindiquen un déficit calórico estándar para pérdida de peso activa.",
                audit_payload={"caloric_deficit_target_kcal": "800-1000"}
            ))

        # 2. CD-PRO-01: Protein Distribution
        if not ctx.can_compute_nutrition:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PROTEINA_INDETERMINADA",
                domain="protein",
                recommendation_type="treatment",
                requirement_id="CD-PRO-01",
                priority="standard",
                status="suppressed",
                depends_on=[],
                trigger_summary=["Falta de clasificación fenotípica (Eje A)"],
                human_readable_basis="Datos insuficientes del Eje A para calcular target de proteínas seguro.",
                suppression_reason="Falta clasificación de fenotipo clínico (Eje A).",
                audit_payload={}
            ))
        elif ctx.has_advanced_ckd:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PROTEINA_MODERADA_CKD",
                domain="protein",
                recommendation_type="treatment",
                requirement_id="CD-PRO-01",
                priority="high",
                status="modified",
                superseded_by="PROTEINA_MODERADA_CKD",
                suppression_reason="Enfermedad Renal Crónica Avanzada detectada",
                depends_on=["CKD_ADVANCED"],
                trigger_summary=["ERC avanzada inhibe proteína alta"],
                human_readable_basis="Paciente con ERC avanzada. La carga proteica debe ser ajustada a guías renales, ignorando el requerimiento sarcopénico estándar para evitar toxicidad urémica.",
                audit_payload={"protein_target_g_kg": "0.6-0.8"}
            ))
        elif ctx.is_slow_burn or ctx.has_sarcopenic_risk:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PROTEINA_ALTA",
                domain="protein",
                recommendation_type="treatment",
                requirement_id="CD-PRO-01",
                priority="high",
                depends_on=["SLOW_BURN", "SARCOPENIC_RISK"],
                trigger_summary=["Riesgo sarcopénico eleva requerimiento proteico"],
                human_readable_basis="Para sinergizar con el déficit calórico moderado y evitar pérdida de FFM, se prescribe un objetivo hiperproteico.",
                audit_payload={"protein_target_g_kg": "1.5-2.0"}
            ))
        else:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PROTEINA_ESTANDAR",
                domain="protein",
                recommendation_type="treatment",
                requirement_id="CD-PRO-01",
                priority="standard",
                depends_on=["NORMAL_BURN"],
                trigger_summary=["Requerimiento proteico basal"],
                human_readable_basis="Paciente con metabolismo y composición corporal normal. Requiere carga proteica estándar.",
                audit_payload={"protein_target_g_kg": "1.0-1.2"}
            ))

        # 3. CD-BEH-01: Behavioral Focus
        if not ctx.can_compute_behavioral:
            # We don't emit a suppressed recommendation for behavioral, 
            # we just don't emit behavioral rules.
            pass
        elif ctx.has_active_behavioral_referral:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="MANTENER_CBT",
                domain="behavioral",
                recommendation_type="referral",
                requirement_id="CD-BEH-01",
                priority="standard",
                status="informational",
                depends_on=["ACTIVE_REFERRAL"],
                trigger_summary=["Paciente ya se encuentra en CBT"],
                human_readable_basis="El paciente ya está bajo manejo cognitivo-conductual activo. No es necesaria una nueva derivación, solo mantener adherencia.",
                audit_payload={"action": "Mantener adherencia a CBT"}
            ))
        elif ctx.has_uncontrolled_eating or ctx.has_emotional_eating:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="DERIVACION_CBT",
                domain="behavioral",
                recommendation_type="referral",
                requirement_id="CD-BEH-01",
                priority="high",
                depends_on=["B_UNCONTROLLED", "B_EMOTIONAL"],
                trigger_summary=["Ingesta no controlada o hambre emocional activa"],
                human_readable_basis="Se ha detectado un patrón desadaptativo de ingesta. La derivación temprana a CBT es fundacional para la retención y éxito a largo plazo.",
                audit_payload={"kpi": "Reducción de episodios de atracón"}
            ))

        # 4. CD-PHM-01: Pharmacological Initiation
        # (Requires A and/or B depending on rule, we will just use basic phenotyping presence)
        if not ctx.can_compute_behavioral:
            pass
        elif ctx.has_uncontrolled_eating:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PHARM_CLASS_GLP1",
                domain="pharmacotherapy",
                recommendation_type="treatment",
                requirement_id="CD-PHM-01",
                priority="high",
                depends_on=["B_UNCONTROLLED"],
                trigger_summary=["Fenotipo de ingesta no controlada prioriza incretinas"],
                human_readable_basis="El paciente muestra un perfil clásico de hambre hedónica/homeostática descontrolada. Fenotípicamente, los agonistas GLP-1 son la primera línea recomendada. Sujeto a safety validation.",
                audit_payload={"preferred_class": "GLP-1"}
            ))
        elif ctx.has_emotional_eating and ctx.has_affective_traits:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PHARM_CLASS_BUPROPION_NALTREXONE",
                domain="pharmacotherapy",
                recommendation_type="treatment",
                requirement_id="CD-PHM-01",
                priority="standard",
                depends_on=["B_EMOTIONAL", "B_AFFECT"],
                trigger_summary=["Fenotipo afectivo prioriza naltrexona/bupropión"],
                human_readable_basis="El perfil alimentario del paciente está fuertemente impulsado por rasgos afectivos y emocionales, donde naltrexona/bupropión tiene un rationale superior inicial. Sujeto a safety validation.",
                audit_payload={"preferred_class": "Bupropion/Naltrexone"}
            ))

        # 5. CD-SLP-01: Sleep Hygiene
        if not ctx.can_compute_behavioral:
            pass
        elif ctx.has_clinical_insomnia:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="PRIORIZAR_SUEÑO",
                domain="sleep",
                recommendation_type="sequencing",
                requirement_id="CD-SLP-01",
                priority="critical",
                depends_on=["B_SLEEP"],
                trigger_summary=["Insomnio severo pausa escalamiento farmacológico"],
                human_readable_basis="El insomnio clínico está activo. Se debe priorizar el tratamiento del sueño antes de escalar agentes supresores del apetito, los cuales podrían exacerbar el cuadro o ver disminuida su eficacia por el déficit de sueño.",
                audit_payload={"sequencing_rule": "Hold appetite suppressants"}
            ))

        # 6. CD-RSK-01: Early Failure Risk Rule
        if not ctx.can_compute_risk_rule:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="ALERTA_FRACASO_INDETERMINADA",
                domain="risk",
                recommendation_type="alert",
                requirement_id="CD-RSK-01",
                priority="standard",
                status="suppressed",
                depends_on=[],
                trigger_summary=["Faltan ejes para calcular regla de fracaso"],
                human_readable_basis="Se requiere clasificación completa en los ejes A, B y C para emitir una alerta validada de fracaso temprano.",
                suppression_reason="Faltan inputs A, B o C.",
                audit_payload={}
            ))
        elif ctx.is_slow_burn and ctx.has_uncontrolled_eating and ctx.has_suboptimal_c:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="ALERTA_FRACASO_TEMPRANO_ALTO",
                domain="risk",
                recommendation_type="alert",
                requirement_id="CD-RSK-01",
                priority="critical",
                depends_on=["SLOW_BURN", "B_UNCONTROLLED", "SUBOPTIMAL_C"],
                trigger_summary=["Cruce A+B+C predice estancamiento a 12 semanas"],
                human_readable_basis="La combinación de metabolismo lento (A), falta de control en la ingesta (B) y una pobre respuesta inicial de pérdida de peso (C) indica una altísima probabilidad de fracaso terapéutico a las 12 semanas. Requiere intensificación inmediata del seguimiento.",
                audit_payload={"risk_level": "Alto Riesgo"}
            ))
        elif ctx.has_suboptimal_c:
            recommendations.append(ClinicalRecommendation(
                recommendation_code="ALERTA_FRACASO_TEMPRANO_MODERADO",
                domain="risk",
                recommendation_type="alert",
                requirement_id="CD-RSK-01",
                priority="high",
                depends_on=["SUBOPTIMAL_C"],
                trigger_summary=["Trayectoria de peso C es subóptima"],
                human_readable_basis="Independientemente de la línea base, el paciente no está perdiendo el peso esperado a las 4 semanas. Se debe ajustar el plan preventivamente.",
                audit_payload={"risk_level": "Riesgo Moderado"}
            ))

        return AdjudicationResult(
            calculated_value="Recomendaciones Clínicas Nucleares",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE],
            evidence=[],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="CONFIRMED_ACTIVE",
            explanation="Traducción estructurada de fenotipos A/B/C a recomendaciones trazables bajo esquema FDA CDS.",
            action_checklist=actions,
            metadata={
                "recommendations": [rec.model_dump() for rec in recommendations]
            }
        )
