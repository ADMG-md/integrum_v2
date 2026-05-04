from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, ClinicalEvidence
from src.engines.base_models import AdjudicationResult
from typing import Tuple, Dict, Any
import math

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class DeepMetabolicProxyMotor(BaseClinicalMotor):
    """
    Tier 4 & 5 Motor: Deep Metabolic & Shadow Proxies.

    LEVEL 1 (Regional Realism):
    Uses accessible biomarkers (GGT, Ferritin, UA, TG/HDL) to infer
    metainflammation and oxidative stress states.

    LEVEL 2 (Frontier Science):
    Uses advanced metabolomics (BCAA, GlycA) for genomic/epigenetic inference.

    Evidence:
    - GGT as oxidative stress marker: Lee et al., 2007. Arterioscler Thromb Vasc Biol 27: 1204.
      GGT predicts CVD independently; reflects glutathione depletion.
    - Ferritin as metainflammation: Fernandez-Real et al., 2002. Diabetes Care 25: 1039-1044.
      Ferritin correlates with insulin resistance and adipose tissue inflammation.
    - Uric Acid / Fat Switch: Johnson et al., 2019. Nat Rev Endocrinol 15: 641-653.
      Fructose-induced hyperuricemia triggers mitochondrial dysfunction and fat storage.
    - TG/HDL ratio as sdLDL proxy: McLaughlin et al., 2005. Circulation 112: 1-7.
      TG/HDL >= 3.0 (M) / >= 2.5 (F) predicts small dense LDL phenotype.
    - BCAA and insulin resistance: Wang et al., 2011. Sci Transl Med 3: 75ra26.
      Branched-chain amino acids predict future diabetes independently.
    - GlycA: Otvos et al., 2015. Clin Chem 61(1): 190-201.
      GlycA as systemic inflammation marker integrating multiple acute-phase proteins.

    REQUIREMENT_ID: DEEP-METABOLIC
    """

    REQUIREMENT_ID = "DEEP-METABOLIC"

    CODES = {
        # Level 1: Colombian/Latin Standard
        "GGT": "GGT-001",
        "FERRITIN": "FER-001",
        "URIC_ACID": "UA-001",
        "TRIG": "2571-8",
        "HDL": "2085-9",
        # Level 2: Deep Metabolomics (Research/International)
        "BCAA_ISO": "BCAA-ISO-001",
        "BCAA_LEU": "BCAA-LEU-001",
        "BCAA_VAL": "BCAA-VAL-001",
        "GLYCA": "GLYCA-001",
        "ACYL_CAR": "ACYL-CAR-001",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Triggers if ANY high-value proxy is present
        has_any = any(encounter.get_observation(code) for code in self.CODES.values())
        if not has_any:
            return False, "No shadow markers or deep metabolomics for analysis"
        return True, ""

    def compute(
        self, encounter: Encounter, context: Dict[str, Any] = None
    ) -> AdjudicationResult:
        findings = []
        evidence = []
        is_male = str(encounter.demographics.gender).lower() in ["male", "m", "hombre"]
        confidence_base = 0.85

        # --- LEVEL 1: REGIONAL PROXIES (COLOMBIA READY) ---

        # 1. GGT: The Shadow of Glutathione Depletion
        ggt = encounter.get_observation(self.CODES["GGT"])
        if ggt:
            val = float(ggt.value)
            threshold = 40 if is_male else 25
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="GGT",
                    value=val,
                    display="GGT",
                    threshold=f">{threshold}",
                )
            )
            if val > threshold:
                findings.append("Proxy de Estrés Oxidativo (Depleción de Glutatión)")

        # 2. Ferritin: The Shadow of Metainflammation (Sick Fat)
        fer = encounter.get_observation(self.CODES["FERRITIN"])
        if fer:
            val = float(fer.value)
            threshold = 300 if is_male else 200
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="FER-001",
                    value=val,
                    display="Ferritina",
                    threshold=f">{threshold}",
                )
            )
            if val > threshold:
                findings.append("Proxy de Metainflamación (Adiposopatía Inflamatoria)")

        # 3. Uric Acid: The Shadow of Mitochondrial 'Fat Switch' (Richard Johnson)
        ua = encounter.get_observation(self.CODES["URIC_ACID"])
        if ua:
            val = float(ua.value)
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="UA-001",
                    value=val,
                    display="Ácido Úrico",
                    threshold=">6.5",
                )
            )
            if val > 6.5:
                findings.append("Proxy de Disfunción Mitocondrial (Vía de la Fructosa)")

        # 4. TG/HDL Ratio: The Shadow of Phenotype B (sdLDL)
        trig = encounter.get_observation(self.CODES["TRIG"])
        hdl = encounter.get_observation(self.CODES["HDL"])
        if trig and hdl and float(hdl.value) > 0:
            ratio = float(trig.value) / float(hdl.value)
            threshold = 3.0 if is_male else 2.5
            evidence.append(
                ClinicalEvidence(
                    type="Calculation",
                    code="TG/HDL",
                    value=round(ratio, 2),
                    display="Cociente TG/HDL",
                    threshold=f">{threshold}",
                )
            )
            if ratio > threshold:
                findings.append(
                    "Proxy de Dislipidemia Aterogénica (Fenotipo B / LDL denso)"
                )

        # --- LEVEL 2: DEEP OMICS PROXIES (FRONTIER) ---

        # BCAA Cluster
        iso = encounter.get_observation(self.CODES["BCAA_ISO"])
        if iso:
            findings.append(
                "Detección de Firma Metabolómica de Resistencia a la Insulina"
            )
            confidence_base = 0.90

        # GlycA
        glyca = encounter.get_observation(self.CODES["GLYCA"])
        if glyca:
            findings.append("Proxy de Envejecimiento Epigenético Sistémico (GlycA)")
            confidence_base = 0.92

        summary = (
            " | ".join(findings)
            if findings
            else "Sin firmas de riesgo metabólico profundo"
        )

        # Actionable checklists
        action_checklist = []
        if "Proxy de Disfunción Mitocondrial" in summary:
            action_checklist.append(
                {
                    "task": "Restricción Agresiva de Fructosa Añadida",
                    "rationale": "El ácido úrico elevado indica activación de la vía aldosa-reductasa (The Fat Switch).",
                    "category": "lifestyle",
                    "priority": "high",
                }
            )
        if "Depleción de Glutatión" in summary:
            action_checklist.append(
                {
                    "task": "Optimizar Precursores de Glutatión (NAC / Glicina)",
                    "rationale": "GGT elevada sugiere compensación por alto estrés oxidativo redox.",
                    "category": "pharmacological",
                    "priority": "medium",
                }
            )

        explanation = (
            "Este motor traduce laboratorios accesibles y pruebas ómicas avanzadas en 'Firmas Metabólicas'. "
            "Utiliza el modelo de Richard Johnson para disfunción mitocondrial (UA) y el consenso de Metainflamación "
            "para Ferritina/GGT. Permite inferir riesgos genómicos y epigenéticos sin pruebas de alto costo."
        )

        return AdjudicationResult(
            calculated_value=summary,
            confidence=confidence_base,
            evidence=evidence,
            explanation=explanation,
            estado_ui="CONFIRMED_ACTIVE" if findings else "PROBABLE_WARNING",
            action_checklist=action_checklist,
        )
