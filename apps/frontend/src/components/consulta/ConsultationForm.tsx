"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import {
  Activity, Brain, Loader2, Send,
} from "lucide-react"

// Extracted sub-components
import Step0HistoriaBiometria from "./step0-historia-biometria"
import Step1Laboratorios from "./step1-laboratorios"
import Step2PsicometriaCierre from "./step2-psicometria-cierre"
import WomensHealthPanel from "./womens-health-panel"
import MensHealthPanel from "./mens-health-panel"
import {
  ConsultationFormState, BaselineEncounter, validateCoherence
} from "./consultation-form-types"
import { EncounterResult } from "@/types"

interface ConsultationFormProps {
  patientId: string
  patient?: { gender: string | null } | null
  baseline?: BaselineEncounter | null
  onSubmit: (results: EncounterResult) => void
}

const INITIAL_FORM: ConsultationFormState = {
  consent_accepted: false,
  reason_for_visit: "",
  onset_trigger: "", age_of_onset: "", max_weight_ever_kg: "",
  has_type2_diabetes: false, has_prediabetes: false, has_hypertension: false,
  has_dyslipidemia: false, has_nafld: false, has_gout: false,
  has_hypothyroidism: false, has_pcos: false, has_osa: false,
  has_gerd: false, has_ckd: false, has_heart_failure: false,
  has_coronary_disease: false, has_stroke: false, has_retinopathy: false,
  has_neuropathy: false, has_bariatric_surgery: false,
  bariatric_surgery_type: "", bariatric_surgery_date: "",
  other_surgeries: "", allergies: "",
  smoking_status: "never", alcohol_intake: "none",
  has_glaucoma: false, has_seizures_history: false,
  has_eating_disorder_history: false, family_history_thyroid_cancer: false,
  has_statin_myalgia: false, caffeine_anxiety_insomnia: false, taking_otc_vitd: false, taking_ppi_chronically: false,
  has_active_substance_abuse: false, ace_score: "",
  weight_kg: "", height_cm: "", waist_cm: "", hip_cm: "",
  systolic_bp: "", diastolic_bp: "",
  body_fat_percent: "", fat_mass_kg: "",   lean_mass_kg: "", lbm_boer_kg: "",
  muscle_mass_kg: "", skeletal_muscle_index: "",
  visceral_fat_area_cm2: "", visceral_fat_level: "",
  basal_metabolic_rate: "", total_body_water_percent: "",
  bone_mass_kg: "",
  arm_circumference_cm: "", calf_circumference_cm: "",
  glucose_mg_dl: "", hba1c_percent: "", insulin_mu_u_ml: "", c_peptide_ng_ml: "",
  creatinine_mg_dl: "", uric_acid_mg_dl: "",
  ast_u_l: "", alt_u_l: "", ggt_u_l: "", alkaline_phosphatase_u_l: "",
  wbc_k_ul: "", lymphocyte_percent: "", neutrophil_percent: "",
  mcv_fl: "", rdw_percent: "", platelets_k_u_l: "",
  hs_crp_mg_l: "", ferritin_ng_ml: "", albumin_g_dl: "",
  tsh_uIU_ml: "", ft4_ng_dl: "", ft3_pg_ml: "",
  rt3_ng_dl: "", shbg_nmol_l: "", cortisol_am_mcg_dl: "",
  aldosterone_ng_dl: "", renin_ng_ml_h: "",
  gada_antibodies: false,
  total_cholesterol_mg_dl: "", ldl_mg_dl: "", hdl_mg_dl: "",
  triglycerides_mg_dl: "", vldl_mg_dl: "",
  apob_mg_dl: "", lpa_mg_dl: "", apoa1_mg_dl: "",
  phq9_score: "", gad7_score: "",
  tfeq_uncontrolled: "", tfeq_cognitive: "", tfeq_emotional: "",
  atenas_score: "", fnq_intrusive: "", fnq_control: "",
  sleep_hours: "", stress_level: "", physical_activity_min_week: "",
  first_meal_time: "", last_meal_time: "",
  snores_loudly: false, daytime_tiredness: false, observed_apnea: false,
  conditions_text: "", medications_text: "",
  personal_history: "", family_history: "",
  pregnancy_status: "unknown", menopausal_status: "unknown",
  cycle_regularity: "unknown", last_menstrual_period: "",
  has_endometriosis: false, has_history_preeclampsia: false,
  has_history_gestational_diabetes: false, contraception_method: "",
  on_hrt: false, ferriman_gallwey_score: "",
  has_erectile_dysfunction: false, iief5_score: "",
  has_prostate_issues: false, has_male_pattern_baldness: false,
  has_gynecomastia: false,
  testosterone_total_ng_dl: "", amh_ng_ml: "",
  lh_u_l: "", fsh_u_l: "", estradiol_pg_ml: "",
  prolactin_ng_ml: "", dhea_s_mcg_dl: "", psa_ng_ml: "",
  vitamin_d_ng_ml: "", vitamin_b12_pg_ml: "",
  grip_right_kg: "", grip_left_kg: "",
  gait_speed_sec: "", five_x_sts_sec: "", sarcf_score: "",
  acosta_falla_saciedad: "", acosta_intestino_hambriento: "",
  acosta_hambre_emocional: "", acosta_metabolismo_lento: "",
  acosta_saciedad_temprana: "",
}

