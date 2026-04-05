from typing import Dict, Any, List
from src.engines.domain import AdjudicationResult, Encounter
from src.services.sanitization_service import sanitization_service
import json

class HybridIntelligenceService:
    """
    Mission 6: Hybrid Intelligence Layer.
    Provides sanitized exports for external LLMs and internal 'Reflective' insights.
    """

    def generate_clinician_prompt(self, results: Dict[str, AdjudicationResult], encounter: Encounter) -> str:
        """
        Generates a HIPAA-compliant prompt for a physician to use with external LLMs (GPT-4/Claude).
        Includes deterministic findings as ground truth.
        """
        # 1. Sanitize the encounter data
        sanitized_encounter = sanitization_service.sanitize_encounter(encounter.model_dump())
        
        # 2. Extract key findings
        findings_summary = []
        for name, res in results.items():
            findings_summary.append(f"- {name}: {res.calculated_value} (Confidence: {res.confidence*100}%)")

        # 3. Construct the prompt
        prompt = f"""
### CONTEXTO CLÍNICO (Saneado por Integrum V2)
Paciente anonimizado con la siguiente configuración:
- Condiciones: {', '.join([c['title'] for c in sanitized_encounter['conditions']])}
- Hallazgos de Motores SaMD (Ground Truth):
{chr(10).join(findings_summary)}

### TAREA PARA EL ASISTENTE IA
Actúa como un Colega Clínico de Medicina de Precisión. Basándote ÚNICAMENTE en los hallazgos determinísticos arriba mencionados, genera una propuesta de:
1. Plan de alimentación enfocado en revertir el fenotipo detectado.
2. Estrategia de optimización de cronodisrupción si aplica.
3. Explicación simplificada para el paciente (NIVEL 5to de primaria).

### RESTRICCIONES
- No sugieras diagnósticos nuevos que no estén en la lista.
- Prioriza la evidencia de los motores Acosta y EOSS.
- Respeta los límites biológicos detectados.
"""
        return prompt

    def generate_patient_narrative(self, results: Dict[str, AdjudicationResult]) -> str:
        """
        Simplified, non-technical reflection for the patient.
        """
        reflections = []
        
        if "acosta" in results:
            val = results["acosta"].calculated_value
            if "Hedonic" in val:
                reflections.append("Tu cuerpo está enviando señales de hambre que no son por falta de energía, sino por búsqueda de placer (Hambre Hedónica).")
            elif "Sarcopenic" in val:
                reflections.append("Necesitamos enfocarnos en fortalecer tus músculos para mejorar tu metabolismo.")

        if "Lifestyle360Motor" in results:
            val = results["Lifestyle360Motor"].calculated_value
            if "Sleep Debt" in val:
                reflections.append("Tu falta de sueño está 'saboteando' tus esfuerzos metabólicos. Dormir es parte de tu tratamiento.")

        if not reflections:
            return "Su análisis está listo. Consulte con su médico para los detalles técnicos."

        return " ".join(reflections)

# Singleton
hybrid_intel_service = HybridIntelligenceService()
