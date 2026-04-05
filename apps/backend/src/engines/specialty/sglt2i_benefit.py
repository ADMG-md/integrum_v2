from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple


class SGLT2iBenefitMotor(BaseClinicalMotor):
    """
    SGLT2 Inhibitor Cardio-Renal Benefit Estimator.

    Estimates absolute risk reduction for MACE, HF hospitalization,
    and CKD progression based on patient profile.

    Evidence from:
    - Zinman et al., 2015. NEJM 373: 2117-2128. doi: 10.1056/NEJMoa1504720.
      EMPA-REG OUTCOME: 14% MACE reduction, 38% CV death reduction.
    - Neal et al., 2017. NEJM 377: 644-657. doi: 10.1056/NEJMoa1611925.
      CANVAS: 14% MACE reduction, 33% HF hospitalization reduction.
    - Wiviott et al., 2019. NEJM 380: 347-357. doi: 10.1056/NEJMoa1812389.
      DECLARE-TIMI 58: 17% CV death/HF hospitalization reduction.
    - Perkovic et al., 2019. NEJM 380: 2295-2306. doi: 10.1056/NEJMoa1904119.
      CREDENCE: 30% ESRD/dialysis/death reduction in CKD.
    - Heerspink et al., 2020. NEJM 383: 1436-1446. doi: 10.1056/NEJMoa2024816.
      DAPA-CKD: 39% CKD progression reduction.
    - McMurray et al., 2019. NEJM 381: 1995-2008. doi: 10.1056/NEJMoa1911303.
      DAPA-HF: 26% HF hospitalization/CV death reduction (non-diabetic HF).

    REQUIREMENT_ID: SGLT2I-BENEFIT
    """

    REQUIREMENT_ID = "SGLT2I-BENEFIT"

    SGLT2_CODES = {
        "EMPAGLIFLOZIN",
        "DAPAGLIFLOZIN",
        "CANAGLIFLOZIN",
        "ERTUGLIFLOZIN",
        "SGLT2I",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        has_t2dm = encounter.history.has_type2_diabetes if encounter.history else False
        has_ckd = encounter.history.has_ckd if encounter.history else False
        has_hf = encounter.has_condition("I50") or encounter.has_condition("I50.9")
        egfr = encounter.egfr_ckd_epi
        if not any([has_t2dm, has_ckd, has_hf]):
            return False, "SGLT2i benefit requires: T2DM, CKD, or Heart Failure."
        if egfr and egfr < 20:
            return False, f"eGFR {egfr} < 20. SGLT2i no indicado (iniciar dialisis)."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        from src.engines.domain import safe_float

        has_t2dm = encounter.history.has_type2_diabetes if encounter.history else False
        has_ckd = encounter.history.has_ckd if encounter.history else False
        has_hf = encounter.has_condition("I50") or encounter.has_condition("I50.9")
        has_ascvd = (
            encounter.has_condition("I25.1")
            or encounter.has_condition("I21")
            or encounter.has_condition("I63")
        )
        egfr = encounter.egfr_ckd_epi
        uacr = encounter.uacr

        findings = []
        actions = []
        benefits = []

        # MACE reduction (14% RRR in meta-analysis)
        if has_t2dm and has_ascvd:
            benefits.append("Reduccion de MACE: 14% RRR (NNT ~56 a 3 anos)")
            findings.append("Beneficio cardiovascular establecido")

        # HF hospitalization reduction (31% RRR)
        if has_t2dm or has_hf:
            benefits.append(
                "Reduccion de hospitalizacion por IC: 31% RRR (NNT ~28 a 2.5 anos)"
            )
            findings.append("Beneficio en insuficiencia cardiaca")

        # CKD progression reduction (39% RRR in CREDENCE)
        if has_ckd or (egfr and egfr < 60):
            benefits.append(
                "Reduccion de progresion de ERC: 39% RRR (NNT ~22 a 2.5 anos)"
            )
            findings.append("Beneficio renal establecido")

        # Weight loss benefit
        bmi = encounter.bmi
        if bmi and bmi >= 25:
            benefits.append("Perdida de peso adicional: 2-3 kg promedio")
            findings.append("Beneficio metabolico adicional")

        # eGFR safety check
        if egfr:
            if egfr < 30:
                findings.append(f"eGFR {egfr}: Monitorizar funcion renal de cerca")
                actions.append(
                    ActionItem(
                        category="diagnostic",
                        priority="high",
                        task="Control de funcion renal a las 2-4 semanas de inicio",
                        rationale=f"eGFR={egfr}. Caida inicial de eGFR es esperada (hemodinamica).",
                    )
                )
            elif egfr < 45:
                findings.append(f"eGFR {egfr}: Beneficio renal maximizado")

        # UACR benefit
        if uacr and uacr > 30:
            benefits.append(
                f"Reduccion de albuminuria esperada (UACR actual: {uacr} mg/g)"
            )
            findings.append("Beneficio antiproteinurico")

        if benefits:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"SGLT2i INDICADO: {len(benefits)} beneficios identificados"
            explanation = (
                f"Beneficio cardio-renal de SGLT2i: {'; '.join(benefits)}. "
                f"{'; '.join(findings)}"
            )
            confidence = 0.92
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "SGLT2i: Beneficio no claramente establecido"
            explanation = "No se identificaron beneficios cardio-renales claros."
            confidence = 0.70

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="SGLT2I-BENEFIT",
                    value=len(benefits),
                    threshold=">=1",
                    display="Beneficios SGLT2i Identificados",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={"benefits": benefits, "findings": findings},
        )
