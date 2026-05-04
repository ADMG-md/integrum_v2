from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple


class CVDReclassifierMotor(BaseClinicalMotor):
    """
    CVD Risk Reclassification for Statin Eligibility.

    Integrates ASCVD 10y risk with risk-enhancing factors to determine
    statin eligibility per ACC/AHA 2018 guidelines:

    Risk-enhancing factors:
    - Family history of premature ASCVD (M<55, F<65)
    - LDL >= 160 mg/dL
    - Metabolic syndrome
    - CKD (eGFR 15-59)
    - Chronic inflammatory conditions
    - High-risk ethnicity
    - TG >= 175 mg/dL
    - hs-CRP >= 2.0 mg/L
    - Lp(a) >= 50 mg/dL
    - ApoB >= 130 mg/dL
    - ABI < 0.9

    ACC/AHA 2018 Cholesterol Guidelines.

    REQUIREMENT_ID: CVD-RECLASSIFIER
    """

    REQUIREMENT_ID = "CVD-RECLASSIFIER"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        ldl = encounter.metabolic_panel.ldl_mg_dl
        if not ldl:
            return False, "CVD Reclassifier requires: LDL cholesterol."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        ldl = encounter.metabolic_panel.ldl_mg_dl
        tg = encounter.metabolic_panel.triglycerides_mg_dl
        hdl = encounter.metabolic_panel.hdl_mg_dl
        hs_crp = encounter.metabolic_panel.hs_crp_mg_l
        lpa = encounter.metabolic_panel.lpa_mg_dl
        apob = encounter.metabolic_panel.apob_mg_dl
        egfr = encounter.egfr_ckd_epi

        risk_factors = []

        # LDL >= 160
        if ldl >= 160:
            risk_factors.append(f"LDL >= 160 ({ldl} mg/dL)")

        # TG >= 175
        if tg and tg >= 175:
            risk_factors.append(f"TG >= 175 ({tg} mg/dL)")

        # Metabolic syndrome (3+ of: waist, TG, HDL, BP, glucose)
        metabolic_count = 0
        waist_obs = encounter.get_observation("WAIST-001")
        if waist_obs:
            waist = safe_float(waist_obs.value)
            is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
            if waist and waist > (102 if is_male else 88):
                metabolic_count += 1
        if tg and tg >= 150:
            metabolic_count += 1
        if hdl and hdl < (
            40 if encounter.metadata.get("sex", "").lower() in ["male", "m"] else 50
        ):
            metabolic_count += 1
        sbp_obs = encounter.get_observation("8480-6")
        if sbp_obs:
            sbp = safe_float(sbp_obs.value)
            if sbp and sbp >= 130:
                metabolic_count += 1
        glu = encounter.glucose_mg_dl
        if glu and glu >= 100:
            metabolic_count += 1
        if metabolic_count >= 3:
            risk_factors.append(f"Syndrome metabolico ({metabolic_count}/5 criterios)")

        # CKD
        if egfr and 15 <= egfr < 60:
            risk_factors.append(f"ERC (eGFR {egfr})")

        # hs-CRP >= 2.0
        if hs_crp and hs_crp >= 2.0:
            risk_factors.append(f"hs-CRP elevado ({hs_crp} mg/L)")

        # Lp(a) >= 50
        if lpa and lpa >= 50:
            risk_factors.append(f"Lp(a) elevada ({lpa} mg/dL)")

        # ApoB >= 130
        if apob and apob >= 130:
            risk_factors.append(f"ApoB elevado ({apob} mg/dL)")

        n_factors = len(risk_factors)

        # Statin eligibility
        if ldl >= 190:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Estatina de ALTA intensidad INDICADA (LDL >= 190)"
            explanation = (
                f"LDL: {ldl} mg/dL. Indicacion clase I para estatina alta intensidad."
            )
            confidence = 0.95
        elif n_factors >= 2:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Estatina INDICADA ({n_factors} factores de riesgo)"
            explanation = (
                f"LDL: {ldl} mg/dL. {n_factors} factores de riesgo: "
                f"{'; '.join(risk_factors)}. "
                f"ACC/AHA 2018: estatina de moderada-alta intensidad indicada."
            )
            confidence = 0.88
        elif n_factors == 1:
            estado = "PROBABLE_WARNING"
            verdict = f"Considerar estatina (1 factor de riesgo)"
            explanation = (
                f"LDL: {ldl} mg/dL. 1 factor de riesgo: {risk_factors[0]}. "
                f"Discutir riesgo/beneficio con paciente."
            )
            confidence = 0.80
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Estatina no indicada actualmente"
            explanation = f"LDL: {ldl} mg/dL. Sin factores de riesgo adicionales."
            confidence = 0.85

        actions = []
        if ldl >= 190:
            actions.append(
                ActionItem(
                    category="pharmacological",
                    priority="critical",
                    task="Iniciar estatina de alta intensidad (Atorvastatina 40-80mg o Rosuvastatina 20-40mg)",
                    rationale=f"LDL={ldl} >= 190 mg/dL. Indicacion clase I.",
                )
            )
        elif n_factors >= 2:
            actions.append(
                ActionItem(
                    category="pharmacological",
                    priority="high",
                    task="Iniciar estatina de moderada intensidad (Atorvastatina 10-20mg o Rosuvastatina 5-10mg)",
                    rationale=f"{n_factors} factores de riesgo + LDL={ldl}.",
                )
            )

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="CVD-RECLASSIFIER",
                    value=n_factors,
                    threshold="0",
                    display="Factores de Riesgo CV",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "risk_factors": risk_factors,
                "n_factors": n_factors,
                "ldl": ldl,
            },
        )
