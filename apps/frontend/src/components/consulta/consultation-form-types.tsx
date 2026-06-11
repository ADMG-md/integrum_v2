import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input, Label, Textarea } from "@/components/ui/form"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, ClipboardList, Upload, CheckCircle, AlertCircle, Loader2, ChevronDown, ChevronRight } from "lucide-react"

// ============================================================
// Shared sub-components (defined outside to prevent focus loss)
// ============================================================

export const Checkbox = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) => (
  <label className="flex items-center gap-2 cursor-pointer select-none">
    <input type="checkbox" checked={checked} onChange={onChange} className="h-4 w-4 rounded border-input text-primary focus:ring-primary" />
    <span className="text-sm">{label}</span>
  </label>
)

export const LabField = ({
  label, value, onChange, placeholder, step, min, max, loincCode, limits
}: {
  label: string; value: string; onChange: (v: string) => void
  placeholder: string; step?: string; min?: string; max?: string;
  loincCode?: string; limits?: Record<string, [number, number]>
}) => {
  const finalMin = min || (loincCode && limits?.[loincCode]?.[0]?.toString());
  const finalMax = max || (loincCode && limits?.[loincCode]?.[1]?.toString());
  
  const isOutOfRange = value && finalMin && finalMax && (
    parseFloat(value) < parseFloat(finalMin) || parseFloat(value) > parseFloat(finalMax)
  );

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-end">
        <Label className="text-xs text-muted-foreground">{label}</Label>
        {finalMin && finalMax && (
          <span className="text-[10px] text-muted-foreground/60">
            rango: {finalMin}–{finalMax}
          </span>
        )}
      </div>
      <Input
        type="number" step={step || "0.01"} value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder} 
        className={`h-8 text-sm ${isOutOfRange ? "border-destructive focus-visible:ring-destructive bg-destructive/5" : ""}`}
        min={finalMin} max={finalMax}
      />
      {isOutOfRange && (
        <p className="text-[10px] text-destructive font-medium animate-pulse">
           Valor fuera de límites fisiológicos.
        </p>
      )}
    </div>
  )
}

