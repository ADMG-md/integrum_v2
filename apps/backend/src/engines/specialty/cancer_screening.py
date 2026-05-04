from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class CancerScreeningMotor(BaseClinicalMotor):
    """
    Obesity-Linked Cancer Screening Engine.

    Obesity is causally linked to 13+ cancers (IARC/WHO).
    This engine identifies screening gaps based on patient age, sex,
    and obesity status.

    Cancer types linked to obesity:
    - Endometrial, Esophageal adenocarcinoma, Gastric cardia
    - Liver, Kidney, Multiple myeloma, Meningioma
    - Pancreatic, Colorectal, Gallbladder
    - Breast (postmenopausal), Ovarian, Thyroid

    IARC Working Group, 2016. N Engl J Med 2016; 375:794-798.

    REQUIREMENT_ID: CANCER-SCREENING
    """

    REQUIREMENT_ID = "CANCER-SCREENING"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        bmi = encounter.bmi
        age_obs = encounter.get_observation("AGE-001")
        if not bmi or not age_obs:
            return False, "Cancer screening requires: BMI and Age."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        from src.engines.domain import safe_float

        bmi = encounter.bmi
        age = safe_float(encounter.get_observation("AGE-001").value)
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]

        if bmi is None or age is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes.",
            )

        findings = []
        actions = []
        gaps = 0

        # Colorectal cancer (both sexes, 45-75)
        if 45 <= age <= 75:
            findings.append("Screening CRC indicado (45-75 anos)")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Screening de cancer colorrectal (FIT anual o colonoscopia cada 10 anos)",
                    rationale="Obesidad aumenta riesgo de CRC en 30-70%. Screening desde los 45.",
                )
            )
            gaps += 1

        # Breast cancer (women, 40+)
        if not is_male and age >= 40:
            findings.append("Screening mama indicado (mujer >= 40 anos)")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Mamografia anual o bienal",
                    rationale="Obesidad postmenopausica aumenta riesgo de cancer de mama 20-40%.",
                )
            )
            gaps += 1

        # Endometrial cancer (women with obesity, any age)
        if not is_male and bmi >= 30:
            findings.append("Riesgo elevado de cancer endometrial")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="medium",
                    task="Evaluar sangrado uterino anormal. Considerar ecografia transvaginal si sintomatica.",
                    rationale=f"Obesidad (BMI {bmi:.1f}) aumenta riesgo de cancer endometrial 2-6x.",
                )
            )
            gaps += 1

        # Liver cancer (NAFLD/MASLD progression)
        if bmi >= 30:
            findings.append("Riesgo de cancer hepatico (via NAFLD)")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="medium",
                    task="Screening de HCC si cirrosis por NAFLD (ecografia + AFP cada 6 meses)",
                    rationale="NAFLD es causa creciente de HCC. Evaluar progresion a cirrosis.",
                )
            )

        # Kidney cancer
        if bmi >= 30 and age >= 40:
            findings.append("Riesgo de cancer renal")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="low",
                    task="Considerar ecografia renal en contexto de obesidad cronica",
                    rationale="Obesidad aumenta riesgo de cancer renal 1.5-2x.",
                )
            )

        # Pancreatic cancer
        if bmi >= 35:
            findings.append("Riesgo de cancer pancreatico")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="low",
                    task="Estar alerta a sintomas pancreaticos (dolor epigastrico, ictericia, diabetes nueva)",
                    rationale="Obesidad severa aumenta riesgo de cancer pancreatico.",
                )
            )

        # Prostate cancer (men, 50+)
        if is_male and age >= 50:
            findings.append("Screening prostata indicado (hombre >= 50 anos)")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="medium",
                    task="PSA + tacto rectal (discutir riesgos/beneficios)",
                    rationale="Obesidad asociada con cancer de prostata mas agresivo.",
                )
            )
            gaps += 1

        # Thyroid cancer
        if bmi >= 30:
            findings.append("Riesgo de cancer tiroideo")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="low",
                    task="Palpacion tiroidea anual. Ecografia si nodulo palpable.",
                    rationale="Obesidad aumenta riesgo de cancer tiroideo.",
                )
            )

        if gaps > 0:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"{gaps} gaps de screening de cancer identificados"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Sin gaps de screening de cancer identificados"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        explanation = (
            f"Screening de cancer en obesidad (BMI {bmi:.1f}): "
            f"Obesidad causa 13+ tipos de cancer. "
            f"{'; '.join(findings)}"
        )

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="CANCER-SCREENING",
                    value=gaps,
                    threshold="0",
                    display="Gaps de Screening de Cancer",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={"gaps": gaps, "findings": findings},
        )