export default function ConsultationForm({ patientId, patient, baseline, onSubmit }: ConsultationFormProps) {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [processingStage, setProcessingStage] = useState<"idle" | "validating" | "engines" | "adjudicating">("idle")
  const [error, setError] = useState("")
  const [prefilling, setPrefilling] = useState(false)
  const [limits, setLimits] = useState<Record<string, [number, number]>>({})
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    historia: true,
    comorbididades: false,
    biometria: false,
    estilo_vida: false,
    ace: false,
    womens: false,
    mens: false,
  })

  // Fetch biological limits from backend (SSOT)
  useEffect(() => {
    const fetchLimits = async () => {
      try {
        const data = await api.get<Record<string, [number, number]>>("/metadata/limits")
        setLimits(data)
      } catch (err) {
        console.error("Failed to fetch biological limits", err)
      }
    }
    fetchLimits()
  }, [])

  const [form, setForm] = useState<ConsultationFormState>(INITIAL_FORM)

  const toggleSection = useCallback((key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const [aceAnswers, setAceAnswers] = useState<Record<number, boolean>>({})

  const handleAceAnswer = useCallback((idx: number, value: boolean) => {
    setAceAnswers((prev) => {
      const next = { ...prev, [idx]: value }
      const score = Object.values(next).filter(Boolean).length
      setForm((f) => ({ ...f, ace_score: String(score) }))
      return next
    })
  }, [])

  const aceScore = Object.values(aceAnswers).filter(Boolean).length

  useEffect(() => {
    if (!baseline) return
    setForm((f) => ({
      ...f,
      reason_for_visit: baseline.reason_for_visit
        ? `${baseline.reason_for_visit} (Control)`
        : "Consulta de control",
      personal_history: baseline.personal_history || f.personal_history,
      family_history: baseline.family_history || f.family_history,
      phq9_score: baseline.psychometrics?.phq9_score ? String(baseline.psychometrics.phq9_score) : "",
      gad7_score: baseline.psychometrics?.gad7_score ? String(baseline.psychometrics.gad7_score) : "",
      tfeq_uncontrolled: baseline.psychometrics?.tfeq_uncontrolled_eating ? String(baseline.psychometrics.tfeq_uncontrolled_eating) : "",
      tfeq_cognitive: baseline.psychometrics?.tfeq_cognitive_restraint ? String(baseline.psychometrics.tfeq_cognitive_restraint) : "",
      tfeq_emotional: baseline.psychometrics?.tfeq_emotional_eating ? String(baseline.psychometrics.tfeq_emotional_eating) : "",
      atenas_score: baseline.psychometrics?.atenas_insomnia_score ? String(baseline.psychometrics.atenas_insomnia_score) : "",
      fnq_intrusive: baseline.psychometrics?.fnq_intrusive_thoughts ? String(baseline.psychometrics.fnq_intrusive_thoughts) : "",
      fnq_control: baseline.psychometrics?.fnq_control_difficulty ? String(baseline.psychometrics.fnq_control_difficulty) : "",
    }))
  }, [baseline])

  const set = useCallback((field: string, value: string) => {
    const boolFields = ["consent_accepted", "gada_antibodies", "snores_loudly", "daytime_tiredness", "observed_apnea",
      "has_type2_diabetes", "has_prediabetes", "has_hypertension", "has_dyslipidemia", "has_nafld", "has_gout",
      "has_hypothyroidism", "has_pcos", "has_osa", "has_gerd", "has_ckd", "has_heart_failure",
      "has_coronary_disease", "has_stroke", "has_retinopathy", "has_neuropathy", "has_bariatric_surgery",
      "has_glaucoma", "has_seizures_history", "has_eating_disorder_history", "family_history_thyroid_cancer",
      "has_statin_myalgia", "caffeine_anxiety_insomnia", "taking_otc_vitd", "taking_ppi_chronically",
      "has_active_substance_abuse", "has_endometriosis", "has_history_preeclampsia", "has_history_gestational_diabetes",
      "on_hrt", "has_erectile_dysfunction", "has_prostate_issues", "has_male_pattern_baldness", "has_gynecomastia"]
    setForm((prev) => ({
      ...prev,
      [field]: boolFields.includes(field) ? (value === "true") : value,
    }))
  }, [])

  const toggle = useCallback((field: string) => {
    setForm((prev) => ({ ...prev, [field]: !(prev as unknown as Record<string, unknown>)[field] }))
  }, [])

  // Auto-calculate LBM Boer when weight, height, or gender changes
  useEffect(() => {
    const weight = parseFloat(form.weight_kg)
    const height = parseFloat(form.height_cm)
    const gender = patient?.gender?.toLowerCase()
    if (isNaN(weight) || isNaN(height) || !gender) {
      if (form.lbm_boer_kg) setForm((prev) => ({ ...prev, lbm_boer_kg: "" }))
      return
    }
    const lbm = gender === "male" || gender === "m"
      ? Math.round(((0.407 * weight) + (0.267 * height) - 19.2) * 10) / 10
      : Math.round(((0.252 * weight) + (0.473 * height) - 48.3) * 10) / 10
    if (lbm > 0 && form.lbm_boer_kg !== String(lbm)) {
      setForm((prev) => ({ ...prev, lbm_boer_kg: String(lbm) }))
    }
  }, [form.weight_kg, form.height_cm, patient?.gender])

  const num = (v: string) => (v ? parseFloat(v) : undefined)

  useEffect(() => {
    if (!patientId) return
    setPrefilling(true)
    api.get<Record<string, unknown>[]>(`/encounters/patient/${patientId}`)
      .then((data) => {
        const encounters = Array.isArray(data) ? data : []
        if (encounters.length === 0) { setPrefilling(false); return }
        const last = encounters[encounters.length - 1]
        if (last.reason_for_visit) {
          setForm((prev) => ({ ...prev, reason_for_visit: last.reason_for_visit as string }))
        }
        setPrefilling(false)
      })
      .catch(() => setPrefilling(false))
  }, [patientId])

  const buildPayload = () => {
    const conditions = form.conditions_text.split("\n").filter(Boolean).map((line) => {
      const parts = line.split("|")
      return { code: (parts[0] || "").trim(), title: (parts[1] || parts[0] || "").trim(), system: "CIE-10" }
    })
    const medications = form.medications_text.split("\n").filter(Boolean).map((line) => {
      const parts = line.split("|")
      return { name: (parts[0] || "").trim(), dose_amount: (parts[1] || "").trim() || undefined, frequency: (parts[2] || "").trim() || undefined }
    })

    return {
      patient_id: patientId,
      reason_for_visit: form.reason_for_visit || "Consulta de rutina",
      history: {
        onset_trigger: form.onset_trigger || undefined,
        age_of_onset: num(form.age_of_onset),
        max_weight_ever_kg: num(form.max_weight_ever_kg),
        has_type2_diabetes: form.has_type2_diabetes, has_prediabetes: form.has_prediabetes,
        has_hypertension: form.has_hypertension, has_dyslipidemia: form.has_dyslipidemia,
        has_nafld: form.has_nafld, has_gout: form.has_gout,
        has_hypothyroidism: form.has_hypothyroidism, has_pcos: form.has_pcos,
        has_osa: form.has_osa, has_gerd: form.has_gerd, has_ckd: form.has_ckd,
        has_heart_failure: form.has_heart_failure, has_coronary_disease: form.has_coronary_disease,
        has_stroke: form.has_stroke, has_retinopathy: form.has_retinopathy,
        has_neuropathy: form.has_neuropathy,
        has_bariatric_surgery: form.has_bariatric_surgery,
        bariatric_surgery_type: form.bariatric_surgery_type || undefined,
        bariatric_surgery_date: form.bariatric_surgery_date || undefined,
        other_surgeries: form.other_surgeries || undefined,
        allergies: form.allergies || undefined,
        smoking_status: form.smoking_status, alcohol_intake: form.alcohol_intake,
        has_glaucoma: form.has_glaucoma, has_seizures_history: form.has_seizures_history,
        has_eating_disorder_history: form.has_eating_disorder_history,
        family_history_thyroid_cancer: form.family_history_thyroid_cancer,
        has_statin_myalgia: form.has_statin_myalgia,
        caffeine_anxiety_insomnia: form.caffeine_anxiety_insomnia,
        taking_otc_vitd: form.taking_otc_vitd,
        taking_ppi_chronically: form.taking_ppi_chronically,
        has_active_substance_abuse: form.has_active_substance_abuse,
        trauma: form.ace_score ? { ace_score: num(form.ace_score) } : undefined,
      },
      observations: [
        { code: "29463-7", value: num(form.weight_kg), unit: "kg" },
        { code: "8302-2", value: num(form.height_cm), unit: "cm" },
        { code: "WAIST-001", value: num(form.waist_cm), unit: "cm" },
        { code: "HIP-001", value: num(form.hip_cm), unit: "cm" },
        { code: "8480-6", value: num(form.systolic_bp), unit: "mmHg" },
        { code: "8462-4", value: num(form.diastolic_bp), unit: "mmHg" },
        { code: "MMA-001", value: num(form.muscle_mass_kg), unit: "kg", category: "BIA" },
        { code: "BIA-FAT-PCT", value: num(form.body_fat_percent), unit: "%", category: "BIA" },
        { code: "BIA-LEAN-KG", value: num(form.lean_mass_kg), unit: "kg", category: "BIA" },
        { code: "BIA-VISCERAL", value: num(form.visceral_fat_area_cm2), unit: "cm2", category: "BIA" },
        { code: "BIA-BMR", value: num(form.basal_metabolic_rate), unit: "kcal", category: "BIA" },
        { code: "BIA-TBW", value: num(form.total_body_water_percent), unit: "%", category: "BIA" },
        { code: "BIA-BONE", value: num(form.bone_mass_kg), unit: "kg", category: "BIA" },
        { code: "ARM-CIRC", value: num(form.arm_circumference_cm), unit: "cm", category: "Anthropometry" },
        { code: "CALF-CIRC", value: num(form.calf_circumference_cm), unit: "cm", category: "Anthropometry" },
        { code: "GRIP-STR-R", value: num(form.grip_right_kg), unit: "kg" },
        { code: "GRIP-STR-L", value: num(form.grip_left_kg), unit: "kg" },
        { code: "GAIT-SPEED", value: num(form.gait_speed_sec), unit: "s" },
        { code: "5XSTS-SEC", value: num(form.five_x_sts_sec), unit: "s" },
        { code: "SARCF-SCORE", value: num(form.sarcf_score), category: "Sarcopenia" },
      ].filter((o) => (o as { value?: unknown }).value !== undefined),
      biometrics: {
        weight_kg: num(form.weight_kg), height_cm: num(form.height_cm),
        waist_cm: num(form.waist_cm), hip_cm: num(form.hip_cm),
        systolic_bp: num(form.systolic_bp), diastolic_bp: num(form.diastolic_bp),
        body_fat_percent: num(form.body_fat_percent), fat_mass_kg: num(form.fat_mass_kg),
        lean_mass_kg: num(form.lean_mass_kg),
        lbm_boer_kg: num(form.lbm_boer_kg),
        muscle_mass_kg: num(form.muscle_mass_kg),
        skeletal_muscle_index: num(form.skeletal_muscle_index),
        visceral_fat_area_cm2: num(form.visceral_fat_area_cm2),
        visceral_fat_level: num(form.visceral_fat_level),
        basal_metabolic_rate: num(form.basal_metabolic_rate),
        total_body_water_percent: num(form.total_body_water_percent),
        bone_mass_kg: num(form.bone_mass_kg),
        arm_circumference_cm: num(form.arm_circumference_cm),
        calf_circumference_cm: num(form.calf_circumference_cm),
        grip_strength_right_kg: num(form.grip_right_kg),
        grip_strength_left_kg: num(form.grip_left_kg),
        gait_speed_m_s: num(form.gait_speed_sec),
        sarcf_score: num(form.sarcf_score),
        five_x_sts_seconds: num(form.five_x_sts_sec),
      },
      metabolic: {
        glucose_mg_dl: num(form.glucose_mg_dl), creatinine_mg_dl: num(form.creatinine_mg_dl),
        hba1c_percent: num(form.hba1c_percent), insulin_mu_u_ml: num(form.insulin_mu_u_ml),
        albumin_g_dl: num(form.albumin_g_dl), alkaline_phosphatase_u_l: num(form.alkaline_phosphatase_u_l),
        mcv_fl: num(form.mcv_fl), rdw_percent: num(form.rdw_percent),
        wbc_k_ul: num(form.wbc_k_ul), lymphocyte_percent: num(form.lymphocyte_percent),
        ferritin_ng_ml: num(form.ferritin_ng_ml), hs_crp_mg_l: num(form.hs_crp_mg_l),
        tsh_u_iu_ml: num(form.tsh_uIU_ml), ft4_ng_dl: num(form.ft4_ng_dl),
        ft3_pg_ml: num(form.ft3_pg_ml), rt3_ng_dl: num(form.rt3_ng_dl),
        shbg_nmol_l: num(form.shbg_nmol_l), cortisol_am_mcg_dl: num(form.cortisol_am_mcg_dl),
        c_peptide_ng_ml: num(form.c_peptide_ng_ml),
        total_cholesterol_mg_dl: num(form.total_cholesterol_mg_dl),
        triglycerides_mg_dl: num(form.triglycerides_mg_dl),
        hdl_mg_dl: num(form.hdl_mg_dl), ldl_mg_dl: num(form.ldl_mg_dl),
        vldl_mg_dl: num(form.vldl_mg_dl), apob_mg_dl: num(form.apob_mg_dl),
        lpa_mg_dl: num(form.lpa_mg_dl), apoa1_mg_dl: num(form.apoa1_mg_dl),
        ast_u_l: num(form.ast_u_l), alt_u_l: num(form.alt_u_l),
        ggt_u_l: num(form.ggt_u_l), uric_acid_mg_dl: num(form.uric_acid_mg_dl),
        platelets_k_u_l: num(form.platelets_k_u_l),
        aldosterone_ng_dl: num(form.aldosterone_ng_dl),
        renin_ng_ml_h: num(form.renin_ng_ml_h),
        neutrophil_percent: num(form.neutrophil_percent),
      },
      psychometrics: {
        phq9_score: num(form.phq9_score), gad7_score: num(form.gad7_score),
        tfeq_uncontrolled_eating: num(form.tfeq_uncontrolled),
        tfeq_cognitive_restraint: num(form.tfeq_cognitive),
        tfeq_emotional_eating: num(form.tfeq_emotional),
        atenas_insomnia_score: num(form.atenas_score),
        fnq_intrusive_thoughts: num(form.fnq_intrusive),
        fnq_control_difficulty: num(form.fnq_control),
      },
      lifestyle: {
        sleep_hours: num(form.sleep_hours),
        stress_level_vas: num(form.stress_level),
        physical_activity_min_week: num(form.physical_activity_min_week),
        first_meal_time: form.first_meal_time || undefined,
        last_meal_time: form.last_meal_time || undefined,
      },
      conditions, medications,
      acosta_survey: {
        falla_de_saciedad: num(form.acosta_falla_saciedad),
        intestino_hambriento: num(form.acosta_intestino_hambriento),
        hambre_emocional: num(form.acosta_hambre_emocional),
        metabolismo_lento: num(form.acosta_metabolismo_lento),
        saciedad_temprana: num(form.acosta_saciedad_temprana),
      },
    }
  }

  const handleSubmit = async () => {
    if (!form.consent_accepted) {
      setError("Debe aceptar el consentimiento informado antes de procesar datos clínicos.")
      return
    }

    const { ok, errors: coherenceErrors, warnings: coherenceWarnings } = validateCoherence(form)

    if (!ok) {
      setError(`Error de coherencia en los datos:\n• ${coherenceErrors.join("\n• ")}`)
      return
    }

    if (coherenceWarnings.length > 0) {
      const proceed = window.confirm(
        `⚠️ Advertencia clínica — Datos inusuales detectados:\n\n• ${coherenceWarnings.join("\n• ")}\n\n¿Confirma que los valores son correctos y desea continuar?`
      )
      if (!proceed) return
    }

    setLoading(true); setError("")
    setProcessingStage("validating")
    try {
      // Verificar consentimiento existente via GET /consent/patient/{id}
      const existingConsent = await api.get<{ is_granted: boolean } | null>(`/consent/patient/${patientId}`)
      if (existingConsent && !existingConsent.is_granted) {
        setError("El paciente ha revocado su consentimiento. No se puede procesar el encuentro.")
        setLoading(false)
        return
      }
      // Si no existe consentimiento, grabarlo
      if (!existingConsent) {
        await api.post<Record<string, unknown>>("/consent/", {
          patient_id: patientId,
          consent_type: "SAMD_ANALYSIS_V1",
          is_granted: true,
        })
      }
      setProcessingStage("engines")
      const result = await api.post<EncounterResult>("/encounters/process", buildPayload())
      setProcessingStage("adjudicating")
      onSubmit(result)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error procesando encuentro")
    } finally { setLoading(false); setProcessingStage("idle") }
  }

  const steps = [
    { label: "Historia y Biometría", icon: "📋" },
    { label: "Laboratorios", icon: "🧪" },
    { label: "Psicometría y Cierre", icon: "🧠" },
  ]

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <Step0HistoriaBiometria
            form={form} set={set} toggle={toggle}
            expandedSections={expandedSections} toggleSection={toggleSection}
            aceAnswers={aceAnswers} aceScore={aceScore} handleAceAnswer={handleAceAnswer}
            patient={patient} baseline={baseline}
            limits={limits}
          />
        )
      case 1:
        return <Step1Laboratorios form={form} set={set} toggle={toggle} limits={limits} />
      case 2:
        return <Step2PsicometriaCierre form={form} set={set} patientId={patientId} />
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{baseline ? "Consulta de Control" : "Nueva Consulta"}</h2>
        <p className="text-muted-foreground">
          {baseline
            ? `Seguimiento — vs ${baseline.created_at ? new Date(baseline.created_at).toLocaleDateString("es-CO", { day: "2-digit", month: "long", year: "numeric" }) : "consulta anterior"}`
            : "Ingrese los datos clínicos del paciente"}
        </p>
      </div>
      {baseline && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-md px-4 py-3 flex items-start gap-3">
          <Activity className="h-5 w-5 text-blue-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-300">Consulta de control</p>
            <p className="text-xs text-blue-200 mt-0.5">
              Datos estables pre-cargados. Labs y biometrics están vacíos para ingresar valores actuales.
            </p>
          </div>
        </div>
      )}
      <div className="flex gap-1 overflow-x-auto pb-2">
        {steps.map((s, i) => (
          <button key={i} type="button" onClick={() => setStep(i)} className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm whitespace-nowrap transition-colors ${i === step ? "bg-primary text-primary-foreground" : i < step ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
            {s.icon}{s.label}
          </button>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle>{steps[step].label}</CardTitle></CardHeader>
        <CardContent>{renderStep()}</CardContent>
      </Card>

      {/* Gender-specific panels (only on step 0) */}
      {step === 0 && patient && (patient.gender === "female" || patient.gender === "f") && (
        <WomensHealthPanel form={form} set={set} toggle={toggle} expandedSections={expandedSections} toggleSection={toggleSection} limits={limits} />
      )}
      {step === 0 && patient && (patient.gender === "male" || patient.gender === "m") && (
        <MensHealthPanel form={form} set={set} toggle={toggle} expandedSections={expandedSections} toggleSection={toggleSection} limits={limits} />
      )}

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>Anterior</Button>
        {step < steps.length - 1 ? (
          <Button onClick={() => setStep(step + 1)}>Siguiente</Button>
        ) : (
          <Button onClick={handleSubmit} disabled={loading} className="min-w-48">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {processingStage === "validating" && "Validando Atributos..."}
                {processingStage === "engines" && "Ejecutando 43 Motores..."}
                {processingStage === "adjudicating" && "Finalizando Juicio..."}
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Ejecutar motores clínicos
              </>
            )}
          </Button>
        )}
      </div>
      {error && <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">{error}</p>}
      {prefilling && <p className="text-sm text-muted-foreground">Cargando datos de consulta previa...</p>}
    </div>
  )
}
