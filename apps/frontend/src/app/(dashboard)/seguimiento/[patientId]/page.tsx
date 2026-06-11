"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AdjudicationResult } from "@/types"
import { api } from "@/lib/api"
import {
  Calendar, TrendingUp, Activity, ChevronRight, FileText,
  ArrowUp, ArrowDown, Minus, Stethoscope, Clock,
} from "lucide-react"
import PatientTimeline from "@/components/patient/PatientTimeline"

interface Encounter {
  id: string
  patient_id: string
  status: string
  reason_for_visit: string | null
  phenotype_result: Record<string, AdjudicationResult> | null
  clinical_notes: string | null
  agreement_rate: number | null
  created_at: string
}

export default function SeguimientoPage() {
  const params = useParams()
  const patientId = params.patientId as string
  const router = useRouter()
  const [encounters, setEncounters] = useState<Encounter[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEncounter, setSelectedEncounter] = useState<string | null>(null)

  useEffect(() => {
    if (!patientId) return
    api.get<Encounter[]>(`/encounters/patient/${patientId}`)
      .then((data) => {
        setEncounters(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [patientId])

  const getMetricTrend = (metric: string) => {
    if (encounters.length < 2) return null
    const values = encounters
      .map((e) => {
        const results = e.phenotype_result || {}
        for (const [, r] of Object.entries(results)) {
          const rec = r as AdjudicationResult
          if (rec?.calculated_value?.includes(metric) || rec?.clinical_profile?.includes(metric)) {
            return rec.calculated_value || rec.clinical_profile
          }
        }
        return null
      })
      .filter(Boolean)

    if (values.length < 2) return null
    const last = values[values.length - 1]
    const prev = values[values.length - 2]
    if (last === prev) return { icon: <Minus className="h-3 w-3" />, color: "text-muted-foreground" }
    return {
      icon: <ArrowUp className="h-3 w-3" />,
      color: "text-yellow-400",
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("es-CO", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Seguimiento del Paciente</h2>
        <p className="text-muted-foreground text-center py-12">Cargando historial...</p>
      </div>
    )
  }

  if (encounters.length === 0) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Seguimiento del Paciente</h2>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Sin encuentros previos</p>
            <p className="text-sm mt-2">Este paciente aún no tiene consultas procesadas</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Extract key metrics from encounters
  const latestEncounter = encounters[encounters.length - 1]
  const latestResults = latestEncounter.phenotype_result || {}

  const getMotorValue = (motorName: string) => {
    const r = latestResults[motorName]
    if (!r) return "N/A"
    return r.calculated_value || r.clinical_profile || r.status || "N/A"
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Seguimiento del Paciente</h2>
        <p className="text-muted-foreground">{encounters.length} encuentro(s) registrado(s)</p>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Fenotipo Actual</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{getMotorValue("AcostaPhenotypeMotor")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">EOSS Stage</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{getMotorValue("EOSSStagingMotor")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Última Consulta</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold">{formatDate(latestEncounter.created_at)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Patient Timeline with Trends */}
      <PatientTimeline patientId={patientId} />

      {/* Encounter List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Historial de Encuentros
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {encounters.map((enc, i) => (
            <div
              key={enc.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                selectedEncounter === enc.id
                  ? "border-primary bg-primary/5"
                  : "hover:border-primary/50"
              }`}
              onClick={() => setSelectedEncounter(selectedEncounter === enc.id ? null : enc.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      enc.status === "FINALIZED" ? "bg-green-400" :
                      enc.status === "ANALYZED" ? "bg-blue-400" :
                      "bg-yellow-400"
                    }`} />
                    <span className="text-sm font-medium">
                      Encuentro #{i + 1}
                    </span>
                  </div>
                  <span className="text-sm text-muted-foreground">{formatDate(enc.created_at)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-1 rounded-full bg-muted">
                    {enc.status}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              {enc.reason_for_visit && (
                <p className="text-sm text-muted-foreground mt-2">{enc.reason_for_visit}</p>
              )}

              {selectedEncounter === enc.id && enc.phenotype_result && (
                <div className="mt-4 pt-4 border-t grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(enc.phenotype_result).map(([name, result]: [string, AdjudicationResult]) => (
                    <div key={name} className="flex items-start gap-2 text-sm">
                      <Activity className="h-3 w-3 text-primary mt-0.5 shrink-0" />
                      <div>
                        <span className="font-medium">{name.replace("Motor", "")}:</span>
                        <span className="text-muted-foreground ml-1">
                          {result.calculated_value || result.clinical_profile || result.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={() => router.push(`/consulta/${patientId}`)}>
          <Stethoscope className="h-4 w-4 mr-2" />
          Nueva consulta
        </Button>
        <Button variant="outline" onClick={() => router.push("/pacientes")}>
          Volver a pacientes
        </Button>
      </div>
    </div>
  )
}
