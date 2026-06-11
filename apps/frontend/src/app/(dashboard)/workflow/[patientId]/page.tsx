"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AdjudicationResult } from "@/types"
import { api } from "@/lib/api"
import {
  CheckCircle, Circle, Clock, ChevronRight, User, Brain, Scale,
  Stethoscope, FileText, ArrowRight, Loader2,
} from "lucide-react"

interface Patient {
  id: string
  external_id: string
  full_name: string
  email: string | null
  created_at: string
}

interface WorkflowEncounter {
  id: string
  reason_for_visit: string | null
  status: string
  phenotype_result: Record<string, AdjudicationResult> | null
}

interface WorkflowStep {
  id: string
  label: string
  role: string
  icon: React.ReactNode
  description: string
  status: "pending" | "in_progress" | "completed"
  route: string
  completedAt: string | null
}

export default function WorkflowPage() {
  const params = useParams()
  const patientId = params.patientId as string
  const router = useRouter()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [loading, setLoading] = useState(true)
  const [encounters, setEncounters] = useState<WorkflowEncounter[]>([])

  useEffect(() => {
    if (!patientId) return
    setLoading(true)

    api.get<Patient[]>("/patients/")
      .then((patients) => {
        const p = patients.find((x) => x.id === patientId)
        setPatient(p || null)
      })
      .catch(() => {})

    api.get<WorkflowEncounter[]>(`/encounters/patient/${patientId}`)
      .then((data) => {
        setEncounters(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [patientId])

  // Determine workflow status based on encounters
  const hasConsent = true // Assume consent exists (would need a consent check endpoint)
  const hasPsychology = encounters.some((e) => e.reason_for_visit?.includes("psicol"))
  const hasNutrition = encounters.length > 0
  const hasMedical = encounters.some((e) => e.status === "FINALIZED" || e.status === "ANALYZED")

  const steps: WorkflowStep[] = [
    {
      id: "registro",
      label: "Registro y Consentimiento",
      role: "AdminStaff",
      icon: <FileText className="h-5 w-5" />,
      description: "Datos demográficos, consentimiento informado",
      status: hasConsent ? "completed" : "pending",
      route: `/pacientes`,
      completedAt: patient?.created_at || null,
    },
    {
      id: "psicologia",
      label: "Evaluación Psicológica",
      role: "Psicóloga",
      icon: <Brain className="h-5 w-5" />,
      description: "PHQ-9, GAD-7, TFEQ-R18, Atenas, FNQ",
      status: hasPsychology ? "completed" : "in_progress",
      route: `/psicologia/${patientId}`,
      completedAt: null,
    },
    {
      id: "nutricion",
      label: "Evaluación Nutricional",
      role: "Nutrióloga",
      icon: <Scale className="h-5 w-5" />,
      description: "Biometría, antropometría, BIA, estilo de vida",
      status: hasNutrition ? "completed" : "pending",
      route: `/consulta/${patientId}`,
      completedAt: null,
    },
    {
      id: "medico",
      label: "Consulta Médica",
      role: "Médico",
      icon: <Stethoscope className="h-5 w-5" />,
      description: "Labs, fenotipado, adjudicación, plan terapéutico",
      status: hasMedical ? "completed" : "pending",
      route: `/consulta/${patientId}`,
      completedAt: null,
    },
  ]

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Flujo de Trabajo</h2>
        <p className="text-muted-foreground text-center py-12">
          <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
          Cargando...
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Flujo de Trabajo</h2>
        <p className="text-muted-foreground">
          {patient ? patient.full_name : "Paciente"} · {encounters.length} encuentro(s)
        </p>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Progreso del Paciente</CardTitle>
          <CardDescription>
            {steps.filter((s) => s.status === "completed").length}/{steps.length} pasos completados
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-center flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    step.status === "completed"
                      ? "bg-green-500/20 text-green-400"
                      : step.status === "in_progress"
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {step.status === "completed" ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <Circle className="h-4 w-4" />
                  )}
                </div>
                {i < steps.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 ${
                      step.status === "completed" ? "bg-green-500/50" : "bg-muted"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step) => (
          <Card
            key={step.id}
            className={`cursor-pointer transition-colors hover:border-primary/50 ${
              step.status === "completed" ? "border-green-500/30" : ""
            }`}
            onClick={() => router.push(step.route)}
          >
            <CardContent className="flex items-center gap-4 p-5">
              <div
                className={`p-3 rounded-lg shrink-0 ${
                  step.status === "completed"
                    ? "bg-green-500/20 text-green-400"
                    : step.status === "in_progress"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {step.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium">{step.label}</p>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
                    {step.role}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {step.status === "completed" && (
                  <span className="text-xs text-green-400 flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" />
                    Completado
                  </span>
                )}
                {step.status === "in_progress" && (
                  <span className="text-xs text-primary flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    En progreso
                  </span>
                )}
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <Button onClick={() => router.push(`/consulta/${patientId}`)}>
          <Stethoscope className="h-4 w-4 mr-2" />
          Iniciar consulta médica
        </Button>
        <Button variant="outline" onClick={() => router.push("/pacientes")}>
          Volver a pacientes
        </Button>
      </div>
    </div>
  )
}
