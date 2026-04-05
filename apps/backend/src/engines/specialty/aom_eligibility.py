from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple


class ObesityPharmaEligibilityMotor(BaseClinicalMotor):
    """
    Anti-Obesity Medication (AOM) Eligibility Engine.

    Evaluates FDA criteria for anti-obesity medication eligibility:
    - BMI >= 30: Eligible for any FDA-approved AOM
    - BMI >= 27 + >=1 comorbidity: Eligible for any FDA-approved AOM

    Specific medication criteria:
    - Semaglutide 2.4mg (Wegovy): BMI >= 30 or >= 27 + comorbidity
    - Tirzepatide (Zepbound): BMI >= 30 or >= 27 + comorbidity
    - Liraglutide 3.0mg (Saxenda): BMI >= 30 or >= 27 + comorbidity
    - Phentermine/Topiramate (Qsymia): BMI >= 30 or >= 27 + comorbidity
    - Naltrexone/Bupropion (Contrave): BMI >= 30 or >= 27 + comorbidity
    - Orlistat (Xenical/Alli): BMI >= 30 or >= 27 + comorbidity

    Contraindications checked:
    - GLP-1/GIP: TCM/MEN2, pancreatitis, pregnancy
    - Phentermine: Uncontrolled HTN, CAD, hyperthyroidism, glaucoma
    - Naltrexone/Bupropion: Seizures, eating disorders, uncontrolled HTN, MAOI use
    - Orlistat: Chronic malabsorption, cholestasis

    FDA Guidance 2024, SELECT trial, SURMOUNT trials.

    REQUIREMENT_ID: AOM-ELIGIBILITY
    """

    REQUIREMENT_ID = "AOM-ELIGIBILITY"

    COMORBIDITIES = {
        "has_hypertension",
        "has_type2_diabetes",
        "has_dyslipidemia",
        "has_osa",
        "has_nafld",
        "has_ckd",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        bmi = encounter.bmi
        if not bmi:
            return False, "AOM Eligibility requires: BMI."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        bmi = encounter.bmi
        h = encounter.history
        if not h or bmi is None:
            return AdjudicationResult(
                calculated_value="Sin historia clínica o BMI",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Se requiere historia clínica y BMI para evaluar elegibilidad.",
            )

        comorbidities = [c for c in self.COMORBIDITIES if getattr(h, c, False)]
        eligible = bmi >= 30 or (bmi >= 27 and len(comorbidities) >= 1)

        findings: list[str] = []
        actions: list[ActionItem] = []
        explanation = ""

        if not eligible:
            estado = "INDETERMINATE_LOCKED"
            verdict = "No elegible para farmacoterapia anti-obesidad"
            explanation = (
                f"BMI: {bmi:.1f}. Criterio FDA: BMI >= 30 o >= 27 + comorbilidad. "
                f"Comorbilidades: {len(comorbidities)}."
            )
            confidence = 0.90
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Elegible para farmacoterapia anti-obesidad (BMI {bmi:.1f})"

            if bmi >= 30:
                findings.append(
                    f"BMI {bmi:.1f} >= 30 — elegible para cualquier AOM aprobado por FDA"
                )
            else:
                findings.append(
                    f"BMI {bmi:.1f} >= 27 + {len(comorbidities)} comorbilidad(es) — "
                    f"elegible para AOM"
                )

            # GLP-1/GIP recommendation (first-line per SELECT 2024)
            glp1_contraindicated = False
            if h.pregnancy_status == "pregnant":
                findings.append("GLP-1/GIP contraindicado: embarazo")
                glp1_contraindicated = True
            if h.has_eating_disorder_history:
                findings.append("GLP-1/GIP: precaución con historia de TCA")
            if h.has_seizures_history:
                findings.append("GLP-1/GIP: precaución con historia de convulsiones")

            if not glp1_contraindicated:
                actions.append(
                    ActionItem(
                        category="pharmacological",
                        priority="high",
                        task="Considerar GLP-1/GIP como primera línea (semaglutida 2.4mg o tirzepatida)",
                        rationale="SELECT trial: reducción de eventos CV con semaglutida en obesidad.",
                    )
                )

            # Phentermine contraindications
            if (
                h.has_hypertension
                or h.has_coronary_disease
                or h.has_glaucoma
                or h.has_hypothyroidism
            ):
                findings.append("Fentermina contraindicada por comorbilidades")
            else:
                actions.append(
                    ActionItem(
                        category="pharmacological",
                        priority="medium",
                        task="Fentermina/topiramato como alternativa de bajo costo",
                        rationale="Eficaz pero requiere monitoreo de efectos adversos.",
                    )
                )

            # Naltrexone/Bupropion contraindications
            if h.has_seizures_history or h.has_eating_disorder_history:
                findings.append(
                    "Naltrexona/bupropión contraindicado (convulsiones/TCA)"
                )
            else:
                actions.append(
                    ActionItem(
                        category="pharmacological",
                        priority="medium",
                        task="Naltrexona/bupropión como alternativa para hambre emocional",
                        rationale="Eficaz para fenotipo de hambre emocional/cerebro hambriento.",
                    )
                )

            confidence = 0.92

        explanation = (
            "; ".join(findings) if findings else explanation if not eligible else ""
        )

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="AOM-ELIGIBILITY",
                    value=bmi,
                    threshold=">=30 o >=27+comorbilidad",
                    display="Elegibilidad Farmacoterapia Anti-Obesidad",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "eligible": eligible,
                "bmi": bmi,
                "comorbidities": comorbidities,
                "n_comorbidities": len(comorbidities),
            },
        )
