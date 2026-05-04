from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class KFREMotor(BaseClinicalMotor):
    """
    Kidney Failure Risk Equation (KFRE) — 2-year and 5-year risk.

    Predicts progression to kidney failure (dialysis/transplant)
    in patients with CKD stages 3-5.

    4-variable model: age, sex, eGFR, UACR

    Tangri et al., 2011 (Lancet). Updated 2016.
    Validated in >30,000 patients across 31 countries.

    Risk thresholds:
    <5% at 5 years: Low risk - monitor annually
    5-25% at 5 years: Moderate risk - nephrology referral
    >25% at 5 years: High risk - urgent nephrology referral

    REQUIREMENT_ID: KFRE-2016
    """

    REQUIREMENT_ID = "KFRE-2016"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        egfr = encounter.egfr_ckd_epi
        uacr = encounter.uacr
        age_obs = encounter.get_observation("AGE-001")
        if not all([egfr, uacr, age_obs]):
            return False, "KFRE requires: eGFR, UACR, and Age."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        egfr = encounter.egfr_ckd_epi
        uacr = encounter.uacr
        age = safe_float(encounter.get_observation("AGE-001").value)
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]

        if egfr is None or uacr is None or age is None:
            return AdjudicationResult(
                calculated_value="No calculable",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Datos insuficientes para calcular KFRE.",
            )

        # 4-variable KFRE (Tangri 2016)
        # Log-linear model with spline terms
        import math

        age_term = 0.0299 * (age - 60) if age > 60 else 0
        egfr_term = -0.584 * math.log(max(egfr, 5))
        uacr_term = 0.417 * math.log(max(uacr, 1))
        sex_term = 0.399 if is_male else 0

        linear_predictor = age_term + egfr_term + uacr_term + sex_term

        # Baseline survival at 2 and 5 years
        s2 = 0.9793
        s5 = 0.9415

        risk_2y = 1 - (s2 ** math.exp(linear_predictor))
        risk_5y = 1 - (s5 ** math.exp(linear_predictor))

        risk_2y = round(min(risk_2y * 100, 100), 1)
        risk_5y = round(min(risk_5y * 100, 100), 1)

        findings = []
        actions = []

        if risk_5y > 25:
            estado = "CONFIRMED_ACTIVE"
            findings.append(f"Riesgo ALTO de falla renal: {risk_5y}% a 5 anos")
            findings.append(f"Riesgo a 2 anos: {risk_2y}%")
            actions.append(
                ActionItem(
                    category="referral",
                    priority="critical",
                    task="Referencia URGENTE a nefrologia",
                    rationale=f"KFRE 5y={risk_5y}% (>25% = alto riesgo). Preparar acceso vascular.",
                )
            )
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Evaluar preparacion para terapia de reemplazo renal",
                    rationale="Riesgo >25% a 5 anos requiere planificacion anticipada.",
                )
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif risk_5y > 5:
            estado = "CONFIRMED_ACTIVE"
            findings.append(f"Riesgo MODERADO de falla renal: {risk_5y}% a 5 anos")
            findings.append(f"Riesgo a 2 anos: {risk_2y}%")
            actions.append(
                ActionItem(
                    category="referral",
                    priority="high",
                    task="Referencia a nefrologia",
                    rationale=f"KFRE 5y={risk_5y}% (5-25% = riesgo moderado).",
                )
            )
            actions.append(
                ActionItem(
                    category="pharmacological",
                    priority="high",
                    task="Optimizar SGLT2i si no contraindicado",
                    rationale="SGLT2i reduce progresion de ERC en 39%.",
                )
            )
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "INDETERMINATE_LOCKED"
            findings.append(f"Riesgo BAJO de falla renal: {risk_5y}% a 5 anos")
            findings.append(f"Riesgo a 2 anos: {risk_2y}%")
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        explanation = (
            f"KFRE: {risk_5y}% a 5 anos, {risk_2y}% a 2 anos. "
            f"(eGFR={egfr}, UACR={uacr}, edad={int(age)}). "
            f"{'; '.join(findings)}"
        )

        return AdjudicationResult(
            calculated_value=f"Riesgo falla renal: {risk_5y}% a 5 anos",
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="KFRE-5Y",
                    value=risk_5y,
                    threshold="<5%",
                    display="KFRE 5-Year Risk",
                ),
                ClinicalEvidence(
                    type="Calculation",
                    code="KFRE-2Y",
                    value=risk_2y,
                    threshold="<5%",
                    display="KFRE 2-Year Risk",
                ),
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "risk_2y": risk_2y,
                "risk_5y": risk_5y,
                "egfr": egfr,
                "uacr": uacr,
                "findings": findings,
            },
        )
