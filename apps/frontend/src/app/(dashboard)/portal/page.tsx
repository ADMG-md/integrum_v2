"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { AdjudicationResult } from "@/types"
import { Activity, Brain, Heart, Pill, Scale, TrendingUp, Loader2 } from "lucide-react"

import { useQuery } from "@tanstack/react-query"

interface PortalData {
  phenotype?: string
  bioAge?: string
  eoss?: string
  lastVisit?: string
}

export default function PortalPage() {
  const [patientId, setPatientId] = useState<string | null>(null)

  useEffect(() => {
    setPatientId(localStorage.getItem("patient_id"))
  }, [])

  const { data, isLoading: loading } = useQuery({
    queryKey: ["portalData", patientId],
    queryFn: async () => {
      if (!patientId) return null
      const encounters = await api.get<Array<{ phenotype_result: Record<string, AdjudicationResult> | null; created_at: string }>>(
        `/encounters/patient/${patientId}`
      )
      if (Array.isArray(encounters) && encounters.length > 0) {
        const latest = encounters[encounters.length - 1]
        const results = latest.phenotype_result || {}
        return {
          phenotype: results["AcostaPhenotypeMotor"]?.calculated_value,
          bioAge: results["BiologicalAgeMotor"]?.calculated_value,
          eoss: results["EOSSStagingMotor"]?.calculated_value,
          lastVisit: latest.created_at,
        } as PortalData
      }
      return null
    },
    enabled: !!patientId,
  })

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Mi Portal de Salud</h2>
        <p className="text-muted-foreground">Tu información de salud personalizada</p>
      </div>

      {!patientId && (
        <Card className="border-amber-500/50 bg-amber-500/10">
          <CardContent className="py-4">
            <p className="text-amber-400">
              No se encontró información de paciente vinculada a tu cuenta. Contacta a tu médico.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className={data?.phenotype ? "border-green-500/50" : "border-primary/50"}>
          <CardHeader>
            <CardTitle>Tu Fenotipo de Obesidad</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.phenotype ? (
              <p className="text-2xl font-bold text-green-400">{data.phenotype}</p>
            ) : (
              <p className="text-muted-foreground">Aún no hay datos disponibles</p>
            )}
          </CardContent>
        </Card>

        <Card className={data?.bioAge ? "border-blue-500/50" : "border-primary/50"}>
          <CardHeader>
            <CardTitle>Mi Edad Biológica</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.bioAge ? (
              <p className="text-2xl font-bold text-blue-400">{data.bioAge} años</p>
            ) : (
              <p className="text-muted-foreground">Aún no hay datos disponibles</p>
            )}
          </CardContent>
        </Card>

        <Card className={data?.eoss ? "border-purple-500/50" : "border-primary/50"}>
          <CardHeader>
            <CardTitle>Estadio EOSS</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.eoss ? (
              <p className="text-2xl font-bold text-purple-400">{data.eoss}</p>
            ) : (
              <p className="text-muted-foreground">Aún no hay datos disponibles</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Última Visita</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.lastVisit ? (
              <p className="text-lg">{new Date(data.lastVisit).toLocaleDateString("es-CO")}</p>
            ) : (
              <p className="text-muted-foreground">Sin encuentros registrados</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { icon: <Scale className="h-5 w-5" />, label: "Mi Progreso", desc: "Peso, IMC y medidas", href: "/seguimiento" },
          { icon: <Brain className="h-5 w-5" />, label: "Mi Bienestar Emocional", desc: "Scores psicométricos" },
          { icon: <Pill className="h-5 w-5" />, label: "Mi Plan de Tratamiento", desc: "Medicamentos y recomendaciones" },
          { icon: <Activity className="h-5 w-5" />, label: "Próxima Cita", desc: "Agenda y recordatorios" },
        ].map((item) => (
          <Card key={item.label} className="hover:border-primary/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">{item.icon}</div>
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
