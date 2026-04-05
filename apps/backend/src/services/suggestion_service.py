from typing import List, Dict
from src.engines.domain import AdjudicationResult, Encounter
from src.schemas.report import ClinicalSuggestionSchema
import structlog

logger = structlog.get_logger()

class SuggestionService:
    """
    The 'Clinical Detective'. Analyzes cross-engine results to suggest 
    diagnostic and therapeutic actions based on Grade Evidence.
    """

    def generate_suggestions(self, results: Dict[str, AdjudicationResult], encounter: Encounter) -> List[ClinicalSuggestionSchema]:
        suggestions = []

        # 1. Diagnostic Suggestions (Detective role)
        if "HypertensionSecondaryMotor" in results:
            hta_res = results["HypertensionSecondaryMotor"]
            if "Primary Aldosteronism" in hta_res.calculated_value:
                suggestions.append(ClinicalSuggestionSchema(
                    title="Confirmación de Aldosteronismo Primario",
                    description="Debido al ARR elevado (>30), se sugiere realizar prueba de supresión con solución salina o test de captopril.",
                    priority="High",
                    category="Diagnostic",
                    evidence_codes=["ARR", "ALDOSTERONE"]
                ))

        if "EndocrinePrecisionMotor" in results:
            endo_res = results["EndocrinePrecisionMotor"]
            if "Subclinical Hypothyroidism" in endo_res.calculated_value:
                suggestions.append(ClinicalSuggestionSchema(
                    title="Seguimiento de Perfil Tiroideo",
                    description="Repetir TSH y T4L en 3-6 meses para confirmar persistencia antes de considerar levotiroxina.",
                    priority="Medium",
                    category="Diagnostic",
                    evidence_codes=["TSH"]
                ))

        # 2. Therapeutic Suggestions (Prescription role)
        if "Lifestyle360Motor" in results:
            life_res = results["Lifestyle360Motor"]
            if "Sleep Debt" in life_res.calculated_value:
                suggestions.append(ClinicalSuggestionSchema(
                    title="Intervención en Higiene de Sueño",
                    description="Implementar protocolo de restricción de luz azul 2h antes de dormir y mantener horario regular.",
                    priority="High",
                    category="Therapeutic",
                    evidence_codes=["SLEEP"]
                ))

        if "PharmacologicalAuditMotor" in results:
            pharma_res = results["PharmacologicalAuditMotor"]
            if "weight gain" in pharma_res.calculated_value.lower():
                suggestions.append(ClinicalSuggestionSchema(
                    title="Revisión de Medicación Obesogénica",
                    description=f"Considerar alternativas metabólicamente neutras para: {pharma_res.calculated_value}.",
                    priority="High",
                    category="Therapeutic",
                    evidence_codes=["MEDS"]
                ))

        # 3. Preventive / Nutrition Correlation
        if "MetabolicPrecisionMotor" in results:
            met_res = results["MetabolicPrecisionMotor"]
            if "Insulin Resistance" in met_res.calculated_value:
                suggestions.append(ClinicalSuggestionSchema(
                    title="Optimización de Carga Glucémica",
                    description="Priorizar carbohidratos de baja densidad energética y alta fibra para mejorar la sensibilidad a la insulina.",
                    priority="High",
                    category="Therapeutic",
                    evidence_codes=["TyG", "GLUCOSE"]
                ))

        return suggestions

# Singleton
suggestion_service = SuggestionService()
