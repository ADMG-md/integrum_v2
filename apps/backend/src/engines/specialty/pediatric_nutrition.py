from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple, List, Optional

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class PediatricNutritionMotor(BaseClinicalMotor):
    """
    Recomienda intervenciones nutricionales específicas en poblaciones pediátricas:
    1. Obesidad pediátrica (2-18 años, IMC percentil >= 85)
    2. Trastornos del espectro autista (TEA) con riesgo nutricional
    3. Trastorno por déficit de atención e hiperactividad (TDAH) con alteraciones alimentarias

    Evidence:
    - AAP 2023: Clinical Practice Guideline for Pediatric Obesity
    - USPSTF 2024: Obesity in Children and Adolescents Screening
    - Al-Beltagi 2024: Nutritional management in ASD
    - Rucklidge 2025: Micronutrients in ADHD (Eur Child Adolesc Psychiatry)

    REQUIREMENT_ID: PEDIATRIC-NUTRITION
    """

    REQUIREMENT_ID = "PEDIATRIC-NUTRITION"

    AGE_GROUPS = {
        (0, 2): "toddler",
        (2, 10): "child",
        (10, 18): "adolescent",
    }

    MIN_PEDIATRIC_AGE = 2
    MAX_PEDIATRIC_AGE = 18

    CALORIC_REQUIRMENTS = {
        "toddler": {"min": 1000, "max": 1400},
        "child": {"min": 1200, "max": 1800},
        "adolescent": {"min": 1600, "max": 2400},
    }

    OMEGA3_DOSAGE = {
        "child": {"min": 500, "max": 1000, "unit": "mg EPA+DHA"},
        "adolescent": {"min": 700, "max": 1300, "unit": "mg EPA+DHA"},
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        age = encounter.demographics.age_years if encounter.demographics else None
        if age is not None and (
            age < self.MIN_PEDIATRIC_AGE or age > self.MAX_PEDIATRIC_AGE
        ):
            return False, f"Edad {age} fuera del rango pediátrico (2-18 años)"
        return True, ""

    def _get_age_group(self, age: int) -> Optional[str]:
        for (age_start, age_end), group in self.AGE_GROUPS.items():
            if age_start <= age < age_end:
                return group
        return None

    def _has_diagnosis(self, encounter: Encounter, code_patterns: List[str]) -> bool:
        if not encounter.conditions:
            return False
        for cond in encounter.conditions:
            for pattern in code_patterns:
                if pattern.lower() in cond.code.lower():
                    return True
        return False

    def _has_obesity(self, encounter: Encounter) -> bool:
        if not encounter.conditions:
            return False
        for cond in encounter.conditions:
            if "e66" in cond.code.lower():
                return True
        return False

    def _check_bmi_percentile(self, encounter: Encounter) -> Optional[float]:
        try:
            anthropometry = getattr(encounter, "anthropometry", None)
            if anthropometry and anthropometry.bmi is not None:
                if anthropometry.age_years and anthropometry.age_years < 18:
                    bmi = anthropometry.bmi
                    if anthropometry.age_years < 5:
                        return bmi
                    elif anthropometry.age_years < 10:
                        return bmi
                    else:
                        if bmi >= 25:
                            return 85
                        elif bmi >= 30:
                            return 95
        except Exception:
            pass
        return None

    def _is_restrictive_eating(self, encounter: Encounter) -> bool:
        return False

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        age = encounter.demographics.age_years if encounter.demographics else 0
        age_group = self._get_age_group(age)

        patient_category = "typical"
        recommendations = []
        supplements = []
        interventions = []
        evidence = []
        action_checklist = []
        next_lab_check = []
        monitoring_frequency = "trimestral"
        confidence = CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]  # Default

        has_asd = self._has_diagnosis(encounter, ["f84", "autism", "tea"])
        has_adhd = self._has_diagnosis(encounter, ["f90", "adhd", "tdah"])
        has_obesity = self._has_obesity(encounter)
        bmi_percentile = self._check_bmi_percentile(encounter)

        if has_asd:
            patient_category = "tea"
            recommendations.append(
                {
                    "type": "assessment",
                    "priority": "high",
                    "text": "Evaluar deficiencias de vitaminas y minerales (Vit D, B12, Zinc, Hierro)",
                    "rationale": "Niños con TEA tienen mayor riesgo de deficiencias nutricionales. Adams et al. 2024.",
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="TEA_DEFICIENCY_RISK",
                    value="Elevated",
                    display="Riesgo de deficiencias nutricionales en TEA",
                )
            )

            if bmi_percentile and bmi_percentile >= 85:
                recommendations.append(
                    {
                        "type": "nutrition",
                        "priority": "high",
                        "text": "Intervención nutricional multimodal + intervención conductual familiar",
                        "rationale": "Obesidad comórbida en TEA requiere enfoque familiar. AAP 2023.",
                    }
                )

            supplements.append(
                {
                    "name": "Vitamina D",
                    "dose": "400-600 UI/día",
                    "indication": "Deficiencia común en TEA",
                    "priority": "medium",
                }
            )

            if bmi_percentile and bmi_percentile < 85:
                supplements.append(
                    {
                        "name": "Omega-3 (DHA+EPA)",
                        "dose": f"{self.OMEGA3_DOSAGE.get(age_group, {}).get('min', 500)}-{self.OMEGA3_DOSAGE.get(age_group, {}).get('max', 1000)} mg/día",
                        "indication": "Puede reducir comportamientos repetitivos (evidencia moderada)",
                        "priority": "low",
                    }
                )

            recommendations.append(
                {
                    "type": "warning",
                    "priority": "high",
                    "text": "Evitar restricciones dietéticas (sin gluten/caseína) sin supervisión profesional",
                    "rationale": "Meta-análisis Fraguas 2019: dietas de eliminación no evidence-based en TEA. Riesgo de deficiencias.",
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Warning",
                    code="TEA_DIET_RESTRICTION",
                    value="Avoid",
                    display="Dietas de eliminación sin supervisión",
                )
            )

            interventions.append(
                {
                    "type": "feeding_pattern",
                    "text": "Establecer horarios de comidas regulares (3 principales + 2 snacks)",
                    "priority": "medium",
                }
            )
            monitoring_frequency = "mensual"

        elif has_adhd:
            patient_category = "tdah"
            recommendations.append(
                {
                    "type": "assessment",
                    "priority": "high",
                    "text": "Evaluar niveles de hierro, zinc y omega-3",
                    "rationale": "Niños con TDAH frecuentemente tienen deficiencias. Lange 2023.",
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="TDAH_NUTRIENT_DEFICIENCY",
                    value="Screening recommended",
                    display="Evaluar deficiencias en TDAH",
                )
            )

            supplements.append(
                {
                    "name": "Multivitamínico pediátrico",
                    "dose": " Según fórmula",
                    "indication": "Suplementación de micronutrientes mejora síntomas de TDAH. Rucklidge 2025.",
                    "priority": "high",
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Study",
                    code="RUCKLIDGE_2025",
                    value="Eur Child Adolesc Psychiatry",
                    display="Micronutrientes en TDAH",
                )
            )

            supplements.append(
                {
                    "name": "Omega-3 (EPA+DHA)",
                    "dose": f"{self.OMEGA3_DOSAGE.get(age_group, {}).get('min', 500)}-{self.OMEGA3_DOSAGE.get(age_group, {}).get('max', 1000)} mg/día",
                    "indication": "Puede mejorar atención (evidencia moderada)",
                    "priority": "medium",
                }
            )

            if age >= 6:
                recommendations.append(
                    {
                        "type": "diet",
                        "priority": "medium",
                        "text": "Dieta mediterránea: alta en frutas, verduras, pescado, aceite de oliva",
                        "rationale": "Patrón dietético asociado a menor riesgo de TDAH. Pinto 2022.",
                    }
                )

            recommendations.append(
                {
                    "type": "behavior",
                    "priority": "high",
                    "text": "Establecer horarios de comidas regulares + snacks estructurados",
                    "rationale": "Niños con TDAH tienen patrones alimentarios irregulares. Evita picos de glucosa.",
                }
            )

            recommendations.append(
                {
                    "type": "warning",
                    "priority": "low",
                    "text": "Considerar reducir colorantes artificiales y azúcares refinados",
                    "rationale": "Evidencia controversial pero algunos niños responden. USPSTF 2024.",
                }
            )

            next_lab_check = ["Ferritina", "Zinc sérico", "Omega-3 índice"]
            monitoring_frequency = "mensual"
            confidence = CONFIDENCE_VALUES[ConfidenceLevel.INDIRECT_EVIDENCE]  # TDAH evidence is less certain

        elif has_obesity or (bmi_percentile and bmi_percentile >= 85):
            patient_category = "obesity"
            recommendations.append(
                {
                    "type": "intervention",
                    "priority": "high",
                    "text": "Intervención multimodal: nutricional + actividad física + comportamiento",
                    "rationale": "AAP 2023: Preferir intervenciones conductuales sobre farmacológicas.",
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Guideline",
                    code="AAP_2023",
                    value="Pediatrics 2023;151(2):e2022060640",
                    display="AAP Clinical Practice Guideline Pediatric Obesity",
                )
            )

            caloric_range = self.CALORIC_REQUIRMENTS.get(age_group, {})
            if caloric_range:
                recommendations.append(
                    {
                        "type": "caloric",
                        "priority": "medium",
                        "text": f"Requerimiento calórico: {caloric_range['min']}-{caloric_range['max']} kcal/día (80-100% según actividad)",
                        "rationale": "No restricción calórica severa en menores de 12 años. Preferir educación alimentaria.",
                    }
                )
                evidence.append(
                    ClinicalEvidence(
                        type="Warning",
                        code="PEDIATRIC_CALORIC_RESTRICTION",
                        value="Avoid",
                        display="Evitar restricciones severas en menores de 12 años",
                    )
                )

            recommendations.append(
                {
                    "type": "protein",
                    "priority": "medium",
                    "text": "Proteína: 1.0-1.2 g/kg/día (mínimo)",
                    "rationale": "Asegurar crecimiento adecuado, evitar pérdida de masa muscular.",
                }
            )

            recommendations.append(
                {
                    "type": "activity",
                    "priority": "high",
                    "text": "Actividad física: 60 min/día de intensidad moderada",
                    "rationale": "AAP 2023: 60 minutos diarios para niños con obesidad.",
                }
            )

            recommendations.append(
                {
                    "type": "family",
                    "priority": "high",
                    "text": "Intervención conductual familiar: Involucrar a toda la familia",
                    "rationale": "El éxito requiere cambio sistémico familiar, no solo del niño.",
                }
            )

            next_lab_check = ["Perfil lipídico", "Glucosa", "HbA1c"]
            monitoring_frequency = "trimestral"

        else:
            patient_category = "typical"
            recommendations.append(
                {
                    "type": "prevention",
                    "priority": "low",
                    "text": "Mantenimiento: patrón dietético equilibrado, actividad física regular",
                    "rationale": "Prevención de obesidad: dieta mediterránea, limitado tiempo de pantalla.",
                }
            )
            monitoring_frequency = "semestral"
            confidence = CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]  # Typical prevention is well-established

        for rec in recommendations:
            action_checklist.append(
                ActionItem(
                    category="lifestyle",
                    priority=rec["priority"],
                    task=rec["text"],
                    rationale=rec.get("rationale", ""),
                )
            )

        if patient_category != "typical":
            action_checklist.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task="Referir a nutrición pediátrica",
                    rationale="Casos complejos requieren evaluación por especialista en nutrición pediátrica.",
                )
            )

        explanation = (
            f"Categoría: {patient_category.upper()}. "
            f"Grupo etario: {age_group or 'N/A'}. "
            f"Recomendaciones: {len(recommendations)}. "
            f"Suplementos sugeridos: {len(supplements)}."
        )

        return AdjudicationResult(
            calculated_value=f"Pediatric Nutrition: {patient_category}",
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
            action_checklist=action_checklist,
            metadata={
                "patient_category": patient_category,
                "age_group": age_group,
                "age_years": age,
                "has_asd": has_asd,
                "has_adhd": has_adhd,
                "has_obesity": has_obesity,
                "bmi_percentile_estimate": bmi_percentile,
                "recommendations_count": len(recommendations),
                "supplements": supplements,
                "interventions": interventions,
                "next_lab_check": next_lab_check,
                "monitoring_frequency": monitoring_frequency,
            },
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="PROBABLE_RECOMMENDATION"
            if patient_category != "typical"
            else "NORMAL",
        )
