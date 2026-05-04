"""
WomensHealthMotor — Precision Female Endocrinology

Evaluates:
1. PCOS Phenotyping (Metabolic vs Adrenal)
2. Safe HRT (Hormone Replacement Therapy) prescribing (Safety Gates) 
3. Premature Menopause (POI) cardiovascular risk enhancer
4. Pregnancy teratogen screening
5. Obstetric History (Preeclampsia, GDM)
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


class WomensHealthMotor(BaseClinicalMotor):
    REQUIREMENT_ID = "WOMENS-HEALTH-V2"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        is_female = encounter.metadata.get("sex", "").lower() in ["female", "f"]
        if not is_female:
            return False, "WomensHealthMotor applies to female patients only."
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
                explanation="Requiere historial clínico e interrogatorio endocrino.",
            )

        findings = []
        actions = []
        evidence = []
        sop_criteria = 0
        phenotypes = []

        # --- 1. PCOS ASSESSMENT & PHENOTYPING ---
        has_hyperandrogenism = False
        mp = encounter.metabolic_panel

        # FAI (Free Androgen Index)
        testo = mp.testosterone_total_ng_dl if mp else None
        shbg = mp.shbg_nmol_l if mp else None
        if testo and shbg and shbg > 0:
            fai = (testo / shbg) * 100
            if fai > 5.0:
                has_hyperandrogenism = True
                findings.append(f"Hiperandrogenismo (FAI: {fai:.1f})")

        # Clinical Hyperandrogenism (Ferriman-Gallwey)
        fg_score = h.ferriman_gallwey_score if hasattr(h, "ferriman_gallwey_score") else None
        if fg_score is not None and fg_score >= 8:
            has_hyperandrogenism = True
            findings.append(f"Hiperandrogenismo clínico (Ferriman: {fg_score})")

        if has_hyperandrogenism:
            sop_criteria += 1

        cycle_irregular = hasattr(h, "cycle_regularity") and h.cycle_regularity in ["irregular", "amenorrhea"]
        if cycle_irregular:
            sop_criteria += 1
            findings.append("Oligo/anovulación")

        amh = mp.amh_ng_ml if mp else None
        if amh is not None and amh > 4.5:
            sop_criteria += 1
            findings.append(f"Morfología poliquística (AMH: {amh} ng/mL)")

        sop_confirmed = sop_criteria >= 2
        if sop_confirmed:
            phenotypes.append("SOP Confirmado")
            evidence.append(ClinicalEvidence(type="Diagnosis", code="PCOS", value=sop_criteria, display="Criterios Rotterdam ≥ 2"))
            
            # Phenotyping: Adrenal vs Metabolic
            dheas_obs = encounter.get_observation("DHEAS-001")
            insulin = mp.insulin_mu_u_ml if mp else None
            glucose = mp.glucose_mg_dl if mp else None
            
            is_metabolic = False
            if insulin and glucose:
                homa_ir = (insulin * glucose) / 405
                if homa_ir > 2.5:
                    is_metabolic = True
                    phenotypes.append("SOP Fenotipo Metabólico")
                    actions.append(ActionItem(
                        category="pharmacological", priority="high",
                        task="SOP Metabólico: Priorizar sensibilizadores a la insulina",
                        rationale=f"SOP + HOMA-IR ({homa_ir:.1f}). Metformina o GLP-1 indicados para reanudar ovulación y proteger metabolismo."
                    ))

            dheas = safe_float(dheas_obs.value) if dheas_obs else None
            if dheas is not None and dheas > 275:
                phenotypes.append("SOP Fenotipo Adrenal")
                actions.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="SOP Adrenal: Considerar inhibición androgénica periférica",
                    rationale=f"Elevación de andrógenos suprarrenales (DHEAS: {dheas} ug/dL). Espironolactona es altamente efectiva para control del exceso androgénico (acné/hirsutismo), asumiendo paciente con anticoncepción asegurada."
                ))
            
            if not is_metabolic and (dheas is None or dheas <= 275):
                actions.append(ActionItem(
                    category="diagnostic", priority="medium",
                    task="Fenotipificar SOP",
                    rationale="Solicitar DHEAS e Insulina basal para diferenciar el driver fisiopatológico del SOP."
                ))


        # --- 2. HRT SAFETY GATE & MENOPAUSE ---
        menopause = h.menopausal_status if hasattr(h, "menopausal_status") else "pre"
        age = encounter.demographics.age_years
        
        has_history_vte = getattr(h, "has_history_dvt_pe", False) or bool(encounter.get_observation("Hx-VTE"))
        has_breast_ca = getattr(h, "has_history_breast_cancer", False) or bool(encounter.get_observation("Hx-BRCA"))
        has_ascvd = h.has_coronary_disease or h.has_stroke or h.has_heart_failure
        
        menopause_age_obs = encounter.get_observation("MENOPAUSE-AGE")
        menopause_age = safe_float(menopause_age_obs.value) if menopause_age_obs else None

        if menopause == "post":
            findings.append("Post-menopáusica")
            
            # Premature Ovarian Insufficiency
            if menopause_age and menopause_age < 40:
                phenotypes.append("Insuficiencia Ovárica Prematura (POI)")
                actions.append(ActionItem(
                    category="pharmacological", priority="critical",
                    task="HRT mandatoria hasta edad fisiológica de menopausia (51 años)",
                    rationale=f"Menopausia a los {menopause_age} años. Alta mortalidad cardiovascular y osteoporosis si no se restituyen estrógenos tempranamente."
                ))
                evidence.append(ClinicalEvidence(type="Risk", code="POI-CV-RISK", value="High", display="Riesgo CV acelerado por POI"))
            else:
                # Standard HRT Safety Gate (ACOG/NAMS Guidelines)
                years_since_menopause = (age - menopause_age) if menopause_age else (age - 51)
                
                if has_breast_ca:
                    actions.append(ActionItem(
                        category="pharmacological", priority="critical",
                        task="Terapia Hormonal (HRT) CONTRAINDICADA (Absoluta)",
                        rationale="Historia de Cáncer de Mama. Referir para manejo no hormonal de síntomas vasomotores (ej. Fezolinetant, ISRS)."
                    ))
                elif has_history_vte or has_ascvd:
                    actions.append(ActionItem(
                        category="pharmacological", priority="high",
                        task="HRT Oral CONTRAINDICADA. Considerar Transdérmica con precaución",
                        rationale="Historia de Trombosis o ASCVD. Los estrógenos orales tienen primer paso hepático incrementando factores procoagulantes. La vía transdérmica evita este riesgo, pero requiere aprobación cardiológica colegiada."
                    ))
                elif age >= 60 or years_since_menopause >= 10:
                    actions.append(ActionItem(
                        category="pharmacological", priority="high",
                        task="No iniciar HRT sistémica",
                        rationale=f"Edad {age} o tiempo desde menopausia >= 10 años. AHA/NAMS no recomiendan inicio de HRT por incremento de riesgo de placa vulnerable y trombosis."
                    ))
                else:
                    actions.append(ActionItem(
                        category="pharmacological", priority="medium",
                        task="Ventana Estrogénica Abierta — Candidata a HRT",
                        rationale="<60 años y <10 años desde menopausia sin contraindicaciones absolutas detectadas. HRT puede proveer alivio vasomotor y protección ósea/metabólica si la paciente es sintomática."
                    ))

        # --- 3. PREGNANCY & OBSTETRICS (Teratogen Guard) ---
        pregnancy = getattr(h, "pregnancy_status", "not_applicable")
        if pregnancy == "pregnant":
            phenotypes.append("Gestación Activa")
            actions.append(ActionItem(
                category="pharmacological", priority="critical",
                task="SUSPENDER TERATÓGENOS: Estatinas, IECA/ARA2, SGLT2i, GLP-1",
                rationale="Medicamentos de uso metabólico rutinario están contraindicados en embarazo (FDA Categoría X o sin data de seguridad)."
            ))

        if getattr(h, "has_history_preeclampsia", False):
            findings.append("Riesgo CV aumentado por Preeclampsia previa (x2)")
            evidence.append(ClinicalEvidence(type="Risk", code="PREECLAMPSIA", value="+", display="Riesgo CV x2"))
        
        if getattr(h, "has_history_gestational_diabetes", False):
            findings.append("Riesgo DM2 aumentado por DMG previa (x7)")
            evidence.append(ClinicalEvidence(type="Risk", code="GDM", value="+", display="Riesgo futuro DM2 x7"))

        # --- OUTCOME STATUS ---
        status = "CONFIRMED_ACTIVE" if sop_confirmed or pregnancy == "pregnant" or menopause == "post" else "INDETERMINATE_LOCKED"
        headline = " | ".join(phenotypes) if phenotypes else "Salud femenina basal"

        return AdjudicationResult(
            calculated_value=headline,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE] if sop_confirmed else 0.80,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=status,
            explanation="; ".join(findings) if findings else "Evaluación femenina completada sin hallazgos patológicos.",
            action_checklist=actions,
            metadata={
                "sop_confirmed": sop_confirmed,
                "pregnancy_status": pregnancy,
            }
        )
