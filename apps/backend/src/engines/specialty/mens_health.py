from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple


class MensHealthMotor(BaseClinicalMotor):
    """
    Men's Health Assessment Engine.

    Evaluates:
    1. Hypogonadism — symptoms + biochemistry:
       - Total T < 300 ng/dL + symptoms (ED, low libido, fatigue)
       - Free T (Vermeulen) < 50 pg/mL
       - LH/FSH to differentiate primary vs secondary

    2. Prostate health — PSA screening
    3. Erectile dysfunction — IIEF-5 score
    4. Androgenic alopecia — Hamilton-Norwood
    5. Gynecomastia

    REQUIREMENT_ID: MENS-HEALTH
    """

    REQUIREMENT_ID = "MENS-HEALTH"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        if not is_male:
            return False, "MensHealthMotor applies to male patients only."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        h = encounter.history
        if not h:
            return AdjudicationResult(
                calculated_value="Sin datos de salud masculina",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Sin historia clinica disponible.",
            )

        findings = []
        actions = []
        mp = encounter.metabolic_panel

        # 1. Hypogonadism assessment
        hypo_risk = 0

        # Total testosterone
        testo = mp.testosterone_total_ng_dl
        if testo is not None:
            if testo < 300:
                hypo_risk += 2
                findings.append(f"Testosterona total baja ({testo} ng/dL)")
            elif testo < 350:
                hypo_risk += 1
                findings.append(f"Testosterona total limtrofe ({testo} ng/dL)")

        # Free testosterone (from FreeTestosterone calculation)
        free_t_obs = encounter.get_observation("FREE-T")
        if free_t_obs:
            free_t = safe_float(free_t_obs.value)
            if free_t is not None and free_t < 50:
                hypo_risk += 2
                findings.append(f"Testosterona libre baja ({free_t} pg/mL)")

        # Symptoms
        if h.has_erectile_dysfunction:
            hypo_risk += 1
            findings.append("Disfuncion erectil reportada")

        # LH/FSH for differentiation
        lh = mp.lh_u_l
        fsh = mp.fsh_u_l
        if testo is not None and testo < 300 and lh is not None:
            if lh < 5:
                findings.append("Hipogonadismo secundario probable (LH baja)")
                actions.append(
                    ActionItem(
                        category="diagnostic",
                        priority="high",
                        task="Evaluar eje hipotalamo-hipofisario (prolactina, ferritina, RMN hipofisis)",
                        rationale=f"T={testo}, LH={lh}. LH baja sugiere origen central.",
                    )
                )
            else:
                findings.append("Hipogonadismo primario probable (LH normal/alta)")

        # 2. Prostate health
        psa = mp.psa_ng_ml
        if psa is not None:
            if psa > 10:
                findings.append(
                    f"PSA muy elevado ({psa} ng/mL) — alto riesgo de cancer"
                )
                actions.append(
                    ActionItem(
                        category="referral",
                        priority="critical",
                        task="Referencia URGENTE a urologia para biopsia prostatica",
                        rationale=f"PSA={psa} > 10 ng/mL. Alto riesgo de cancer de prostata.",
                    )
                )
            elif psa > 4:
                findings.append(f"PSA elevado ({psa} ng/mL)")
                actions.append(
                    ActionItem(
                        category="referral",
                        priority="high",
                        task="Referencia a urologia para evaluacion prostatica",
                        rationale=f"PSA={psa} > 4 ng/mL.",
                    )
                )
            elif h.has_prostate_issues:
                findings.append("Problemas prostaticos reportados")

        # 3. Erectile dysfunction (IIEF-5)
        iief5 = h.iief5_score
        if iief5 is not None:
            if iief5 <= 7:
                findings.append(f"Disfuncion erectil severa (IIEF-5: {iief5})")
            elif iief5 <= 11:
                findings.append(f"Disfuncion erectil moderada-severa (IIEF-5: {iief5})")
            elif iief5 <= 16:
                findings.append(f"Disfuncion erectil moderada (IIEF-5: {iief5})")
            elif iief5 <= 21:
                findings.append(f"Disfuncion erectil leve (IIEF-5: {iief5})")

        # 4. Androgenic alopecia
        if h.has_male_pattern_baldness:
            findings.append("Alopecia androgenica")

        # 5. Gynecomastia
        if h.has_gynecomastia:
            findings.append("Ginecomastia")
            if testo is not None and testo < 300:
                actions.append(
                    ActionItem(
                        category="diagnostic",
                        priority="medium",
                        task="Evaluar ratio estradiol/testosterona como causa de ginecomastia",
                        rationale="Ginecomastia + hipogonadismo sugiere desbalance hormonal.",
                    )
                )

        # Classification
        if hypo_risk >= 3:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Hipogonadismo masculino confirmado"
            confidence = 0.88
        elif hypo_risk >= 2:
            estado = "PROBABLE_WARNING"
            verdict = "Sospecha de hipogonadismo"
            confidence = 0.80
        elif psa is not None and psa > 4:
            estado = "CONFIRMED_ACTIVE"
            verdict = "PSA elevado — evaluacion urologica indicada"
            confidence = 0.85
        elif findings:
            estado = "PROBABLE_WARNING"
            verdict = "Hallazgos de salud masculina identificados"
            confidence = 0.78
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Salud masculina sin hallazgos de preocupacion"
            confidence = 0.85

        explanation = "; ".join(findings) if findings else "Sin hallazgos relevantes."

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="MENS-HEALTH",
                    value=hypo_risk,
                    threshold="0",
                    display="Evaluacion de Salud Masculina",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "hypogonadism_risk": hypo_risk,
                "testosterone_total": testo,
                "psa": psa,
                "iief5_score": iief5,
                "findings": findings,
            },
        )
