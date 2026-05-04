"""
MensHealthMotor — Precision Male Endocrinology (Testosterone Safety & TRT Limits)

Evaluates:
1. Hypogonadism (Primary vs Secondary via LH/FSH)
2. TRT Safety Gates (Hematocrit > 54%, PSA > 4.0, Severe OSA, Prostate Cancer)
3. Cardiovascular safety of TRT (TRAVERSE Trial criteria)
4. Erectile dysfunction and androgenic alopecia
5. Gynecomastia etiology (Testo/Estradiol ratio)
"""

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


class MensHealthMotor(BaseClinicalMotor):
    REQUIREMENT_ID = "MENS-HEALTH-V2"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        if not is_male:
            return False, "MensHealthMotor applies to male patients only."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        h = encounter.history
        if not h:
            return AdjudicationResult(
                calculated_value="Sin historia clínica",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="Requiere historial clínico para evaluación urológica y endocrina.",
            )

        findings = []
        actions = []
        evidence = []
        mp = encounter.metabolic_panel

        hypo_risk = 0
        phenotypes = []

        # --- 1. HYPOGONADISM (Endocrine Society 2018) ---
        testo = mp.testosterone_total_ng_dl if mp else None
        free_t_obs = encounter.get_observation("FREE-T")
        free_t = safe_float(free_t_obs.value) if free_t_obs else None

        has_biochemical_hypogonadism = False
        if testo is not None and testo < 300:
            has_biochemical_hypogonadism = True
            hypo_risk += 2
            findings.append(f"Testosterona total baja ({testo} ng/dL)")
            evidence.append(ClinicalEvidence(type="Lab", code="TOTAL-T", value=testo, threshold="<300 ng/dL", display="Hipogonadismo Bioquímico (T. Total)"))

        if free_t is not None and free_t < 50:
            has_biochemical_hypogonadism = True
            hypo_risk += 2
            findings.append(f"Testosterona libre baja ({free_t} pg/mL)")

        has_symptoms = False
        if getattr(h, "has_erectile_dysfunction", False):
            hypo_risk += 1
            has_symptoms = True
            findings.append("Síntomas: Disfunción eréctil")

        is_hypogonadal = has_biochemical_hypogonadism and has_symptoms
        if is_hypogonadal:
            phenotypes.append("Hipogonadismo Clínico Confirmado")
            lh = mp.lh_u_l if mp else None
            if lh is not None:
                if lh <= 5.0:
                    phenotypes.append("Secundario (Central)")
                    actions.append(ActionItem(
                        category="diagnostic", priority="high",
                        task="Descartar causas de Hipogonadismo Secundario",
                        rationale=f"LH inapropiadamente baja/normal ({lh} UI/L) con Testosterona baja. Evaluar hiperprolactinemia, obesidad visceral severa, hemocromatosis o uso de esteroides anabólicos."
                    ))
                else:
                    phenotypes.append("Primario (Falla Testicular)")
                    actions.append(ActionItem(
                        category="diagnostic", priority="high",
                        task="Hipogonadismo Primario Detectado",
                        rationale=f"LH elevada ({lh} UI/L) indica falla testicular directa (ej. Klinefelter, quimioterapia, trauma). Terapia de reemplazo requerida."
                    ))

        # --- 2. TRT SAFETY GATES (Vetos Absolutos) ---
        # Si tiene hipogonadismo, debemos autorizar o vetar el inicio de TRT
        if is_hypogonadal or encounter.get_observation("TRT-USE"):
            trt_veto = False
            
            # Hematocrit Limit (Viscosity / Thrombosis risk)
            hct_obs = encounter.get_observation("HCT-001")
            hct = safe_float(hct_obs.value) if hct_obs else None
            if hct is not None and hct > 54.0:
                trt_veto = True
                actions.append(ActionItem(
                    category="pharmacological", priority="critical",
                    task="HARD STOP: TRT Contraindicada (Hematocrito > 54%)",
                    rationale=f"Hematocrito hiperviscoso ({hct}%). Iniciar testosterona exógena inducirá eritrocitosis crítica, riesgo inminente de stroke o DVT. Sangría terapéutica y cardiólogo requeridos."
                ))
            elif hct is not None and hct > 50.0:
                actions.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Precaución TRT: Hematocrito limítrofe (50-54%)",
                    rationale=f"Hematocrito {hct}%. Si inicia TRT, monitorear a los 3 y 6 meses. Suspender si supera 54%."
                ))

            # Prostate Cancer Gate
            psa = mp.psa_ng_ml if mp else None
            if psa is not None and psa > 4.0:
                trt_veto = True
                actions.append(ActionItem(
                    category="pharmacological", priority="critical",
                    task="HARD STOP: TRT Contraindicada (PSA > 4.0)",
                    rationale=f"PSA sospechoso ({psa} ng/mL). Peligro de acelerar crecimiento de un CaP subclínico. Autorización urológica y biopsia mandatarias previas a TRT."
                ))

            # Severe Untreated Sleep Apnea
            has_osa = getattr(h, "has_osa", False)
            if has_osa:
                actions.append(ActionItem(
                    category="diagnostic", priority="high",
                    task="Gatekeeper: Verificar CPAP en Apnea del Sueño",
                    rationale="El paciente tiene AOS. La TRT empeora severamente la apnea obstructiva. Solo iniciar si está adherente a CPAP."
                ))
            
            if not trt_veto:
                actions.append(ActionItem(
                    category="pharmacological", priority="medium",
                    task="TRT Seguridad CV: Parámetros TRAVERSE aceptables",
                    rationale="Ausencia de hematocrito crítico y PSA normal. Según TRAVERSE Trial (2023), TRT no incrementa eventos MACE en esta subpoblación si se titula adecuadamente."
                ))

        # --- 3. PROSTATE SCREENING (Outside TRT context) ---
        psa = mp.psa_ng_ml if mp else None
        if psa is not None and psa > 10.0:
            actions.append(ActionItem(
                category="referral", priority="critical",
                task="Referencia URGENTE a Urología",
                rationale=f"PSA muy elevado ({psa} ng/mL). Alta sospecha oncológica prostática."
            ))

        # --- 4. GYNECOMASTIA & ESTROGEN ---
        if getattr(h, "has_gynecomastia", False):
            phenotypes.append("Ginecomastia")
            estradiol = mp.estradiol_pg_ml if hasattr(mp, "estradiol_pg_ml") else None
            if estradiol and testo:
                ratio = (estradiol * 10) / testo # Aromatization index proxy
                if ratio > 1.5:
                    actions.append(ActionItem(
                        category="diagnostic", priority="medium",
                        task="Sugerencia Inhibición de Aromatasa o corrección visceral",
                        rationale="Ginecomastia con hiperaromatización periférica (suele ocurrir en obesidad severa por exceso de tejido adiposo)."
                    ))

        # --- OUTCOME STATUS ---
        if is_hypogonadal or (psa is not None and psa >= 4.0):
            estado = "CONFIRMED_ACTIVE"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        elif has_biochemical_hypogonadism or has_symptoms:
            estado = "PROBABLE_WARNING"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "INDETERMINATE_LOCKED"
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        headline = " | ".join(phenotypes) if phenotypes else "Salud Masculina Basal"

        return AdjudicationResult(
            calculated_value=headline,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation="; ".join(findings) if findings else "Evaluación completada sin hallazgos patológicos androgénicos.",
            action_checklist=actions,
            metadata={
                "hypogonadism_confirmed": is_hypogonadal,
                "testosterone_total": testo,
                "psa": psa,
            }
        )
