from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple, List

class SleepApneaPrecisionMotor(BaseClinicalMotor):
    """
    Motor de Tamizaje de Apnea Obstructiva del Sueño (STOP-Bang Score).
    Identifica riesgo de OSA basándose en variables clínicas y de estilo de vida.
    """

    REQUIREMENT_ID = "SLEEP-APNEA"
    
    CODES = {
        "SNORING": "LIFE-SNORING",
        "TIREDNESS": "LIFE-TIRED",
        "OBSERVED": "LIFE-APNEA",
        "PRESSURE": "I10", # Hypertension condition or 8480-6 > 130
        "BMI": "39156-5",
        "AGE": "AGE-001",
        "NECK": "NECK-001"
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Minimum data: At least BMI, Age and Sex (Metadata)
        if not encounter.bmi or not encounter.get_observation("AGE-001"):
            return False, "Se requiere IMC y Edad para tamizaje STOP-Bang."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        score = 0
        evidence = []
        
        # S - Snoring
        s_obs = encounter.get_observation(self.CODES["SNORING"])
        if s_obs and s_obs.value in [1, True, "Yes", "Si"]:
            score += 1
            evidence.append(ClinicalEvidence(type="Lifestyle", code="STOP-S", value="Yes", display="Ronca fuerte"))
            
        # T - Tiredness
        t_obs = encounter.get_observation(self.CODES["TIREDNESS"])
        if t_obs and t_obs.value in [1, True, "Yes", "Si"]:
            score += 1
            evidence.append(ClinicalEvidence(type="Lifestyle", code="STOP-T", value="Yes", display="Cansancio diurno"))

        # O - Observed apnea
        o_obs = encounter.get_observation(self.CODES["OBSERVED"])
        if o_obs and o_obs.value in [1, True, "Yes", "Si"]:
            score += 1
            evidence.append(ClinicalEvidence(type="Lifestyle", code="STOP-O", value="Yes", display="Apneas presenciadas"))

        # P - Pressure (HTN)
        sbp = encounter.get_observation("8480-6")
        if (sbp and float(sbp.value) >= 130) or encounter.has_condition("I10"):
            score += 1
            evidence.append(ClinicalEvidence(type="Clinical", code="STOP-P", value="Yes", display="HTN / Presión >= 130"))

        # B - BMI > 35
        bmi = encounter.bmi
        if bmi and bmi > 35:
            score += 1
            evidence.append(ClinicalEvidence(type="Calculation", code="STOP-B", value=round(bmi, 1), display="BMI > 35"))

        # A - Age > 50
        age = encounter.get_observation(self.CODES["AGE"])
        if age and float(age.value) > 50:
            score += 1
            evidence.append(ClinicalEvidence(type="Observation", code="STOP-A", value=float(age.value), display="Edad > 50"))

        # N - Neck > 40cm
        neck = encounter.get_observation(self.CODES["NECK"])
        if neck and float(neck.value) > 40:
            score += 1
            evidence.append(ClinicalEvidence(type="Observation", code="STOP-N", value=float(neck.value), display="Cuello > 40cm"))

        # G - Gender (Male)
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        if is_male:
            score += 1
            evidence.append(ClinicalEvidence(type="Metadata", code="STOP-G", value="Male", display="Sexo Masculino"))

        # Risk Stratification
        if score >= 5: risk = "Riesgo Alto de OSA"
        elif score >= 3: risk = "Riesgo Intermedio de OSA"
        else: risk = "Riesgo Bajo de OSA"

        # Athens Insomnia Scale Integration (Legacy Parity)
        ais_obs = encounter.get_observation("ATENAS-001")
        from src.engines.domain import safe_float
        ais_val = safe_float(ais_obs.value if ais_obs else None)
        if ais_val is not None and ais_val >= 6:
            risk += " + Insomnio Confirmado (Atenas)"
            evidence.append(ClinicalEvidence(type="Psychometry", code="ATENAS-001", value=ais_val, threshold=">=6", display="Insomnio Confirmado"))

        return AdjudicationResult(
            calculated_value=f"{risk} (Score: {score}/8)",
            confidence=0.9,
            evidence=evidence,
            explanation=f"Tamizaje STOP-Bang completado. " + ("Se recomienda estudio de sueño (Polisomnografía) por riesgo elevado." if score >= 3 else "Bajo riesgo de apnea obstructiva del sueño.")
        )
