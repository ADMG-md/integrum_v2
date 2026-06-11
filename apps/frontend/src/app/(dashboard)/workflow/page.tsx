"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/form"
import { api } from "@/lib/api"
import {
  Workflow, Search, ChevronRight, CheckCircle, Clock, Circle,
  User, Brain, Scale, Stethoscope,
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
}

export default function WorkflowPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [encountersByPatient, setEncountersByPatient] = useState<Record<string, WorkflowEncounter[]>>({})
  const router = useRouter()

  useEffect(() => {
    setLoading(true)

    api.get<Patient[]>("/patients/")
      .then((data) => {
        const patients = Array.isArray(data) ? data : []
        setPatients(patients)
        // Fetch encounters for each patient
        const promises = patients.map(async (p) => {
          const encs = await api.get<WorkflowEncounter[]>(`/encounters/patient/${p.id}`).catch(() => [])
          return { id: p.id, encounters: Array.isArray(encs) ? encs : [] }
        })
        Promise.all(promises).then((results) => {
          const map: Record<string, WorkflowEncounter[]> = {}
          results.forEach((r) => { map[r.id] = r.encounters })
          setEncountersByPatient(map)
          setLoading(false)
        })
      })
      .catch(() => setLoading(false))
  }, [])

  const getWorkflowStatus = (patientId: string) => {
    const encs = encountersByPatient[patientId] || []
    const hasPsychology = encs.some((e) => e.reason_for_visit?.toLowerCase().includes("psicol"))
    const hasNutrition = encs.length > 0
    const hasMedical = encs.some((e) => e.status === "FINALIZED" || e.status === "ANALYZED")

    const steps = [
      { label: "Registro", icon: <User className="h-3 w-3" />, done: true },
      { label: "Psicología", icon: <Brain className="h-3 w-3" />, done: hasPsychology },
      { label: "Nutrición", icon: <Scale className="h-3 w-3" />, done: hasNutrition },
      { label: "Médico", icon: <Stethoscope className="h-3 w-3" />, done: hasMedical },
    ]

    const completed = steps.filter((s) => s.done).length
    const isComplete = completed === steps.length

    return { steps, completed, isComplete }
  }

  const filtered = patients.filter(
    (p) =>
      p.full_name.toLowerCase().includes(search.toLowerCase()) ||
      p.external_id.toLowerCase().includes(search.toLowerCase()),
  )

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Flujo de Trabajo</h2>
        <p className="text-muted-foreground text-center py-12">Cargando pacientes...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Flujo de Trabajo</h2>
        <p className="text-muted-foreground">Estado del proceso multidisciplinario por paciente</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          className="pl-10"
          placeholder="Buscar paciente..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No se encontraron pacientes
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((patient) => {
            const { steps, completed, isComplete } = getWorkflowStatus(patient.id)
            return (
              <Card
                key={patient.id}
                className={`cursor-pointer transition-colors hover:border-primary/50 ${
                  isComplete ? "border-green-500/30" : ""
                }`}
                onClick={() => router.push(`/workflow/${patient.id}`)}
              >
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-medium">{patient.full_name}</p>
                      <p className="text-sm text-muted-foreground">
                        ID: {patient.external_id}
                        {patient.email && ` · ${patient.email}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {isComplete ? (
                        <span className="text-xs text-green-400 flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          Completo
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {completed}/4 pasos
                        </span>
                      )}
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>

                  {/* Progress Steps */}
                  <div className="flex items-center gap-1">
                    {steps.map((step, i) => (
                      <div key={i} className="flex items-center flex-1">
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                            step.done
                              ? "bg-green-500/20 text-green-400"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {step.done ? (
                            <CheckCircle className="h-3.5 w-3.5" />
                          ) : (
                            <Circle className="h-3.5 w-3.5" />
                          )}
                        </div>
                        {i < steps.length - 1 && (
                          <div
                            className={`flex-1 h-0.5 mx-1 ${
                              step.done ? "bg-green-500/50" : "bg-muted"
                            }`}
                          />
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Step Labels */}
                  <div className="flex gap-1 mt-1">
                    {steps.map((step, i) => (
                      <div key={i} className="flex-1 text-center">
                        <span className="text-[10px] text-muted-foreground">{step.label}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
