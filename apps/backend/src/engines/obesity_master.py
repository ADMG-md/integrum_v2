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
    metabolic_proxies_summary: Optional[str] = None  # Added V2.6
    metabolic_proxies_active: bool = False  # Added V2.6


class ObesityClinicalStoryOutput(BaseModel):
    clinical_profile: str
    discordant_profile: bool
    discordance_reason: Optional[str]
    headline_verdict: str
    explanation: str


class ObesityMasterMotor:
    ENGINE_NAME = "ObesityMasterMotor"
    ENGINE_VERSION = "0.2.0"
    REQUIREMENT_ID = "OBESITY-MASTER"

    def get_version_hash(self) -> str:
        return "0.2.0"

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
        if data.eoss_stage >= 3:
            actions.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task="Referencia a manejo especializado de obesidad",
                    rationale=f"EOSS Stage {data.eoss_stage} indica daño orgánico establecido.",
                )
            )

        estado = (
            "CONFIRMED_ACTIVE"
            if (discordant or data.eoss_stage >= 3 or data.metabolic_proxies_active)
            else "INDETERMINATE_LOCKED"
        )
        confidence = 0.90 if not discordant else 0.75

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
                "discordant_profile": discordant,
                "discordance_reason": reason,
                "headline_verdict": headline,
                "acosta_phenotype": data.acosta_phenotype,
                "eoss_stage": data.eoss_stage,
                "sarcopenia_risk": data.sarcopenia_risk,
                "bmi": data.bmi_kg_m2,
                "cvd_risk": data.cvd_risk_category,
            },
        )

    def _detect_discordance(
        self, d: ObesityClinicalStoryInput
    ) -> Tuple[bool, Optional[str]]:
        # MHO (Metabolically Healthy Obesity) but CVD risk is high is REMOVED
        # to comply with FDA 2026 CDS guidelines (experimental engines cannot drive hard automatic alerts).

        # Sarcopenic obesity: high sarcopenia risk + elevated BMI
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
            return "Perfil de obesidad de alto interés clínico; requiere revisión integral."

        # MISSION 12.5: Elevate risk based on Deep Metabolic Proxies
        if d.metabolic_proxies_active:
            summary = d.metabolic_proxies_summary or ""
            if "Disfunción Mitocondrial" in summary:
                return "Obesidad con Disfunción Mitocondrial (Vía de la Fructosa); Riesgo Metabólico Elevado."
            if "Metainflamación" in summary:
                return "Obesidad con Metainflamación Sistémica Activa; Prioridad Terapéutica Alta."

        if d.eoss_stage >= 3:
            return "Obesidad con daño establecido (EOSS ≥3)."
        return "Obesidad sin daño avanzado aparente."

    def _build_explanation(
        self, d: ObesityClinicalStoryInput, discordant: bool, reason: Optional[str]
    ) -> str:
        parts = [
            f"Fenotipo Acosta: {d.acosta_phenotype}.",
            f"EOSS: {d.eoss_stage}.",
            f"Riesgo de sarcopenia: {d.sarcopenia_risk}.",
            f"BMI: {d.bmi_kg_m2:.1f}, cintura: {d.waist_cm:.1f} cm.",
        ]
        if d.cvd_risk_category:
            parts.append(f"Riesgo cardiovascular: {d.cvd_risk_category}.")
        if d.metabolic_proxies_summary:
            parts.append(f"Firmas Metabólicas: {d.metabolic_proxies_summary}.")
        if discordant and reason:
            parts.append(f"Discordancia detectada: {reason}.")

        return " ".join(parts)
