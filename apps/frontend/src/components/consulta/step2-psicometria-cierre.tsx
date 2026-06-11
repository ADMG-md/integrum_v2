"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Label, Textarea } from "@/components/ui/form"
import { Button } from "@/components/ui/button"
import { LabField, ConsultationFormState } from "./consultation-form-types"
import { Brain, ChevronRight, Activity } from "lucide-react"
import AcostaSurvey, { AcostaSurveyResults } from "./acosta-survey"

interface Step2CierreProps {
  form: ConsultationFormState
  set: (field: string, value: string) => void
  patientId: string
}

export default function Step2PsicometriaCierre({ form, set, patientId }: Step2CierreProps) {
  const router = useRouter()
  const hasPsychData = !!(form.phq9_score || form.gad7_score || form.tfeq_uncontrolled)
  const [showAcostaSurvey, setShowAcostaSurvey] = useState(false)

  const handleAcostaComplete = (results: AcostaSurveyResults) => {
    set("acosta_falla_saciedad", String(results.saciacion_alterada_score))
    set("acosta_intestino_hambriento", String(results.saciedad_acelerada_score))
    set("acosta_hambre_emocional", String(results.hambre_hedonica_score))
    set("acosta_metabolismo_lento", String(results.gasto_energetico_reducido_score))
    set("acosta_saciedad_temprana", String(results.saciedad_temprana_score))
  }

  if (showAcostaSurvey) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => setShowAcostaSurvey(false)}>
          ← Volver a Scores Psicométricos
        </Button>
        <AcostaSurvey patientId={patientId} onComplete={handleAcostaComplete} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Encuesta de Fenotipo Acosta */}
      <div className="border rounded-lg p-4 bg-muted/30">
        <div className="flex items-start justify-between">
          <div>
            <Label className="text-sm font-medium">Encuesta de Fenotipo de Obesidad</Label>
            <p className="text-xs text-muted-foreground mt-1">
              Identifica el fenotipo fisiopatológico: Falla de Saciedad, Intestino Hambriento, Hambre Emocional o Metabolismo Lento.
              Basada en Acosta et al. 2023 (Mayo Clinic).
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 ml-4"
            onClick={() => setShowAcostaSurvey(true)}
          >
            <Activity className="h-4 w-4 mr-1.5" />
            Iniciar encuesta
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Psicometría */}
      <div>
        <Label className="mb-2 block text-sm font-medium">Scores Psicométricos</Label>

        {hasPsychData ? (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-md px-4 py-3 flex items-start gap-3 mb-3">
            <span className="text-blue-400 mt-0.5">ℹ</span>
            <div>
              <p className="text-sm font-medium text-blue-300">Scores pre-cargados de Psicología</p>
              <p className="text-xs text-blue-200 mt-0.5">
                Estos valores fueron registrados en la evaluación psicológica previa. Puedes modificarlos si es necesario.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-md px-4 py-3 mb-3">
            <p className="text-sm text-amber-300 mb-2">
              Si ya aplicaste los cuestionarios en Psicología, ingresa los scores aquí.
            </p>
            <Button
              size="sm"
              variant="outline"
              className="text-amber-300 border-amber-500/30 hover:bg-amber-500/20"
              onClick={() => router.push(`/psicologia/${patientId}`)}
            >
              <Brain className="h-4 w-4 mr-1.5" />
              Ir a Psicometría
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="PHQ-9" value={form.phq9_score} onChange={(v) => set("phq9_score", v)} placeholder="10" step="1" />
          <LabField label="GAD-7" value={form.gad7_score} onChange={(v) => set("gad7_score", v)} placeholder="8" step="1" />
          <LabField label="TFEQ Uncontrolled" value={form.tfeq_uncontrolled} onChange={(v) => set("tfeq_uncontrolled", v)} placeholder="5" step="1" />
          <LabField label="TFEQ Cognitivo" value={form.tfeq_cognitive} onChange={(v) => set("tfeq_cognitive", v)} placeholder="4" step="1" />
          <LabField label="TFEQ Emocional" value={form.tfeq_emotional} onChange={(v) => set("tfeq_emotional", v)} placeholder="6" step="1" />
          <LabField label="Atenas" value={form.atenas_score} onChange={(v) => set("atenas_score", v)} placeholder="10" step="1" />
          <LabField label="FNQ Intrusivo" value={form.fnq_intrusive} onChange={(v) => set("fnq_intrusive", v)} placeholder="3" step="1" />
          <LabField label="FNQ Control" value={form.fnq_control} onChange={(v) => set("fnq_control", v)} placeholder="2" step="1" />
        </div>
      </div>

      {/* Condiciones */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Condiciones (CIE-10)</Label>
        <Textarea value={form.conditions_text} onChange={(e) => set("conditions_text", e.target.value)} placeholder={"E66.0|Obesidad\nI10|Hipertensión esencial"} rows={4} className="font-mono text-sm" />
        <p className="text-xs text-muted-foreground mt-1">Formato: código|nombre (una por línea)</p>
      </div>

      {/* Medicamentos */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Medicamentos</Label>
        <Textarea value={form.medications_text} onChange={(e) => set("medications_text", e.target.value)} placeholder={"Metformina|500mg|BID\nLosartán|50mg|Día"} rows={4} className="font-mono text-sm" />
        <p className="text-xs text-muted-foreground mt-1">Formato: nombre|dosis|frecuencia (uno por línea)</p>
      </div>
    </div>
  )
}