export const Section = ({ sectionKey, title, badge, expanded, onToggle, children }: {
  sectionKey: string; title: string; badge?: string;
  expanded: boolean; onToggle: (key: string) => void; children: React.ReactNode
}) => (
  <div className="border rounded-lg overflow-hidden">
    <button
      type="button"
      className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
      onClick={() => onToggle(sectionKey)}
    >
      <span className="text-sm font-medium">{title}</span>
      <div className="flex items-center gap-2">
        {badge && <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">{badge}</span>}
        {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
      </div>
    </button>
    {expanded && <div className="p-4 space-y-4">{children}</div>}
  </div>
)

// ============================================================
// ACE Questionnaire data
// ============================================================

export const ACE_QUESTIONS = [
  "Un adulto frecuentemente te insultaba, humillaba o te hacía sentir menos",
  "Un adulto frecuentemente te empujaba, golpeaba o te lastimaba físicamente",
  "Un adulto te tocaba o besaba de forma sexual inapropiada",
  "Sentías que no tenías a quién acudir por protección",
  "Sentías que tu familia no se apoyaba mutuamente",
  "Tus padres se separaron o divorciaron",
  "Un familiar tenía problemas de alcohol o drogas",
  "Un familiar estaba deprimido o intentó suicidarse",
  "Un familiar fue encarcelado",
  "Presenciaste violencia doméstica",
]

// ============================================================
// CSV Import component
// ============================================================

export const CsvImport = ({ onImport }: { onImport: (labs: Record<string, number>) => void }) => {
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const lines = text.split("\n").filter(Boolean)
      if (lines.length < 2) { setStatus({ type: "error", message: "CSV vacío" }); return }

      const headers = lines[0].split(",").map(h => h.trim().toLowerCase())
      const values = lines[1].split(",").map(v => v.trim())

      const loincMap: Record<string, string> = {
        "glucose": "glucose_mg_dl", "glucosa": "glucose_mg_dl", "2339-0": "glucose_mg_dl",
        "hba1c": "hba1c_percent", "a1c": "hba1c_percent", "hemoglobina glicosilada": "hba1c_percent",
        "insulin": "insulin_mu_u_ml", "insulina": "insulin_mu_u_ml",
        "creatinine": "creatinine_mg_dl", "creatinina": "creatinine_mg_dl",
        "uric acid": "uric_acid_mg_dl", "acido urico": "uric_acid_mg_dl",
        "ast": "ast_u_l", "alt": "alt_u_l", "ggt": "ggt_u_l",
        "alkaline phosphatase": "alkaline_phosphatase_u_l", "fosfatasa alcalina": "alkaline_phosphatase_u_l",
        "wbc": "wbc_k_ul", "leucocitos": "wbc_k_ul",
        "lymphocytes": "lymphocyte_percent", "linfocitos": "lymphocyte_percent",
        "neutrophils": "neutrophil_percent", "neutrofilos": "neutrophil_percent",
        "mcv": "mcv_fl", "rdw": "rdw_percent",
        "platelets": "platelets_k_u_l", "plaquetas": "platelets_k_u_l",
        "crp": "hs_crp_mg_l", "hs-crp": "hs_crp_mg_l", "proteina c reactiva": "hs_crp_mg_l",
        "ferritin": "ferritin_ng_ml", "ferritina": "ferritin_ng_ml",
        "albumin": "albumin_g_dl", "albumina": "albumin_g_dl",
        "tsh": "tsh_uIU_ml", "ft4": "ft4_ng_dl", "ft3": "ft3_pg_ml",
        "shbg": "shbg_nmol_l", "cortisol": "cortisol_am_mcg_dl",
        "total cholesterol": "total_cholesterol_mg_dl", "colesterol total": "total_cholesterol_mg_dl",
        "ldl": "ldl_mg_dl", "hdl": "hdl_mg_dl",
        "triglycerides": "triglycerides_mg_dl", "trigliceridos": "triglycerides_mg_dl",
        "apob": "apob_mg_dl", "apoa1": "apoa1_mg_dl",
        "vitamin d": "vitamin_d_ng_ml", "vitamina d": "vitamin_d_ng_ml",
        "vitamin b12": "vitamin_b12_pg_ml", "vitamina b12": "vitamin_b12_pg_ml",
        "testosterone": "testosterone_total_ng_dl", "testosterona": "testosterone_total_ng_dl",
        "psa": "psa_ng_ml",
      }

      const labs: Record<string, number> = {}
      let count = 0
      headers.forEach((header, i) => {
        const field = loincMap[header]
        if (field) {
          const num = parseFloat(values[i])
          if (!isNaN(num)) { labs[field] = num; count++ }
        }
      })

      if (count > 0) {
        onImport(labs)
        setStatus({ type: "success", message: `${count} labs importados` })
      } else {
        setStatus({ type: "error", message: "No se reconocieron columnas. Use headers: glucose, hba1c, ldl, hdl, etc." })
      }
    } catch {
      setStatus({ type: "error", message: "Error leyendo CSV" })
    }
  }

  return (
    <div className="p-4 border-2 border-dashed rounded-lg border-muted-foreground/25 text-center">
      {status && (
        <p className={`text-xs mb-2 ${status.type === "success" ? "text-green-400" : "text-destructive"}`}>
          {status.message}
        </p>
      )}
      <input ref={inputRef} type="file" accept=".csv,.tsv,.txt" className="hidden" onChange={handleFile} />
      <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
        <ClipboardList className="h-4 w-4 mr-2" />Importar CSV
      </Button>
      <p className="text-xs text-muted-foreground mt-2">Headers: glucose, hba1c, ldl, hdl, triglycerides, etc.</p>
    </div>
  )
}

