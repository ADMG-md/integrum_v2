"use client"

import { useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input, Label, Textarea } from "@/components/ui/form"
import { Card, CardContent } from "@/components/ui/card"
import { Brain } from "lucide-react"
import {
  Checkbox, LabField, Section, ACE_QUESTIONS, ConsultationFormState, BaselineEncounter
} from "./consultation-form-types"

interface Step0Props {
  form: ConsultationFormState
  set: (field: string, value: string) => void
  toggle: (field: string) => void
  expandedSections: Record<string, boolean>
  toggleSection: (key: string) => void
  aceAnswers: Record<number, boolean>
  aceScore: number
  handleAceAnswer: (idx: number, value: boolean) => void
  patient: { gender: string | null } | null | undefined
  baseline: BaselineEncounter | null | undefined
  limits?: Record<string, [number, number]>
}

export default function Step0HistoriaBiometria({
  form, set, toggle, expandedSections, toggleSection,
  aceAnswers, aceScore, handleAceAnswer, patient, baseline, limits
}: Step0Props) {
  const router = useRouter()

  return (
    <div className="space-y-4">
      {/* Consentimiento Informado */}
      <Card className="border-primary/50 bg-primary/5">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <input type="checkbox" id="consent" checked={form.consent_accepted}
              onChange={(e) => set("consent_accepted", e.target.checked ? "true" : "false")}
              className="h-4 w-4 mt-1 rounded border-input text-primary focus:ring-primary" />
            <div>
              <label htmlFor="consent" className="font-medium text-sm cursor-pointer">Consentimiento Informado — Habeas Data</label>
              <p className="text-xs text-muted-foreground mt-1">
                De acuerdo con la Ley 1581 de 2012 y el Decreto 1377 de 2013 de la República de Colombia,
                autorizo de manera libre, expresa, voluntaria e informada el tratamiento de mis datos personales
                y datos sensibles (información de salud) por parte de Integrum V2.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Motivo de consulta */}
      <div className="space-y-2">
        <Label>Motivo de consulta</Label>
        <Textarea value={form.reason_for_visit} onChange={(e) => set("reason_for_visit", e.target.value)} placeholder="Control de obesidad, seguimiento..." rows={2} />
      </div>

      {/* Historia Clínica */}
      <Section sectionKey="historia" title="📋 Historia Clínica" expanded={expandedSections.historia} onToggle={toggleSection}>
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Trigger de inicio</Label>
            <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.onset_trigger} onChange={(e) => set("onset_trigger", e.target.value)}>
              <option value="">Seleccionar</option>
              <option value="childhood">Infancia</option><option value="puberty">Pubertad</option>
              <option value="pregnancy">Embarazo</option><option value="menopause">Menopausia</option>
              <option value="smoking_cessation">Dejó de fumar</option><option value="medication">Medicamentos</option>
              <option value="injury">Lesión</option><option value="stress">Estrés</option>
              <option value="unknown">Desconocido</option>
            </select>
          </div>
          <LabField label="Edad de inicio" value={form.age_of_onset} onChange={(v) => set("age_of_onset", v)} placeholder="25" step="1" />
          <LabField label="Peso máximo (kg)" value={form.max_weight_ever_kg} onChange={(v) => set("max_weight_ever_kg", v)} placeholder="120" />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Tabaquismo</Label>
            <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.smoking_status} onChange={(e) => set("smoking_status", e.target.value)}>
              <option value="never">Nunca</option><option value="former">Ex-fumador</option><option value="current">Actual</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label>Alcohol</Label>
            <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.alcohol_intake} onChange={(e) => set("alcohol_intake", e.target.value)}>
              <option value="none">Ninguno</option><option value="occasional">Ocasional</option><option value="frequent">Frecuente</option>
            </select>
          </div>
          <LabField label="ACE Score (auto)" value={String(aceScore)} onChange={() => {}} placeholder="0" step="1" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2"><Label>Alergias</Label><Textarea value={form.allergies} onChange={(e) => set("allergies", e.target.value)} placeholder="NKDA..." rows={2} /></div>
          <div className="space-y-2"><Label>Otras cirugías</Label><Textarea value={form.other_surgeries} onChange={(e) => set("other_surgeries", e.target.value)} placeholder="Colecistectomía..." rows={2} /></div>
        </div>
        {baseline && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Antecedentes personales</Label>
              <Textarea value={form.personal_history} onChange={(e) => set("personal_history", e.target.value)} placeholder="Cargado de consulta anterior..." rows={3} className="text-xs" />
            </div>
            <div className="space-y-2">
              <Label>Antecedentes familiares</Label>
              <Textarea value={form.family_history} onChange={(e) => set("family_history", e.target.value)} placeholder="Cargado de consulta anterior..." rows={3} className="text-xs" />
            </div>
          </div>
        )}
        <div className="grid grid-cols-3 gap-4">
          <Checkbox label="Cirugía bariátrica" checked={form.has_bariatric_surgery} onChange={() => toggle("has_bariatric_surgery")} />
          {form.has_bariatric_surgery && (
            <>
              <LabField label="Tipo" value={form.bariatric_surgery_type} onChange={(v) => set("bariatric_surgery_type", v)} placeholder="Bypass" />
              <div className="space-y-1"><Label className="text-xs text-muted-foreground">Fecha</Label><Input type="date" value={form.bariatric_surgery_date} onChange={(e) => set("bariatric_surgery_date", e.target.value)} className="h-8 text-sm" /></div>
            </>
          )}
        </div>
      </Section>

      {/* Comorbilidades */}
      <Section sectionKey="comorbididades" title="⚕️ Comorbilidades" expanded={expandedSections.comorbididades} onToggle={toggleSection}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          <Checkbox label="Diabetes tipo 2" checked={form.has_type2_diabetes} onChange={() => toggle("has_type2_diabetes")} />
          <Checkbox label="Prediabetes" checked={form.has_prediabetes} onChange={() => toggle("has_prediabetes")} />
          <Checkbox label="Hipertensión" checked={form.has_hypertension} onChange={() => toggle("has_hypertension")} />
          <Checkbox label="Dislipidemia" checked={form.has_dyslipidemia} onChange={() => toggle("has_dyslipidemia")} />
          <Checkbox label="Hígado graso" checked={form.has_nafld} onChange={() => toggle("has_nafld")} />
          <Checkbox label="Gota" checked={form.has_gout} onChange={() => toggle("has_gout")} />
          <Checkbox label="Hipotiroidismo" checked={form.has_hypothyroidism} onChange={() => toggle("has_hypothyroidism")} />
          <Checkbox label="SOP" checked={form.has_pcos} onChange={() => toggle("has_pcos")} />
          <Checkbox label="Apnea del sueño" checked={form.has_osa} onChange={() => toggle("has_osa")} />
          <Checkbox label="ERGE" checked={form.has_gerd} onChange={() => toggle("has_gerd")} />
          <Checkbox label="ERC" checked={form.has_ckd} onChange={() => toggle("has_ckd")} />
          <Checkbox label="Insuf. cardíaca" checked={form.has_heart_failure} onChange={() => toggle("has_heart_failure")} />
          <Checkbox label="Enf. coronaria" checked={form.has_coronary_disease} onChange={() => toggle("has_coronary_disease")} />
          <Checkbox label="ACV" checked={form.has_stroke} onChange={() => toggle("has_stroke")} />
          <Checkbox label="Retinopatía" checked={form.has_retinopathy} onChange={() => toggle("has_retinopathy")} />
          <Checkbox label="Neuropatía" checked={form.has_neuropathy} onChange={() => toggle("has_neuropathy")} />
          <Checkbox label="Glaucoma" checked={form.has_glaucoma} onChange={() => toggle("has_glaucoma")} />
          <Checkbox label="Convulsiones" checked={form.has_seizures_history} onChange={() => toggle("has_seizures_history")} />
          <Checkbox label="TCA" checked={form.has_eating_disorder_history} onChange={() => toggle("has_eating_disorder_history")} />
          <Checkbox label="Ca. tiroides familiar" checked={form.family_history_thyroid_cancer} onChange={() => toggle("family_history_thyroid_cancer")} />
          <Checkbox label="Abuso sustancias" checked={form.has_active_substance_abuse} onChange={() => toggle("has_active_substance_abuse")} />
          
          <div className="col-span-full mt-3 mb-1">
            <p className="text-xs font-semibold text-indigo-400 border-b border-border/50 pb-1 flex items-center">
              <span className="mr-2">🧬</span> Variación Farmacogenómica (Anamnesis Proxy)
            </p>
          </div>
          <Checkbox label="Mialgia por Estatinas (SLCO1B1)" checked={form.has_statin_myalgia} onChange={() => toggle("has_statin_myalgia")} />
          <Checkbox label="Insomnio/Ansiedad x Cafeína (CYP1A2)" checked={form.caffeine_anxiety_insomnia} onChange={() => toggle("caffeine_anxiety_insomnia")} />
          <Checkbox label="Uso crónico IBP (Bloqueo Nutricional)" checked={form.taking_ppi_chronically} onChange={() => toggle("taking_ppi_chronically")} />
          <Checkbox label="Automedica Vitamina D" checked={form.taking_otc_vitd} onChange={() => toggle("taking_otc_vitd")} />
        </div>
      </Section>

      {/* ACE Questionnaire */}
      <Section sectionKey="ace" title="🧠 ACE Questionnaire" badge={`${aceScore}/10`} expanded={expandedSections.ace} onToggle={toggleSection}>
        <p className="text-xs text-muted-foreground mb-4">
          Experiencias Adversas en la Infancia. Cada "Sí" = 1 punto. Score ≥4 → riesgo 2x de enfermedad metabólica.
        </p>
        <div className="space-y-3">
          {ACE_QUESTIONS.map((q, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
              <p className="text-sm flex-1 mr-4">
                <span className="text-muted-foreground mr-2">{i + 1}.</span>{q}
              </p>
              <div className="flex gap-2 shrink-0">
                <button type="button" onClick={() => handleAceAnswer(i, true)}
                  className={`px-4 py-1.5 rounded-md text-sm transition-colors ${aceAnswers[i] === true ? "bg-red-500/20 text-red-400 font-medium border border-red-500/30" : "bg-muted text-muted-foreground hover:bg-accent"}`}>Sí</button>
                <button type="button" onClick={() => handleAceAnswer(i, false)}
                  className={`px-4 py-1.5 rounded-md text-sm transition-colors ${aceAnswers[i] === false ? "bg-green-500/20 text-green-400 font-medium border border-green-500/30" : "bg-muted text-muted-foreground hover:bg-accent"}`}>No</button>
              </div>
            </div>
          ))}
        </div>
        {aceScore >= 4 && (
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
            <p className="text-sm text-amber-400 font-medium">⚠️ ACE Score: {aceScore}/10 — Riesgo elevado</p>
            <p className="text-xs text-muted-foreground mt-1">Se recomienda integrar evaluación de trauma en el plan de tratamiento.</p>
          </div>
        )}
      </Section>

      {/* Biometría */}
      <Section sectionKey="biometria" title="📏 Biometría y Antropometría" expanded={expandedSections.biometria} onToggle={toggleSection}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="Peso (kg)" value={form.weight_kg} onChange={(v) => set("weight_kg", v)} placeholder="85.5" min="20" max="500" loincCode="29463-7" limits={limits} />
          <LabField label="Talla (cm)" value={form.height_cm} onChange={(v) => set("height_cm", v)} placeholder="170" min="50" max="250" loincCode="8302-2" limits={limits} />
          <LabField label="Cintura (cm)" value={form.waist_cm} onChange={(v) => set("waist_cm", v)} placeholder="98" min="30" max="300" loincCode="8280-0" limits={limits} />
          <LabField label="Cadera (cm)" value={form.hip_cm} onChange={(v) => set("hip_cm", v)} placeholder="105" min="30" max="300" />
          <LabField label="PA Sistólica" value={form.systolic_bp} onChange={(v) => set("systolic_bp", v)} placeholder="135" step="1" min="60" max="300" loincCode="8480-6" limits={limits} />
          <LabField label="PA Diastólica" value={form.diastolic_bp} onChange={(v) => set("diastolic_bp", v)} placeholder="85" step="1" min="30" max="200" loincCode="8462-4" limits={limits} />
          <LabField label="% Grasa" value={form.body_fat_percent} onChange={(v) => set("body_fat_percent", v)} placeholder="35" min="2" max="70" />
          <LabField label="Masa magra (BIA, kg)" value={form.lean_mass_kg} onChange={(v) => set("lean_mass_kg", v)} placeholder="55" min="10" max="150" />
          <LabField label="LBM Boer (kg)" value={form.lbm_boer_kg} onChange={(v) => set("lbm_boer_kg", v)} placeholder="55" min="10" max="150" />
          <LabField label="Masa muscular (kg)" value={form.muscle_mass_kg} onChange={(v) => set("muscle_mass_kg", v)} placeholder="28" min="5" max="100" />
          <LabField label="SMI (kg/m²)" value={form.skeletal_muscle_index} onChange={(v) => set("skeletal_muscle_index", v)} placeholder="7.5" min="3" max="15" />
          <LabField label="Grasa visceral (nivel BIA)" value={form.visceral_fat_level} onChange={(v) => set("visceral_fat_level", v)} placeholder="10" min="1" max="59" />
          <LabField label="Brazo (cm)" value={form.arm_circumference_cm} onChange={(v) => set("arm_circumference_cm", v)} placeholder="30" min="10" max="60" />
          <LabField label="Pantorrilla (cm)" value={form.calf_circumference_cm} onChange={(v) => set("calf_circumference_cm", v)} placeholder="35" min="15" max="60" />
        </div>
      </Section>

      {/* Estilo de vida */}
      <Section sectionKey="estilo_vida" title="🏃 Estilo de Vida" expanded={expandedSections.estilo_vida} onToggle={toggleSection}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="Horas sueño" value={form.sleep_hours} onChange={(v) => set("sleep_hours", v)} placeholder="7" />
          <LabField label="Nivel estrés (1-10)" value={form.stress_level} onChange={(v) => set("stress_level", v)} placeholder="5" step="1" />
          <LabField label="Actividad física (min/sem)" value={form.physical_activity_min_week} onChange={(v) => set("physical_activity_min_week", v)} placeholder="150" step="1" />
          <LabField label="Primera comida (hh:mm)" value={form.first_meal_time} onChange={(v) => set("first_meal_time", v)} placeholder="08:00" />
          <LabField label="Última comida (hh:mm)" value={form.last_meal_time} onChange={(v) => set("last_meal_time", v)} placeholder="20:00" />
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <Checkbox label="Ronca fuerte" checked={form.snores_loudly} onChange={() => toggle("snores_loudly")} />
          <Checkbox label="Cansancio diurno" checked={form.daytime_tiredness} onChange={() => toggle("daytime_tiredness")} />
          <Checkbox label="Apnea observada" checked={form.observed_apnea} onChange={() => toggle("observed_apnea")} />
        </div>
        <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Cuestionarios Psicométricos</p>
              <p className="text-xs text-muted-foreground">PHQ-9, GAD-7, TFEQ-R18, Atenas, FNQ</p>
            </div>
            <Button size="sm" variant="outline" onClick={() => router.push(`/psicologia/${(window.location.pathname.split("/").pop() || "")}`)}>
              <Brain className="h-4 w-4 mr-2" />Ir a Psicología
            </Button>
          </div>
        </div>
      </Section>
    </div>
  )
}
