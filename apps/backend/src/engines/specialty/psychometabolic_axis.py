"""
PsychometabolicAxisMotor — Gut-Brain Axis / Neuroinflammatory Phenotyping

This engine synthesizes psychometric questionnaires (PHQ-9, GAD-7, TFEQ-R18),
inflammatory biomarkers (hs-CRP), and nutritional cofactors (iron, vitamin D)
to produce an integrated psychometabolic phenotype and actionable clinical
recommendations.

Clinical Basis:
  1. Dantzer R et al., 2008. Nat Rev Neurosci — Cytokine-induced sickness behavior
     (IL-6, TNF-α → IDO activation → tryptophan shunting → ↓serotonin / ↑kynurenine)
  2. Raison CL et al., 2013. JAMA Psychiatry — Inflammatory Depression responds
     poorly to SSRIs; anti-inflammatory adjuncts improve outcomes.
  3. Felger JC & Lotrich FE, 2013. Neuropsychopharmacology — CRP > 3 mg/L predicts
     SSRI non-response; dopaminergic/glutamatergic pathways more affected.
  4. Luppino FS et al., 2010. Arch Gen Psychiatry — Bidirectional association between
     depression and obesity (OR 1.55 for obesity → depression; OR 1.58 reciprocal).
  5. Sharma AM & Padwal RS. Lancet 2009 — EOSS framework: Stage 3 if severe
     psychological comorbidity present.
  6. Acosta RD et al., 2021. Gastroenterology — Emotional Eating phenotype requires
     concurrent behavioral intervention for pharmacological success.
  7. Stahl SM. Essential Psychopharmacology. 5th Ed. — Bupropion mechanism:
     NE/DA reuptake inhibition; weight-neutral antidepressant.
  8. FDA Black Box Warning — Bupropion: suicidal ideation risk in <25yo,
     contraindicated with seizure history.
  9. Patrick RP & Ames BN, 2015. FASEB J — Vitamin D modulates serotonin synthesis
     via TPH2 activation in the brain (VDR-mediated).
  10. Beard JL et al., 2005. J Nutr — Iron is obligate cofactor for tryptophan
      hydroxylase (TPH); iron deficiency → impaired serotonin synthesis.

Safety Classification: IEC 62304 Class B — Decision Support (Clinician in Loop)
"""

