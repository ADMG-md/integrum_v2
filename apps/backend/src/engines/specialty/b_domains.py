from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple, List, Dict, Any, Optional
from src.models.encounter import CompletenessStatus

class BDomainScoresMotor(BaseClinicalMotor):
    """
    Evaluates 6 specific domains for Axis B:
    - B_AFFECT (PHQ-9)
    - B_ANXIETY (GAD-7)
    - B_UNCONTROLLED (TFEQ-UNCONTROLLED)
    - B_EMOTIONAL (TFEQ-EMOTIONAL)
    - B_COGNITIVE (TFEQ-COGNITIVE)
    - B_SLEEP (AIS-001)
    """

    REQUIREMENT_ID = "B-DOMAINS-2026"

    CODES = {
        "PHQ9": "PHQ9-SCORE",
        "GAD7": "GAD-7",
        "TFEQ_UNCONTROLLED": "TFEQ-UNCONTROLLED",
        "TFEQ_EMOTIONAL": "TFEQ-EMOTIONAL",
        "TFEQ_COGNITIVE": "TFEQ-COGNITIVE",
        "AIS": "AIS-001",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Always runs, missing data results in indeterminate status.
        return True, ""

    def _get_float(self, encounter: Encounter, code: str) -> Optional[float]:
        obs = encounter.get_observation(code)
        if obs:
            try:
                return float(obs.value)
            except (ValueError, TypeError):
                pass
        return None

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        domain_scores = []
        
        # B_AFFECT -> PHQ9
        phq9 = self._get_float(encounter, self.CODES["PHQ9"])
        if phq9 is not None:
            if phq9 <= 4:
                code, label = "minimal", "Sin carga afectiva significativa"
            elif phq9 <= 9:
                code, label = "mild", "Depresión leve"
            elif phq9 <= 14:
                code, label = "moderate", "Depresión moderada"
            else:
                code, label = "severe", "Depresión severa"
            domain_scores.append({"code": "B_AFFECT", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": phq9, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_AFFECT", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        # B_ANXIETY -> GAD7
        gad7 = self._get_float(encounter, self.CODES["GAD7"])
        if gad7 is not None:
            if gad7 <= 4:
                code, label = "minimal", "Sin ansiedad significativa"
            elif gad7 <= 9:
                code, label = "mild", "Ansiedad leve"
            elif gad7 <= 14:
                code, label = "moderate", "Ansiedad moderada"
            else:
                code, label = "severe", "Ansiedad severa"
            domain_scores.append({"code": "B_ANXIETY", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": gad7, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_ANXIETY", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        # B_UNCONTROLLED -> TFEQ-UNCONTROLLED
        uncontrolled = self._get_float(encounter, self.CODES["TFEQ_UNCONTROLLED"])
        if uncontrolled is not None:
            if uncontrolled <= 2.5:
                code, label = "normal", "Ingesta controlada"
            else:
                code, label = "elevated", "Ingesta no controlada patológica"
            domain_scores.append({"code": "B_UNCONTROLLED", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": uncontrolled, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_UNCONTROLLED", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        # B_EMOTIONAL -> TFEQ-EMOTIONAL
        emotional = self._get_float(encounter, self.CODES["TFEQ_EMOTIONAL"])
        if emotional is not None:
            if emotional <= 2.5:
                code, label = "normal", "Sin alimentación emocional"
            else:
                code, label = "elevated", "Alimentación emocional patológica"
            domain_scores.append({"code": "B_EMOTIONAL", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": emotional, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_EMOTIONAL", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        # B_COGNITIVE -> TFEQ-COGNITIVE
        cognitive = self._get_float(encounter, self.CODES["TFEQ_COGNITIVE"])
        if cognitive is not None:
            if cognitive <= 2.5:
                code, label = "low", "Baja restricción cognitiva"
            else:
                code, label = "active", "Restricción cognitiva activa"
            domain_scores.append({"code": "B_COGNITIVE", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": cognitive, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_COGNITIVE", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        # B_SLEEP -> AIS-001
        sleep = self._get_float(encounter, self.CODES["AIS"])
        if sleep is not None:
            if sleep <= 5:
                code, label = "normal", "Sueño normal"
            elif sleep <= 10:
                code, label = "borderline", "Riesgo de insomnio"
            else:
                code, label = "insomnia", "Insomnio probable"
            domain_scores.append({"code": "B_SLEEP", "label": label, "completeness_status": CompletenessStatus.COMPLETE.value, "score": sleep, "mapped_code": code})
        else:
            domain_scores.append({"code": "B_SLEEP", "label": "Unknown", "completeness_status": CompletenessStatus.INDETERMINATE.value, "score": None, "mapped_code": "unknown"})

        return AdjudicationResult(
            calculated_value="B Domain Scores Evaluated",
            confidence=1.0,
            estado_ui="CONFIRMED_ACTIVE",
            metadata={"domain_scores": domain_scores}
        )