// ============================================================
// Form type definition
// ============================================================

export interface ConsultationFormState {
  consent_accepted: boolean
  reason_for_visit: string
  onset_trigger: string
  age_of_onset: string
  max_weight_ever_kg: string
  has_type2_diabetes: boolean
  has_prediabetes: boolean
  has_hypertension: boolean
  has_dyslipidemia: boolean
  has_nafld: boolean
  has_gout: boolean
  has_hypothyroidism: boolean
  has_pcos: boolean
  has_osa: boolean
  has_gerd: boolean
  has_ckd: boolean
  has_heart_failure: boolean
  has_coronary_disease: boolean
  has_stroke: boolean
  has_retinopathy: boolean
  has_neuropathy: boolean
  has_bariatric_surgery: boolean
  bariatric_surgery_type: string
  bariatric_surgery_date: string
  other_surgeries: string
  allergies: string
  smoking_status: string
  alcohol_intake: string
  has_glaucoma: boolean
  has_seizures_history: boolean
  has_eating_disorder_history: boolean
  family_history_thyroid_cancer: boolean
  has_statin_myalgia: boolean
  caffeine_anxiety_insomnia: boolean
  taking_otc_vitd: boolean
  taking_ppi_chronically: boolean
  has_active_substance_abuse: boolean
  ace_score: string
  weight_kg: string
  height_cm: string
  waist_cm: string
  hip_cm: string
  systolic_bp: string
  diastolic_bp: string
  body_fat_percent: string
  fat_mass_kg: string
  lean_mass_kg: string
  lbm_boer_kg: string
  muscle_mass_kg: string
  skeletal_muscle_index: string
  visceral_fat_area_cm2: string
  visceral_fat_level: string
  basal_metabolic_rate: string
  total_body_water_percent: string
  bone_mass_kg: string
  arm_circumference_cm: string
  calf_circumference_cm: string
  glucose_mg_dl: string
  hba1c_percent: string
  insulin_mu_u_ml: string
  c_peptide_ng_ml: string
  creatinine_mg_dl: string
  uric_acid_mg_dl: string
  ast_u_l: string
  alt_u_l: string
  ggt_u_l: string
  alkaline_phosphatase_u_l: string
  wbc_k_ul: string
  lymphocyte_percent: string
  neutrophil_percent: string
  mcv_fl: string
  rdw_percent: string
  platelets_k_u_l: string
  hs_crp_mg_l: string
  ferritin_ng_ml: string
  albumin_g_dl: string
  tsh_uIU_ml: string
  ft4_ng_dl: string
  ft3_pg_ml: string
  rt3_ng_dl: string
  shbg_nmol_l: string
  cortisol_am_mcg_dl: string
  aldosterone_ng_dl: string
  renin_ng_ml_h: string
  gada_antibodies: boolean
  total_cholesterol_mg_dl: string
  ldl_mg_dl: string
  hdl_mg_dl: string
  triglycerides_mg_dl: string
  vldl_mg_dl: string
  apob_mg_dl: string
  lpa_mg_dl: string
  apoa1_mg_dl: string
  phq9_score: string
  gad7_score: string
  tfeq_uncontrolled: string
  tfeq_cognitive: string
  tfeq_emotional: string
  atenas_score: string
  fnq_intrusive: string
  fnq_control: string
  sleep_hours: string
  stress_level: string
  physical_activity_min_week: string
  first_meal_time: string
  last_meal_time: string
  snores_loudly: boolean
  daytime_tiredness: boolean
  observed_apnea: boolean
  conditions_text: string
  medications_text: string
  personal_history: string
  family_history: string
  pregnancy_status: string
  menopausal_status: string
  cycle_regularity: string
  last_menstrual_period: string
  has_endometriosis: boolean
  has_history_preeclampsia: boolean
  has_history_gestational_diabetes: boolean
  contraception_method: string
  on_hrt: boolean
  ferriman_gallwey_score: string
  has_erectile_dysfunction: boolean
  iief5_score: string
  has_prostate_issues: boolean
  has_male_pattern_baldness: boolean
  has_gynecomastia: boolean
  testosterone_total_ng_dl: string
  amh_ng_ml: string
  lh_u_l: string
  fsh_u_l: string
  estradiol_pg_ml: string
  prolactin_ng_ml: string
  dhea_s_mcg_dl: string
  psa_ng_ml: string
  vitamin_d_ng_ml: string
  vitamin_b12_pg_ml: string
  grip_right_kg: string
  grip_left_kg: string
  gait_speed_sec: string
  five_x_sts_sec: string
  sarcf_score: string
  acosta_falla_saciedad: string
  acosta_intestino_hambriento: string
  acosta_hambre_emocional: string
  acosta_metabolismo_lento: string
  acosta_saciedad_temprana: string
}

