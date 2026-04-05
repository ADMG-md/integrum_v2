from typing import Dict, List
from src.engines.domain import AdjudicationResult, Encounter
from src.services.sanitization_service import sanitization_service
import structlog

logger = structlog.get_logger()

class NarrativeService:
    """
    Transforms raw clinical adjudications into a cohesive, explainable narrative.
    Correlates findings across different motors to provide a '360 perspective'.
    Uses SanitizationService to ensure HIPAA compliance if sending to external LLMs.
    """

    def generate_technical_summary(self, results: Dict[str, AdjudicationResult], encounter: Encounter) -> str:
        # 1. PII Sanitization (HIPAA)
        # In a real hybrid LLM flow, we would send 'sanitized_context' to the model.
        sanitized_context = sanitization_service.sanitize_encounter(encounter.model_dump())
        
        narrative_parts = []
        
        # 1. Start with the "Persona" (Core Phenotype)
        if "acosta" in results:
            acosta_res = results["acosta"]
            narrative_parts.append(f"El análisis fenotípico central sugiere un {acosta_res.calculated_value}.")

        # 2. Add Staging/Severity
        if "eoss" in results:
            eoss_res = results["eoss"]
            narrative_parts.append(f"La severidad clínica se clasifica como {eoss_res.calculated_value}, indicando el nivel de daño a órgano blanco.")

        # 3. Correlated Specialty Insights
        specialty_findings = []
        
        # Risk correlations (The 'Brain' of the narrative)
        if "MetabolicPrecisionMotor" in results and "Lifestyle360Motor" in results:
            met_res = results["MetabolicPrecisionMotor"]
            life_res = results["Lifestyle360Motor"]
            if "Insulin Resistance" in met_res.calculated_value and "Sleep Debt" in life_res.calculated_value:
                specialty_findings.append(
                    "Se observa una desregulación metabólico-circadiana significativa: "
                    "la deuda de sueño identificada está exacerbando la resistencia a la insulina medida por índices TyG/Mets-IR."
                )

        if "HypertensionSecondaryMotor" in results:
            hta_res = results["HypertensionSecondaryMotor"]
            if "Primary Aldosteronism" in hta_res.calculated_value:
                specialty_findings.append(
                    "Atención: Los hallazgos hemodinámicos sugieren un riesgo elevado de aldosteronismo primario, "
                    "lo cual requiere confirmación mediante pruebas de supresión."
                )

        if "InflammationMotor" in results:
            inf_res = results["InflammationMotor"]
            if "Meta-inflammation" in inf_res.calculated_value:
                specialty_findings.append(
                    f"Existe un estado de meta-inflamación sistémica ({inf_res.evidence[0].value if inf_res.evidence else ''} mg/dL de hs-CRP) "
                    "que actúa como motor de progresión para la enfermedad cardiometabólica."
                )

        if "PharmacologicalAuditMotor" in results:
            pharma_res = results["PharmacologicalAuditMotor"]
            if "weight gain" in pharma_res.calculated_value.lower():
                specialty_findings.append(
                    f"Se ha detectado sabotaje farmacológico: medicamentos actuales ({pharma_res.calculated_value}) "
                    "están induciendo ganancia ponderal de forma exógena."
                )

        if specialty_findings:
            narrative_parts.append("\nEn cuanto a la medicina de precisión:")
            narrative_parts.extend(specialty_findings)

        # 4. Closing Logic
        if not narrative_parts:
            return "No se han detectado hallazgos clínicos significativos tras la ejecución de los motores."

        return " ".join(narrative_parts)

# Singleton
narrative_service = NarrativeService()
