from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class Lifestyle360Motor(BaseClinicalMotor):
    """
    Evaluates metabolic impact of lifestyle habits (Sleep, Stress, Exercise).
    Integrates Athens Insomnia Scale (AIS) and TFEQ-R18 correlation.

    Evidence:
    - AIS: Soldatos et al., 2000. J Psychosom Res 49(1): 29-35.
      Athens Insomnia Scale: score >= 6 = clinical insomnia.
    - TFEQ-R18: de Lauzon et al., 2004. Appetite 42(1): 9-16.
      Three-Factor Eating Questionnaire: emotional eating > 2.5 = high risk.
    - Physical activity: WHO Guidelines 2020. >= 150 min/week moderate, >= 300 for optimal.
    - Sleep deprivation & insulin resistance: Spiegel et al., 1999. Lancet 354: 1435-1439.
      6 nights of 4h sleep reduces glucose tolerance by 40%.

    REQUIREMENT_ID: LIFESTYLE-360
    """

    REQUIREMENT_ID = "LIFESTYLE-360"
    ENGINE_NAME = "Lifestyle360Motor"
    ENGINE_VERSION = "0.2.0"  # Hardened Logic

    CODES = {
        "AF_MINUTES": "LIFE-EXERCISE",  # Weekly total minutes
        "STRESS_LEVEL": "LIFE-STRESS",  # VAS 1-10
        "SLEEP_HOURS": "LIFE-SLEEP",  # Quantity
        "ATHENS_INSOMNIA": "AIS-001",  # Quality (Score >= 6 = Insomnia)
        "TFEQ_EMOTIONAL": "TFEQ-EMOTIONAL",
        "TFEQ_UNCONTROLLED": "TFEQ-UNCONTROLLED",
    }

    def run(self, encounter: Encounter, context: dict = None) -> AdjudicationResult:
        """Standardized interface for SpecialtyRunner"""
        return self.compute(encounter)

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Minimal lifestyle data check
        codes_to_check = [
            self.CODES["AF_MINUTES"],
            self.CODES["STRESS_LEVEL"],
            self.CODES["SLEEP_HOURS"],
        ]
        if not any(encounter.get_observation(c) for c in codes_to_check):
            return (
                False,
                "Faltan pilares básicos de Estilo de Vida (AF, Estrés o Sueño).",
            )
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        af = encounter.get_observation(self.CODES["AF_MINUTES"])
        stress = encounter.get_observation(self.CODES["STRESS_LEVEL"])
        hours = encounter.get_observation(self.CODES["SLEEP_HOURS"])
        ais = encounter.get_observation(self.CODES["ATHENS_INSOMNIA"])
        tfeq_emo = encounter.get_observation(self.CODES["TFEQ_EMOTIONAL"])
        tfeq_unc = encounter.get_observation(self.CODES["TFEQ_UNCONTROLLED"])

        findings = []
        evidence = []
        explanation = (
            "Evaluación Integral del Entorno del Paciente (Pilares Estilo de Vida). "
        )
        confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED]

        # 1. PUNTUACIÓN DE SUEÑO (Calidad vs Cantidad)
        is_insomniac = False
        if ais and float(ais.value) >= 6:
            is_insomniac = True
            findings.append("Insomnio Clínico Detectado (AIS >= 6)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code=self.CODES["ATHENS_INSOMNIA"],
                    value=ais.value,
                    threshold=">=6",
                    display="Escala Atenas",
                )
            )

        if hours and float(hours.value) < 6:
            findings.append("Privación Crónica de Sueño (< 6h)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code=self.CODES["SLEEP_HOURS"],
                    value=hours.value,
                    threshold="<6h",
                    display="Horas/Noche",
                )
            )
            if is_insomniac:
                findings.append("Riesgo Circadiano Crítico (Déficit + Mala Calidad)")
                explanation += "Déficit de sueño dual detectado. Alta probabilidad de resistencia periférica a la insulina. "

        # 2. CARGA ALOSTÁTICA (Estrés)
        if stress and float(stress.value) > 7:
            findings.append("Carga Alostática Elevada (Estrés Crónico)")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code=self.CODES["STRESS_LEVEL"],
                    value=stress.value,
                    threshold=">7/10",
                    display="Estrés VAS",
                )
            )
            if tfeq_emo and float(tfeq_emo.value) > 2.5:
                findings.append("Eje Neuro-Endocrino: Hambre por Estrés")
                explanation += "Correlación diagnóstica entre estrés subjetivo e ingesta emocional. "

        # 3. ACTIVIDAD FÍSICA (Sabotaje Sedentario)
        if af:
            af_val = float(af.value)
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code=self.CODES["AF_MINUTES"],
                    value=af_val,
                    display="Actividad Física (min/sem)",
                )
            )
            if af_val < 150:
                findings.append("Sabotaje Sedentario (AF < 150 min/sem)")
                explanation += (
                    "No se alcanzan las metas mínimas OMS de salud metabólica. "
                )
            elif af_val >= 300:
                findings.append("Protección Metabólica por Ejercicio AF > 300")
                explanation += "Nivel de actividad deportiva protector contra enfermedades crónicas. "

        return AdjudicationResult(
            calculated_value=" | ".join(findings)
            if findings
            else "Estilo de Vida en Rango de Seguridad",
            confidence=confidence,
            evidence=evidence,
            explanation=explanation.strip(),
            estado_ui="CONFIRMED_ACTIVE" if findings else "INDETERMINATE_LOCKED",
        )