from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter, AdjudicationResult, ClinicalEvidence,
    ActionItem, MedicationGap,
)
from typing import Tuple, List, Optional

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class PsychometabolicAxisMotor(BaseClinicalMotor):
    """
    Integrates the Gut-Brain Axis into clinical decision-making.
    Phenotypes: Inflammatory Depression, Hedonic Deficit, Anxiety-Driven
    Hyperphagia, Metabolic Encephalopathy.
    """
    REQUIREMENT_ID = "PSYCHOMETABOLIC-AXIS-2026"

    # --- LOINC / Internal Observation Codes ---
    CODES = {
        "PHQ9":           "PHQ9-SCORE",
        "PHQ9_ITEM9":     "PHQ9-I9-001",
        "GAD7":           "GAD-7",
        "TFEQ_EMOTIONAL": "TFEQ-EMOTIONAL",
        "TFEQ_UNCONTROLLED": "TFEQ-UNCONTROLLED",
        "TFEQ_COGNITIVE": "TFEQ-COGNITIVE",
        "HS_CRP":         "30522-7",      # LOINC hs-CRP (mg/L)
        "FERRITIN":       "FERRITIN-001",
        "VITD":           "VITD-001",
        "ATENAS":         "ATENAS-001",
        "FNQ_INTRUSIVE":  "FNQ-INTRUSIVE",
        "FNQ_CONTROL":    "FNQ-CONTROL",
    }

    # --- PHQ-9 Severity Thresholds (Kroenke 2001) ---
    PHQ9_MINIMAL   = 4
    PHQ9_MILD      = 9
    PHQ9_MODERATE  = 14
    PHQ9_MOD_SEV   = 19
    PHQ9_SEVERE    = 20  # 20-27

    # --- GAD-7 Severity Thresholds (Spitzer 2006) ---
    GAD7_MINIMAL  = 4
    GAD7_MILD     = 9
    GAD7_MODERATE = 14
    GAD7_SEVERE   = 15  # 15-21

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        """Requires at least PHQ-9 OR GAD-7 for psychometric phenotyping."""
        phq9 = encounter.get_observation(self.CODES["PHQ9"])
        gad7 = encounter.get_observation(self.CODES["GAD7"])
        if not phq9 and not gad7:
            return False, "No se proporcionaron cuestionarios PHQ-9 ni GAD-7. Motor psicometabólico requiere al menos uno."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence: List[ClinicalEvidence] = []
        actions: List[ActionItem] = []
        critical_omissions: List[MedicationGap] = []
        phenotypes_detected: List[str] = []
        safety_flags: List[str] = []

        # ── 0. DATA EXTRACTION ──────────────────────────────────────────
        phq9_obs = encounter.get_observation(self.CODES["PHQ9"])
        phq9_i9  = encounter.get_observation(self.CODES["PHQ9_ITEM9"])
        gad7_obs = encounter.get_observation(self.CODES["GAD7"])
        tfeq_emo = encounter.get_observation(self.CODES["TFEQ_EMOTIONAL"])
        tfeq_unc = encounter.get_observation(self.CODES["TFEQ_UNCONTROLLED"])
        tfeq_cog = encounter.get_observation(self.CODES["TFEQ_COGNITIVE"])
        crp_obs  = encounter.get_observation(self.CODES["HS_CRP"])
        ferritin_obs = encounter.get_observation(self.CODES["FERRITIN"])
        vitd_obs = encounter.get_observation(self.CODES["VITD"])
        atenas_obs = encounter.get_observation(self.CODES["ATENAS"])
        fnq_intr = encounter.get_observation(self.CODES["FNQ_INTRUSIVE"])
        fnq_ctrl = encounter.get_observation(self.CODES["FNQ_CONTROL"])

        phq9  = int(phq9_obs.value) if phq9_obs else None
        item9 = int(phq9_i9.value)  if phq9_i9  else None
        gad7  = int(gad7_obs.value) if gad7_obs  else None
        crp   = float(crp_obs.value) if crp_obs  else None
        ferritin = float(ferritin_obs.value) if ferritin_obs else None
        vitd  = float(vitd_obs.value) if vitd_obs else None
        atenas = int(atenas_obs.value) if atenas_obs else None

        # ── 1. SAFETY GATE: SUICIDAL IDEATION (PHQ-9 Item 9) ────────────
        #    FDA Black Box, APA Practice Guidelines 2023
        if item9 is not None and item9 >= 1:
            severity = "moderate" if item9 == 1 else "critical"
            if item9 >= 2:
                safety_flags.append("RIESGO SUICIDA ACTIVO")
                critical_omissions.append(MedicationGap(
                    drug_class="Bupropión / Naltrexona-Bupropión",
                    gap_type="CONTRAINDICATED",
                    severity="critical",
                    clinical_rationale=(
                        f"PHQ-9 Ítem 9 = {item9} (Ideación suicida: "
                        f"{'Varios días' if item9 == 1 else 'Más de la mitad de los días' if item9 == 2 else 'Casi todos los días'}). "
                        "FDA Black Box Bupropión: riesgo incrementado de ideación suicida. "
                        "Acción obligatoria: Derivación psiquiátrica urgente ANTES de cualquier decisión farmacológica para peso."
                    ),
                ))
                actions.append(ActionItem(
                    category="referral", priority="critical",
                    task="DERIVACIÓN PSIQUIÁTRICA URGENTE",
                    rationale=f"PHQ-9 Ítem 9 = {item9}. Riesgo suicida activo. La seguridad del paciente precede a cualquier objetivo de manejo del peso.",
                ))
            else:
                safety_flags.append("IDEACIÓN PASIVA DETECTADA")
                actions.append(ActionItem(
                    category="referral", priority="high",
                    task="Evaluación psiquiátrica recomendada",
                    rationale=f"PHQ-9 Ítem 9 = {item9} (pensamiento pasivo de muerte). Requiere exploración clínica antes de iniciar psicofármacos.",
                ))
            evidence.append(ClinicalEvidence(
                type="Safety", code="PHQ9-I9", value=item9,
                display=f"Riesgo Suicida: Ítem 9 = {item9}",
            ))

        # ── 2. DEPRESSION SEVERITY & PHENOTYPING ────────────────────────
        depression_severity = "none"
        if phq9 is not None:
            if phq9 >= self.PHQ9_SEVERE:
                depression_severity = "severe"
            elif phq9 >= self.PHQ9_MOD_SEV:
                depression_severity = "moderately_severe"
            elif phq9 > self.PHQ9_MODERATE:
                depression_severity = "moderate"
            elif phq9 > self.PHQ9_MILD:
                depression_severity = "mild"
            else:
                depression_severity = "minimal"

            evidence.append(ClinicalEvidence(
                type="Psychometric", code="PHQ-9", value=phq9,
                display=f"Depresión: {depression_severity.replace('_', ' ').title()} (PHQ-9 = {phq9})",
            ))

        # ── 2a. INFLAMMATORY DEPRESSION PHENOTYPE ───────────────────────
        #    Raison 2013, Felger 2013: CRP > 3 + PHQ9 >= 10
        #    → Kynurenine pathway activated, tryptophan shunted
        #    → SSRIs less effective; consider anti-inflammatory adjuncts
        if phq9 is not None and phq9 >= 10 and crp is not None and crp > 3.0:
            phenotypes_detected.append("Depresión Inflamatoria")
            evidence.append(ClinicalEvidence(
                type="Neuroinflammatory", code="INFLAM-DEPRESS",
                value=f"PHQ-9={phq9}, hs-CRP={crp}",
                display="Fenotipo: Depresión Inflamatoria (IDO/Quinurenina)",
            ))
            actions.append(ActionItem(
                category="pharmacological", priority="high",
                task="Fenotipo Depresión Inflamatoria: ISRS probablemente subóptimos",
                rationale=(
                    f"PHQ-9 ({phq9}) + hs-CRP ({crp} mg/L) indica activación de la vía IDO → "
                    "desvío de triptófano hacia quinureninas neurotóxicas. "
                    "La respuesta a ISRS clásicos es pobre (Raison 2013). "
                    "Considerar: 1) Bupropión (si no hay contraindicación suicida), "
                    "2) Omega-3 EPA ≥1g/día, "
                    "3) Ejercicio aeróbico (efecto antiinflamatorio directo), "
                    "4) Evaluar causa inflamatoria subyacente (obesidad visceral, periodontitis, NASH)."
                ),
            ))

        # ── 2b. SEROTONIN PRECURSOR DEFICIT ─────────────────────────────
        #    Iron (TPH cofactor) + Vitamin D (VDR-TPH2 axis)
        serotonin_risk_factors = []

        if ferritin is not None and ferritin < 30:
            serotonin_risk_factors.append(f"Ferritina Baja ({ferritin} ng/mL)")
            evidence.append(ClinicalEvidence(
                type="Nutritional", code="FERRITIN-LOW",
                value=ferritin, display=f"Ferritina {ferritin} ng/mL (cofactor TPH)",
            ))
        if vitd is not None and vitd < 20:
            serotonin_risk_factors.append(f"Déficit Vitamina D ({vitd} ng/mL)")
            evidence.append(ClinicalEvidence(
                type="Nutritional", code="VITD-LOW",
                value=vitd, display=f"Vitamina D {vitd} ng/mL (activador TPH2)",
            ))

        if serotonin_risk_factors and phq9 is not None and phq9 >= 5:
            phenotypes_detected.append("Déficit de Precursores Serotoninérgicos")
            actions.append(ActionItem(
                category="pharmacological", priority="high",
                task="Corregir déficit de cofactores serotoninérgicos ANTES de iniciar ISRS",
                rationale=(
                    f"Factores detectados: {', '.join(serotonin_risk_factors)}. "
                    "El hierro es cofactor obligado de la triptófano hidroxilasa (Beard 2005); "
                    "la vitamina D activa TPH2 cerebral vía VDR (Patrick & Ames 2015). "
                    "Si el paciente tiene déficit de estos sustratos, prescribir un ISRS es "
                    "como exigir producción sin materia prima. Corregir primero."
                ),
            ))

        # ── 3. ANXIETY & HPA AXIS DYSREGULATION ────────────────────────
        anxiety_severity = "none"
        if gad7 is not None:
            if gad7 >= self.GAD7_SEVERE:
                anxiety_severity = "severe"
            elif gad7 > self.GAD7_MODERATE:
                anxiety_severity = "moderate"
            elif gad7 > self.GAD7_MILD:
                anxiety_severity = "mild"
            else:
                anxiety_severity = "minimal"

            evidence.append(ClinicalEvidence(
                type="Psychometric", code="GAD-7", value=gad7,
                display=f"Ansiedad: {anxiety_severity.replace('_', ' ').title()} (GAD-7 = {gad7})",
            ))

        # ── 3a. ANXIETY-DRIVEN HYPERPHAGIA ──────────────────────────────
        #    Cortisol → visceral fat deposition → insulin resistance loop
        has_anxiety_eating = False
        if gad7 is not None and gad7 >= 10:
            if tfeq_unc and float(tfeq_unc.value) >= 2.5:
                has_anxiety_eating = True
                phenotypes_detected.append("Hiperfagia Ansiogénica")
                evidence.append(ClinicalEvidence(
                    type="Behavioral", code="ANXIETY-HYPERPHAGIA",
                    value=f"GAD-7={gad7}, TFEQ-UNC={tfeq_unc.value}",
                    display="Fenotipo: Hiperfagia mediada por Ansiedad (Eje HPA)",
                ))
                actions.append(ActionItem(
                    category="pharmacological", priority="high",
                    task="Hiperfagia Ansiogénica: Tratar ansiedad antes de abordar peso",
                    rationale=(
                        f"GAD-7 ({gad7}) + TFEQ Descontrol ({tfeq_unc.value}): "
                        "La hiperfagia es un síntoma del eje HPA hiperactivo, no un "
                        "problema primario de apetito. Cortisol crónico → grasa visceral → "
                        "resistencia a insulina. Priorizar manejo ansiolítico (TCC, "
                        "ISRS si PHQ-9 también elevado, o Pregabalina si ansiedad pura). "
                        "GLP-1 como coadyuvante, no como primera línea."
                    ),
                ))

        # ── 4. HEDONIC DEFICIT / REWARD DYSREGULATION ───────────────────
        #    TFEQ-Emotional + Depression = Dopaminergic pathway dysfunction
        if tfeq_emo and float(tfeq_emo.value) >= 2.5:
            if phq9 is not None and phq9 >= 10:
                phenotypes_detected.append("Déficit Hedónico / Disregulación de Recompensa")
                evidence.append(ClinicalEvidence(
                    type="Behavioral", code="HEDONIC-DEFICIT",
                    value=f"TFEQ-EMO={tfeq_emo.value}, PHQ-9={phq9}",
                    display="Fenotipo: Comida como Automedicación (Vía Dopaminérgica)",
                ))
                # Naltrexone/Bupropion is the pharmacological sweet spot here,
                # BUT only if suicidal ideation is absent
                if item9 is None or item9 == 0:
                    actions.append(ActionItem(
                        category="pharmacological", priority="high",
                        task="Candidato a Naltrexona/Bupropión (Contrave o Formulación Magistral)",
                        rationale=(
                            f"Depresión (PHQ-9={phq9}) + Comida Emocional (TFEQ-E={tfeq_emo.value}): "
                            "Patrón de automedicación con alimentos (vía dopamina/opioides). "
                            "Naltrexona (bloqueo μ-opioide) + Bupropión (↑NE/DA) actúa directamente "
                            "sobre el circuito de recompensa y tiene efecto antidepresivo simultáneo. "
                            "Dos pájaros de un tiro (Stahl, Essential Psychopharmacology)."
                        ),
                    ))
                else:
                    actions.append(ActionItem(
                        category="referral", priority="critical",
                        task="Naltrexona/Bupropión CONTRAINDICADO — Derivar a Psiquiatría",
                        rationale=(
                            f"Fenotipo hedónico ideal para Contrave, PERO PHQ-9 Ítem 9 = {item9}. "
                            "FDA Black Box: Bupropión incrementa riesgo suicida. "
                            "Secure mental health FIRST, luego reevaluar."
                        ),
                    ))
            elif phq9 is None or phq9 < 10:
                # Emotional eating without clinical depression
                phenotypes_detected.append("Comida Emocional sin Depresión Clínica")
                actions.append(ActionItem(
                    category="lifestyle", priority="high",
                    task="Intervención Conductual Estructurada (TCC / Mindful Eating)",
                    rationale=(
                        f"TFEQ-Emotional elevado ({tfeq_emo.value}) sin depresión clínica (PHQ-9={phq9 or 'N/A'}). "
                        "El patrón es conductual puro, no neuropsiquiátrico. "
                        "La intervención óptima es TCC enfocada en alimentación + Mindful Eating. "
                        "Los fármacos deben ser segunda línea."
                    ),
                ))

        # ── 5. FOOD NOISE / OBSESSIVE EATING ────────────────────────────
        #    FNQ (Food Noise Questionnaire) — Emerging construct
        if fnq_intr and fnq_ctrl:
            fnq_total = int(fnq_intr.value) + int(fnq_ctrl.value)
            if fnq_total >= 6:  # Significant food noise
                phenotypes_detected.append("Ruido Alimentario Obsesivo (Food Noise)")
                evidence.append(ClinicalEvidence(
                    type="Behavioral", code="FOOD-NOISE",
                    value=fnq_total,
                    display=f"Food Noise Score = {fnq_total} (Pensamientos intrusivos + Dificultad de control)",
                ))
                actions.append(ActionItem(
                    category="pharmacological", priority="medium",
                    task="GLP-1 agonistas silencian Food Noise (hallazgo SURMOUNT/STEP)",
                    rationale=(
                        f"Food Noise elevado (FNQ = {fnq_total}). "
                        "Los agonistas GLP-1/GIP han demostrado reducción significativa "
                        "del 'ruido alimentario' en estudios SURMOUNT y STEP, "
                        "probablemente vía receptores GLP-1 en hipotálamo y sistema límbico."
                    ),
                ))

        # ── 6. INSOMNIA-METABOLISM-MOOD TRIAD ───────────────────────────
        #    Athens Insomnia Scale + PHQ-9 + metabolic markers
        if atenas is not None and atenas >= 6:
            if phq9 is not None and phq9 >= 10:
                phenotypes_detected.append("Tríada Insomnio-Depresión-Metabolismo")
                evidence.append(ClinicalEvidence(
                    type="Sleep", code="INSOMNIA-TRIAD",
                    value=f"AIS={atenas}, PHQ-9={phq9}",
                    display="Insomnio + Depresión: Disrupción circadiana del apetito",
                ))
                actions.append(ActionItem(
                    category="lifestyle", priority="high",
                    task="Priorizar Higiene del Sueño + Restricción calórica nocturna",
                    rationale=(
                        f"AIS ({atenas}) + PHQ-9 ({phq9}): la disrupción circadiana "
                        "incrementa ghrelina nocturna, reduce leptina y activa la ingesta "
                        "hedónica posprandial tardía. Tratar el insomnio tiene impacto "
                        "directo en cortisol/HPA, apetito y ánimo."
                    ),
                ))

        # ── 7. IATROGENIC WEIGHT GAIN SCREEN ────────────────────────────
        #    Detect medications known to cause significant weight gain
        weight_gaining_drugs = []
        if hasattr(encounter, "medications") and encounter.medications:
            IATROGENS = {
                "PAROXETINE":  "Paroxetina (ISRS — máximo potencial de ganancia de peso)",
                "MIRTAZAPINE": "Mirtazapina (NaSSA — antagonista H1 → ↑apetito)",
                "OLANZAPINE":  "Olanzapina (Antipsicótico — ganancia > 7kg a 6 meses)",
                "QUETIAPINE":  "Quetiapina (Antipsicótico atípico — ganancia moderada)",
                "AMITRIPTYLINE":"Amitriptilina (Tricíclico — ganancia moderada-severa)",
                "PREGABALIN":  "Pregabalina (edema + ↑apetito en 15-20% de pacientes)",
                "VALPROATE":   "Ácido Valproico (ganancia severa + resistencia a insulina)",
                "INSULIN":     "Insulina (ganancia de peso dosis-dependiente)",
            }
            for med in encounter.medications:
                if med.is_active:
                    code_upper = (med.code or "").upper()
                    name_upper = (med.name or "").upper()
                    for drug_key, drug_desc in IATROGENS.items():
                        if drug_key in code_upper or drug_key in name_upper:
                            weight_gaining_drugs.append(drug_desc)

        if weight_gaining_drugs:
            phenotypes_detected.append("Ganancia Iatrogénica de Peso")
            evidence.append(ClinicalEvidence(
                type="Medication", code="IATROGENIC-GAIN",
                value=len(weight_gaining_drugs),
                display=f"{len(weight_gaining_drugs)} fármaco(s) obesogénico(s) activo(s)",
            ))
            actions.append(ActionItem(
                category="pharmacological", priority="high",
                task=f"Auditoría de fármacos obesogénicos: {', '.join(weight_gaining_drugs)}",
                rationale=(
                    "Se detectaron medicamentos psiquiátricos con efecto significativo "
                    "sobre el peso. Antes de intensificar tratamiento anti-obesidad, "
                    "evaluar con Psiquiatría la posibilidad de rotar a alternativas "
                    "weight-neutral: Bupropión (ISRS→), Aripiprazol (antipsicótico→), "
                    "Topiramato (anticonvulsivante→)."
                ),
            ))

        # ── 8. COGNITIVE RESTRAINT PARADOX ──────────────────────────────
        #    High cognitive restraint + depression = restrictive-binge cycle
        if tfeq_cog and float(tfeq_cog.value) >= 3.0:
            if phq9 is not None and phq9 >= 10:
                phenotypes_detected.append("Paradoja de Restricción Cognitiva")
                evidence.append(ClinicalEvidence(
                    type="Behavioral", code="RESTRAINT-PARADOX",
                    value=f"TFEQ-COG={tfeq_cog.value}, PHQ-9={phq9}",
                    display="Restricción Cognitiva Alta + Depresión = Ciclo Restricción-Atracón",
                ))
                actions.append(ActionItem(
                    category="lifestyle", priority="high",
                    task="ALERTA: Riesgo de ciclo Restricción-Atracón",
                    rationale=(
                        f"Restricción Cognitiva alta (TFEQ-C={tfeq_cog.value}) + Depresión (PHQ-9={phq9}): "
                        "combinación de alto riesgo para Binge Eating Disorder (BED). "
                        "NO indicar dietas muy restrictivas. Preferir plan flexible "
                        "(enfoque 80/20) y derivar a evaluación por TCA (Trastorno de Conducta Alimentaria)."
                    ),
                ))

        # ── 9. SYNTHESIS ────────────────────────────────────────────────
        if not phenotypes_detected:
            phenotypes_detected.append("Sin fenotipo psicometabólico significativo")

        headline = " | ".join(phenotypes_detected)

        # Determine UI status
        if safety_flags:
            status = "PROBABLE_WARNING"
        elif any(p in phenotypes_detected for p in [
            "Depresión Inflamatoria",
            "Déficit Hedónico / Disregulación de Recompensa",
            "Hiperfagia Ansiogénica",
        ]):
            status = "CONFIRMED_ACTIVE"
        elif phenotypes_detected == ["Sin fenotipo psicometabólico significativo"]:
            status = "RULED_OUT"
        else:
            status = "CONFIRMED_ACTIVE"

        # Build explanation
        explanation_parts = []
        if phq9 is not None:
            explanation_parts.append(f"Depresión: {depression_severity} (PHQ-9={phq9})")
        if gad7 is not None:
            explanation_parts.append(f"Ansiedad: {anxiety_severity} (GAD-7={gad7})")
        if crp is not None:
            crp_cat = "bajo" if crp < 1.0 else ("intermedio" if crp <= 3.0 else "alto (neuroinflamatorio)")
            explanation_parts.append(f"hs-CRP: {crp} mg/L ({crp_cat})")
        if safety_flags:
            explanation_parts.append(f"⚠️ SEGURIDAD: {', '.join(safety_flags)}")

        explanation = "Eje Psicometabólico: " + "; ".join(explanation_parts) if explanation_parts else "Evaluación psicometabólica sin hallazgos."

        return AdjudicationResult(
            calculated_value=headline,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.INDIRECT_EVIDENCE],
            evidence=evidence,
            estado_ui=status,
            requirement_id=self.REQUIREMENT_ID,
            action_checklist=actions,
            critical_omissions=critical_omissions,
            explanation=explanation,
            metadata={
                "phenotypes": phenotypes_detected,
                "depression_severity": depression_severity if phq9 else "not_assessed",
                "anxiety_severity": anxiety_severity if gad7 else "not_assessed",
                "safety_flags": safety_flags,
                "serotonin_precursor_deficit": bool(serotonin_risk_factors),
                "iatrogenic_drugs": weight_gaining_drugs,
            },
        )
