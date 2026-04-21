from pydantic import BaseModel
from typing import Literal, Tuple, Optional
from src.engines.domain import AdjudicationResult, ClinicalEvidence, ActionItem


class ObesityClinicalStoryInput(BaseModel):
    acosta_phenotype: str
    eoss_stage: int  # 0-4
    sarcopenia_risk: Literal["low", "moderate", "high"]
    bmi_kg_m2: float
    waist_cm: float
    cvd_risk_category: Optional[
        Literal["low", "borderline", "intermediate", "high"]
    ] = None
    metabolic_proxies_summary: Optional[str] = None
    metabolic_proxies_active: bool = False
    nutrition_precision_summary: Optional[str] = None  # Added V2.7
    pharma_precision_summary: Optional[str] = None  # Added V2.7


class ObesityClinicalStoryOutput(BaseModel):
    clinical_profile: str
    discordant_profile: bool
    discordance_reason: Optional[str]
    headline_verdict: str
    explanation: str


class ObesityMasterMotor:
    ENGINE_NAME = "ObesityMasterMotor"
    ENGINE_VERSION = "0.3.0"  # Augmented Synthesis
    REQUIREMENT_ID = "OBESITY-MASTER-V3"

    def get_version_hash(self) -> str:
        return "0.3.0"

    def __call__(self, data: ObesityClinicalStoryInput) -> AdjudicationResult:
        discordant, reason = self._detect_discordance(data)
        profile = self._build_profile_label(data, discordant)
        headline = self._build_headline_verdict(data, discordant)
        explanation = self._build_explanation(data, discordant, reason)

        actions = []
        if discordant and reason:
            actions.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task=f"Revisión integral: {reason}",
                    rationale=f"Perfil discordante detectado ({reason}). Requiere evaluación multidisciplinaria.",
                )
            )
        
        # Sugerencia de derivación agresiva si hay sarcopenia severa y obesidad
        if data.sarcopenia_risk == "high":
             actions.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task="Evaluación por Rehabilitación/Fisiatría",
                    rationale="Riesgo alto de Sarcopenia detectado en paciente con Obesidad. Priorizar ganancia funcional ante pérdida de peso."
                )
            )

        estado = (
            "CONFIRMED_ACTIVE"
            if (discordant or data.eoss_stage >= 3 or data.metabolic_proxies_active)
            else "INDETERMINATE_LOCKED"
        )
        confidence = 0.95 if not discordant else 0.80

        return AdjudicationResult(
            calculated_value=headline,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="OBESITY-MASTER",
                    value=profile,
                    display="Clinical Obesity Profile",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "clinical_profile": profile,
                "headline_verdict": headline,
                "acosta_phenotype": data.acosta_phenotype,
                "eoss_stage": data.eoss_stage,
                "sarcopenia_risk": data.sarcopenia_risk,
                "bmi": data.bmi_kg_m2,
                "cvd_risk": data.cvd_risk_category,
                "nutrition_summary": data.nutrition_precision_summary,
                "pharma_summary": data.pharma_precision_summary,
                "discordant_profile": discordant,
                "discordance_reason": reason,
            },
        )

    def _detect_discordance(
        self, d: ObesityClinicalStoryInput
    ) -> Tuple[bool, Optional[str]]:
        if d.sarcopenia_risk == "high" and d.bmi_kg_m2 >= 27:
            return True, "Obesidad sarcopénica"
        return False, None

    def _build_profile_label(
        self, d: ObesityClinicalStoryInput, discordant: bool
    ) -> str:
        base = f"{d.acosta_phenotype}, EOSS {d.eoss_stage}"
        if discordant:
            return f"{base} (perfil discordante)"
        return base

    def _build_headline_verdict(
        self, d: ObesityClinicalStoryInput, discordant: bool
    ) -> str:
        if discordant:
            return "Perfil de obesidad de alto interés clínico (Sarcopenia); requiere revisión integral."

        if d.metabolic_proxies_active:
            summary = d.metabolic_proxies_summary or ""
            if "Disfunción Mitocondrial" in summary:
                return "Obesidad con Disfunción Mitocondrial (Vía de la Fructosa); Prioridad Metabólica."
            if "Metainflamación" in summary:
                return "Obesidad con Metainflamación Sistémica Activa; Prioridad Terapéutica."

        if d.eoss_stage >= 3:
            return f"Obesidad con daño establecido (EOSS {d.eoss_stage})."
        return "Obesidad metabólicamente activa (EOSS <3)."

    def _build_explanation(
        self, d: ObesityClinicalStoryInput, discordant: bool, reason: Optional[str]
    ) -> str:
        parts = [
            f"Paciente con fenotipo ACOSTA: {d.acosta_phenotype}.",
            f"Grado de complicación EOSS: {d.eoss_stage}.",
            f"Riesgo de sarcopenia: {d.sarcopenia_risk}.",
            f"Riesgo cardiovascular estimado: {d.cvd_risk_category or 'pendiente'}.",
        ]
        
        if d.nutrition_precision_summary:
            parts.append(f"DIRECCIÓN NUTRICIONAL: {d.nutrition_precision_summary}.")
        
        if d.pharma_precision_summary:
            parts.append(f"DIRECCIÓN FARMACOLÓGICA: {d.pharma_precision_summary}.")

        if d.metabolic_proxies_summary:
            parts.append(f"FIRMAS METABÓLICAS: {d.metabolic_proxies_summary}.")

        if discordant and reason:
            parts.append(f"NOTA: Detectada discordancia clínica ({reason}).")

        return " ".join(parts)
