from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple


class WomensHealthMotor(BaseClinicalMotor):
    """
    Women's Health Assessment Engine.

    Evaluates:
    1. PCOS (Rotterdam 2003) — requires 2 of 3:
       - Hyperandrogenism: FAI > 5 OR Ferriman-Gallwey >= 8
       - Oligo/anovulation: irregular cycles OR amenorrhea
       - Polycystic ovarian morphology: AMH > 4.5 ng/mL

    2. Pregnancy screening — gate for teratogenic medications
    3. Menopausal status — therapeutic implications
    4. Obstetric history — preeclampsia (2x CV risk), GDM (7x DM2 risk)

    REQUIREMENT_ID: WOMENS-HEALTH
    """

    REQUIREMENT_ID = "WOMENS-HEALTH"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        is_female = encounter.metadata.get("sex", "").lower() in ["female", "f"]
        if not is_female:
            return False, "WomensHealthMotor applies to female patients only."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        h = encounter.history
        if not h:
            return AdjudicationResult(
                calculated_value="Sin datos de salud femenina",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Sin historia clinica disponible.",
            )

        findings = []
        actions = []
        sop_criteria = 0

        # 1. PCOS Assessment (Rotterdam 2003)
        # Criterion 1: Hyperandrogenism
        has_hyperandrogenism = False

        # Via FAI (Free Androgen Index)
        testo = encounter.metabolic_panel.testosterone_total_ng_dl
        shbg = encounter.metabolic_panel.shbg_nmol_l
        if testo and shbg and shbg > 0:
            fai = (testo / shbg) * 100
            if fai > 5:
                has_hyperandrogenism = True
                findings.append(f"Hiperandrogenismo bioquimico (FAI: {fai:.1f})")

        # Via Ferriman-Gallwey
        fg_score = h.ferriman_gallwey_score
        if fg_score is not None and fg_score >= 8:
            has_hyperandrogenism = True
            findings.append(f"Hiperandrogenismo clinico (Ferriman-Gallwey: {fg_score})")

        if has_hyperandrogenism:
            sop_criteria += 1

        # Criterion 2: Oligo/anovulation
        cycle_irregular = h.cycle_regularity in ["irregular", "amenorrhea"]
        if cycle_irregular:
            sop_criteria += 1
            findings.append(f"Oligo/anovulacion (ciclos: {h.cycle_regularity})")

        # Criterion 3: Polycystic ovarian morphology (AMH)
        amh = encounter.metabolic_panel.amh_ng_ml
        if amh is not None and amh > 4.5:
            sop_criteria += 1
            findings.append(f"Morfologia ovarica poliquistica (AMH: {amh} ng/mL)")

        # SOP diagnosis
        sop_confirmed = sop_criteria >= 2
        if sop_confirmed:
            findings.append(f"SOP confirmado ({sop_criteria}/3 criterios Rotterdam)")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Confirmar SOP con ecografia transvaginal y perfil hormonal completo",
                    rationale=f"{sop_criteria}/3 criterios de Rotterdam cumplidos.",
                )
            )
            actions.append(
                ActionItem(
                    category="pharmacological",
                    priority="medium",
                    task="Considerar metformina si resistencia a insulina + SOP",
                    rationale="Metformina mejora ovulacion y sensibilidad a insulina en SOP.",
                )
            )

        # 2. Pregnancy screening
        pregnancy = h.pregnancy_status
        if pregnancy == "pregnant":
            findings.append(
                "Paciente embarazada — verificar medicamentos teratogenicos"
            )
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="critical",
                    task="SUSPENDER: estatinas, SGLT2i, ACE/ARB si estan prescritos",
                    rationale="Medicamentos teratogenicos contraindicados en embarazo.",
                )
            )

        # 3. Menopausal status
        menopause = h.menopausal_status
        if menopause == "post":
            findings.append("Post-menopausica — mayor riesgo cardiovascular")
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="medium",
                    task="Evaluar necesidad de terapia hormonal de reemplazo (HRT)",
                    rationale="HRT puede mejorar sintomas y riesgo CV si iniciada <60 anos.",
                )
            )
        elif menopause == "peri":
            findings.append("Peri-menopausica — monitorear cambios metabolicos")

        # 4. Obstetric history
        ob_risks = []
        if h.has_history_preeclampsia:
            ob_risks.append("Preeclampsia previa (riesgo CV 2x)")
        if h.has_history_gestational_diabetes:
            ob_risks.append("Diabetes gestacional previa (riesgo DM2 7x)")

        if ob_risks:
            findings.extend(ob_risks)
            actions.append(
                ActionItem(
                    category="diagnostic",
                    priority="high",
                    task="Screening cardiovascular intensificado por historia obstetrica",
                    rationale="Historia obstetrica de alto riesgo cardiovascular.",
                )
            )

        # Classification
        if sop_confirmed:
            estado = "CONFIRMED_ACTIVE"
            verdict = "Sindrome de Ovario Poliquistico confirmado"
            confidence = 0.90
        elif sop_criteria == 1:
            estado = "PROBABLE_WARNING"
            verdict = "Sospecha de SOP (1/3 criterios)"
            confidence = 0.75
        elif pregnancy == "pregnant":
            estado = "CONFIRMED_ACTIVE"
            verdict = "Embarazo — verificar seguridad de medicamentos"
            confidence = 0.95
        elif ob_risks:
            estado = "PROBABLE_WARNING"
            verdict = "Factores de riesgo obstetrico identificados"
            confidence = 0.85
        else:
            estado = "INDETERMINATE_LOCKED"
            verdict = "Salud femenina sin hallazgos de preocupacion"
            confidence = 0.85

        explanation = "; ".join(findings) if findings else "Sin hallazgos relevantes."

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="WOMENS-HEALTH",
                    value=sop_criteria,
                    threshold=">=2 para SOP",
                    display="Evaluacion de Salud Femenina",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            action_checklist=actions,
            metadata={
                "sop_criteria": sop_criteria,
                "sop_confirmed": sop_confirmed,
                "pregnancy_status": pregnancy,
                "menopausal_status": menopause,
                "ob_risk_factors": ob_risks,
                "findings": findings,
            },
        )
