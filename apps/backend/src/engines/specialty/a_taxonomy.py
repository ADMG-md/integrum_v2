from typing import Dict, Any, Tuple
from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence


class ATaxonomyMotor(BaseClinicalMotor):
    """
    Motor compositor que lee outputs de AcostaPhenotypeMotor y observaciones TFEQ/GAD-7/PHQ-9
    para producir un único código de Axis A (A0-A4) con semántica clínica de obesidad.
    """
    REQUIREMENT_ID = "A-TAXONOMY-V0.1"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # El motor agregador siempre corre, su lógica maneja datos faltantes asumiendo A0 si no hay dominancia
        return True, ""

    def compute(self, encounter: Encounter, primary_results: Dict[str, Any] = None) -> AdjudicationResult:
        if primary_results is None:
            primary_results = {}

        # 1. Extraer AcostaPhenotypeMotor scores
        acosta_result = primary_results.get("AcostaPhenotypeMotor")
        acosta_scores = {
            "cerebro_hambriento": 0.0,
            "intestino_hambriento": 0.0,
            "hambre_emocional": 0.0,
            "quema_lenta": 0.0
        }
        is_acosta_indeterminate = False

        if acosta_result and hasattr(acosta_result, "metadata"):
            meta = acosta_result.metadata
            if "phenotype_scores" in meta:
                acosta_scores.update(meta["phenotype_scores"])
            if acosta_result.estado_ui == "INDETERMINATE_LOCKED":
                is_acosta_indeterminate = True
        elif acosta_result and isinstance(acosta_result, dict):
            # En caso de que se pase un dict (ej. desde endpoints)
            meta = acosta_result.get("metadata", {})
            if "phenotype_scores" in meta:
                acosta_scores.update(meta["phenotype_scores"])
            if acosta_result.get("estado_ui") == "INDETERMINATE_LOCKED":
                is_acosta_indeterminate = True

        # 2. Extraer observaciones
        def safe_get_obs(code: str) -> float:
            obs = encounter.get_observation(code)
            if obs:
                try:
                    return float(obs.value)
                except (ValueError, TypeError):
                    pass
            return 0.0

        tfeq_unc = safe_get_obs("TFEQ-UNCONTROLLED")
        tfeq_emo = safe_get_obs("TFEQ-EMOTIONAL")
        gad7 = safe_get_obs("GAD-7")
        phq9 = safe_get_obs("PHQ9-SCORE") or safe_get_obs("PHQ-9") # Fallback for code used in psychometabolic

        evidence = []
        code = "A0"
        display = "A0 - Sin dominancia clara o Indeterminado"
        estado = "CONFIRMED_ACTIVE"
        confidence = 1.0

        # Reglas en orden de prioridad
        if tfeq_unc > 2.5 and gad7 >= 10:
            code = "A4"
            display = "A4 - Hiperfagia Ansiogénica (Vía HPA)"
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A4", value=f"TFEQ-UNC={tfeq_unc}, GAD-7={gad7}",
                display="Hiperfagia ansiogénica"
            ))
        elif tfeq_emo > 2.5 and phq9 >= 10:
            code = "A2"
            display = "A2 - Déficit Hedónico / Emocional (Vía Dopaminérgica)"
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A2", value=f"TFEQ-EMO={tfeq_emo}, PHQ-9={phq9}",
                display="Hedónico con depresión activa"
            ))
        elif tfeq_emo > 2.5:
            code = "A2"
            display = "A2 - Déficit Hedónico / Emocional"
            confidence = 0.5  # Partial confidence since no active severe depression
            estado = "PROBABLE_WARNING"
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A2", value=f"TFEQ-EMO={tfeq_emo}",
                display="Hedónico aislado"
            ))
        elif tfeq_unc > 2.5:
            code = "A1"
            display = "A1 - Ingesta-Dominante (No Ansiogénico)"
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A1", value=f"TFEQ-UNC={tfeq_unc}",
                display="Uncontrolled eating"
            ))
        elif acosta_scores["cerebro_hambriento"] > 0.65 or acosta_scores["intestino_hambriento"] > 0.65:
            code = "A1"
            display = "A1 - Ingesta-Dominante (Fenotipo Acosta)"
            max_acosta = max(acosta_scores["cerebro_hambriento"], acosta_scores["intestino_hambriento"])
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A1", value=f"Acosta_score={max_acosta}",
                display="Saciación/Saciedad alterada"
            ))
        elif acosta_scores["quema_lenta"] > 0.65:
            code = "A3"
            display = "A3 - Gasto-Limitado (Quema Lenta)"
            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A3", value=f"Quema_Lenta={acosta_scores['quema_lenta']}",
                display="Fenotipo de bajo gasto energético"
            ))
        else:
            # A0
            code = "A0"
            if is_acosta_indeterminate:
                display = "A0 - Acosta Indeterminado"
                estado = "INDETERMINATE_LOCKED"
                confidence = 0.0
            else:
                display = "A0 - Fenotipo Basal o Mixto (Sin Dominancia)"
                confidence = 1.0

            evidence.append(ClinicalEvidence(
                type="Taxonomy", code="A0", value="No rules matched",
                display="A0 Fallback"
            ))

        return AdjudicationResult(
            calculated_value=display,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            metadata={"axis": "A", "code": code}
        )