export interface BaselineEncounter {
  id: string
  phenotype_result: Record<string, unknown> | null
  clinical_notes: string | null
  plan_of_action: Record<string, unknown> | null
  personal_history: string | null
  family_history: string | null
  reason_for_visit: string | null
  psychometrics: {
    phq9_score?: number | null
    gad7_score?: number | null
    tfeq_uncontrolled_eating?: number | null
    tfeq_cognitive_restraint?: number | null
    tfeq_emotional_eating?: number | null
    atenas_insomnia_score?: number | null
    fnq_intrusive_thoughts?: number | null
    fnq_control_difficulty?: number | null
  } | null
  created_at: string | null
}

// ============================================================
// Coherence validation (extracted for reuse)
// ============================================================

const num = (v: string) => (v ? parseFloat(v) : undefined)

export const validateCoherence = (form: ConsultationFormState): { ok: boolean; errors: string[]; warnings: string[] } => {
  const errors: string[] = []
  const warnings: string[] = []

  const sbp = num(form.systolic_bp)
  const dbp = num(form.diastolic_bp)
  const wt = num(form.weight_kg)
  const ht = num(form.height_cm)
  const gluc = num(form.glucose_mg_dl)
  const hba1c = num(form.hba1c_percent)
  const tsh = num(form.tsh_uIU_ml)
  const ft4 = num(form.ft4_ng_dl)
  const waist = num(form.waist_cm)
  const totalChol = num(form.total_cholesterol_mg_dl)
  const hdl = num(form.hdl_mg_dl)
  const ldl = num(form.ldl_mg_dl)
  const tg = num(form.triglycerides_mg_dl)
  const vldl = num(form.vldl_mg_dl)
  const ferritin = num(form.ferritin_ng_ml)

  // --- HARD BLOCKS ---
  if (sbp !== undefined && dbp !== undefined) {
    if (sbp < dbp) {
      errors.push(`PA imposible: sistólica (${sbp}) < diastólica (${dbp}). Verifique los valores.`)
    } else if (sbp === dbp) {
      errors.push(`PA imposible: sistólica igual a diastólica (${sbp}/${dbp}). Presión de pulso = 0 es incompatible con vida.`)
    }
  }

  if (wt !== undefined && ht !== undefined && ht > 0) {
    const bmi = wt / Math.pow(ht / 100, 2)
    if (bmi < 10) {
      errors.push(`IMC resultante ${bmi.toFixed(1)} kg/m² es fisiológicamente imposible. ¿Ingresó la talla en metros en vez de centímetros? (ej. 1.70 → 170)`)
    }
  }

  if (totalChol !== undefined && hdl !== undefined && totalChol < hdl) {
    errors.push(`Colesterol total (${totalChol}) < HDL (${hdl}). LDL resultante sería negativo. Verifique si los campos están invertidos.`)
  }

  if (ldl !== undefined && totalChol !== undefined && ldl > totalChol) {
    errors.push(`LDL (${ldl} mg/dL) no puede superar el colesterol total (${totalChol} mg/dL). Verifique error de ingreso o de laboratorio.`)
  }

  if (tg !== undefined && hba1c !== undefined && tg > 400) {
    errors.push(
      `TG ${tg} mg/dL interfiere con el ensayo de HbA1c — resultado potencialmente inválido. ` +
      `Con TG >400, el método por intercambio iónico sobreestima HbA1c. ` +
      `Reconfirmar por HPLC o ensayo de boronato después de normalizar TG. ` +
      `Registre HbA1c solo si el laboratorio certificó método no afectado por hipertrigliceridemia.`
    )
  }

  if (tg !== undefined && vldl !== undefined && tg < vldl) {
    errors.push(`TG (${tg} mg/dL) no puede ser menor que VLDL (${vldl} mg/dL). VLDL = TG/5 por definición. Verifique si los campos están invertidos.`)
  }

  if (gluc !== undefined && hba1c !== undefined) {
    const eAG = hba1c * 28.7 - 46.7
    const diff = Math.abs(gluc - eAG)
    if (diff > 120 && eAG > 0) {
      const direction = gluc > eAG ? 'mayor' : 'menor'
      errors.push(
        `Glucosa puntual (${gluc} mg/dL) muy diferente del promedio esperado por HbA1c ${hba1c}% ` +
        `(eAG ≈ ${eAG.toFixed(0)} mg/dL, diff=${diff.toFixed(0)}). ` +
        `Posibles causas: (1) error de unidad — ¿glucosa en mmol/L en vez de mg/dL? ` +
        `(2) glucosa postprandial vs HbA1c de diferente periodo. ` +
        `(3) anemia hemolítica que falsea HbA1c. Confirmar ambos valores.`
      )
    }
  }

  // --- SOFT WARNINGS ---
  if (gluc !== undefined && hba1c !== undefined) {
    if (gluc > 300 && hba1c < 5.8) {
      warnings.push(`Discordancia glucosa/HbA1c: glucosa ${gluc} mg/dL con HbA1c ${hba1c}% es clínicamente inusual. Causas posibles: hemoglobinopatía, hemólisis activa, transfusión reciente, o error de ingreso.`)
    }
  }

  if (tsh !== undefined && ft4 !== undefined) {
    if (tsh > 10 && ft4 > 1.8) {
      warnings.push(`Discordancia tiroidea: TSH ${tsh} μIU/mL alto con FT4 ${ft4} ng/dL elevado. La relación normal es inversa. Considere interferencia de ensayo, anticuerpos heterófilos, o hipotiroidismo central.`)
    }
  }

  if (waist !== undefined && ht !== undefined && waist > ht && waist > 200) {
    warnings.push(`Cintura (${waist} cm) supera la talla (${ht} cm). Confirme que no están invertidos los campos.`)
  }

  if (tsh !== undefined && ft4 !== undefined) {
    if (tsh < 0.1 && ft4 < 0.5) {
      warnings.push(
        `TSH muy suprimido (${tsh} μIU/mL) con FT4 muy bajo (${ft4} ng/dL): ` +
        `patrón inusual. En hipertiroidismo severo, FT4 típicamente está elevado. ` +
        `Considere: interferencia de biotina (suplementos >5mg/día), anticuerpos heterófilos, ` +
        `hipotiroidismo central, o error de laboratorio. Repetir sin suplementos 48h antes.`
      )
    }
  }

  if (ferritin !== undefined && ferritin < 15) {
    warnings.push(
      `Ferritina ${ferritin} ng/mL — déficit de hierro severo (< 15 ng/mL, umbral OMS). ` +
      `Impacto metabólico directo: anemia ferropénica falsea HbA1c, ` +
      `afecta función tiroidea, deteriora metabolismo energético. ` +
      `Considerar suplementación antes de interpretar HbA1c y TSH.`
    )
  }

  return { ok: errors.length === 0, errors, warnings }
}
