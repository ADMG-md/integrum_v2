"""
Pharmacogenomic Proxy Motor
Uses clinical and standard laboratory markers as low-cost proxies for genetic polymorphisms.
- MTHFR (Methylation defect) -> Homocysteine + MCV -> Suggest Methylfolate
- SLCO1B1 (Statin Intolerance) -> Myalgias on statins -> Suggest Hydrophilic statins / CoQ10
- CYP1A2 (Caffeine Slow Metabolizer) -> Anxiety/Insomnia on caffeine -> Veto thermogenics
- VDR (Vitamin D Receptor Resistance) -> Persistent low Vit D + PPI use -> High dose micellized D3 + Mg
"""

from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter, AdjudicationResult, ClinicalEvidence, ActionItem, safe_float
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel

class PharmacogenomicProxyMotor(BaseClinicalMotor):
    REQUIREMENT_ID = "PHARMACOGENOMICS-PROXY-V1"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Always runs if there's an encounter
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        actions = []
        evidence = []
        findings = []
        confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER] # Inherently proxy-based, lower baseline confidence

        h = encounter.history
        mp = encounter.metabolic_panel

        # --- 1. MTHFR (Methylation Proxy) ---
        hcy_obs = encounter.get_observation("HCY-001") # Homocysteine
        mcv_obs = encounter.get_observation("MCV-001") # Mean Corpuscular Volume
        
        hcy = safe_float(hcy_obs.value) if hcy_obs else None
        mcv = safe_float(mcv_obs.value) if mcv_obs else None

        if hcy is not None and hcy >= 15.0:
            evidence.append(ClinicalEvidence(type="Lab", code="HCY", value=hcy, threshold=">=15", display="Hiperhomocisteinemia"))
            if mcv is not None and mcv >= 95.0:
                findings.append("Alto riesgo funcional de mutación MTHFR (Homocisteína >15 y Macrocitosis)")
                actions.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Sustituir Ácido Fólico Sintético por L-Metilfolato",
                    rationale="Defecto de metilación probable (MTHFR proxy+). El ácido fólico sintético se acumula sin convertirse, elevando el riesgo CV y neurodegenerativo. Usar solo Folato Metilado (5-MTHF) y B12."
                ))
                confidence += 0.10

        # --- 2. SLCO1B1 (Statin Intolerance Proxy) ---
        history_statin_myalgia = getattr(h, "has_statin_myalgia", False)
        if history_statin_myalgia:
            findings.append("Miopatía por estatinas (Proxy SLCO1B1)")
            evidence.append(ClinicalEvidence(type="History", code="STATIN-MYALGIA", value="Yes", display="Mialgia inducida por Estatinas"))
            actions.append(ActionItem(
                category="pharmacological", priority="high",
                task="Cambio a Estatinas Hidrofílicas o Adición de CoQ10",
                rationale="Miopatía lipofílica (Proxy SLCO1B1 defectuoso). Rotar a Rosuvastatina/Pravastatina (poca penetración muscular) y/o prescribir Coenzima Q10 (200mg/día) u omitir vía oral (Bempedoico/PCSK9i)."
            ))

        # --- 3. CYP1A2 (Caffeine Slow Metabolizer Proxy) ---
        history_caffeine_anxiety = getattr(h, "caffeine_anxiety_insomnia", False)
        if history_caffeine_anxiety:
            findings.append("Metabolizador Lento de Cafeína (Proxy CYP1A2)")
            actions.append(ActionItem(
                category="lifestyle", priority="medium",
                task="VETAR suplementos térmicos y pre-entrenos",
                rationale="Hipersensibilidad cafeínica (Proxy CYP1A2 Lento). Elevado riesgo de crash metabólico y pico de cortisol. Restringir uso de fat-burners estimulantes."
            ))

        # --- 4. VDR (Vitamin D Receptor Mutation Proxy) ---
        vitd_obs = encounter.get_observation("VIT-D-25OH")
        vitd = safe_float(vitd_obs.value) if vitd_obs else None
        taking_otc_vitd = getattr(h, "taking_otc_vitd", False)
        taking_ppi = getattr(h, "taking_ppi_chronically", False) # Omeprazole / Pantoprazole

        if vitd is not None and vitd < 30.0:
            if taking_otc_vitd or taking_ppi:
                findings.append("Resistencia a Vitamina D (Proxy VDR / IBP)")
                evidence.append(ClinicalEvidence(type="Lab/Hx", code="VDR-PROXY", value="Resistant", display="Vitamina D refractaria a OTC"))
                actions.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Vitamina D3 Micelizada + Cofactores (Glicinato de Mg)",
                    rationale="El paciente no absorbe y/o no ensambla la VitD (probable hipoclorhidria por IBP o polimorfismo VDR). Dosis de choque micelizada requerida, dictaminando magnesio exógeno obligatorio."
                ))

        status = "CONFIRMED_ACTIVE" if findings else "INDETERMINATE_LOCKED"
        headline = " | ".join(findings) if findings else "Ausencia de proxys farmacogenómicos de alto riesgo."

        return AdjudicationResult(
            calculated_value=headline,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=status,
            explanation="Evaluación de sombras genéticas (Proxys clínicos).",
            action_checklist=actions,
            metadata={"pharmacogenomic_proxies": bool(findings)}
        )
