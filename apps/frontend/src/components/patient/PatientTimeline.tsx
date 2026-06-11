"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import { TrendingUp, TrendingDown, Minus, Activity, Scale, Brain, Heart } from "lucide-react"

import { useQuery } from "@tanstack/react-query"

interface PatientTimelineProps {
  patientId: string
}

interface TimelineData {
  patient_id: string
  timeline: Record<string, Array<{
    date: string
    value: string
    confidence: number
    is_overridden: boolean
    physician_value?: string
  }>>
}

interface EncounterData {
  id: string
  created_at: string
  reason_for_visit?: string
  phenotype_result?: Record<string, { calculated_value: string; confidence: number }> | null
  clinical_notes?: string
}

export default function PatientTimeline({ patientId }: PatientTimelineProps) {
  const { data, isLoading: loading } = useQuery({
    queryKey: ["patientTimeline", patientId],
    queryFn: async () => {
      const [timeline, encs] = await Promise.all([
        api.get<TimelineData>(`/timeline/${patientId}`),
        api.get<EncounterData[]>(`/encounters/patient/${patientId}`)
      ])
      const encounters = Array.isArray(encs) ? encs.sort((a, b) => a.created_at.localeCompare(b.created_at)) : []
      return { timelineData: timeline, encounters }
    },
    enabled: !!patientId,
  })

  const timelineData = data?.timelineData || null
  const encounters = data?.encounters || []

  if (loading) return <p className="text-muted-foreground text-sm">Cargando historial...</p>
  if (!timelineData && encounters.length === 0) return <p className="text-muted-foreground text-sm">Sin datos previos.</p>

  const getMotorTrend = (engineName: string): { date: string; value: number }[] => {
    const motorData = timelineData?.timeline?.[engineName]
    if (!motorData || motorData.length === 0) return []
    return motorData.map(d => ({
      date: d.date,
      value: parseFloat(d.value) || 0,
    }))
  }

  const phenotypeTrend = getMotorTrend("AcostaPhenotypeMotor")
  const bioAgeTrend = getMotorTrend("BiologicalAgeMotor")
  const eossTrend = getMotorTrend("EOSSStagingMotor")

  const TrendChart = ({ title, icon, data, unit, color }: {
    title: string
    icon: React.ReactNode
    data: { date: string; value: number }[]
    unit: string
    color: string
  }) => {
    if (data.length < 2) return null
    const trend = data[data.length - 1].value - data[0].value
    const TrendIcon = trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus
    const trendColor = title.includes("PHQ") || title.includes("Edad")
      ? (trend > 0 ? "text-red-400" : "text-green-400")
      : (trend > 0 ? "text-red-400" : "text-green-400")

    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            {icon}
            {title}
            <span className={`ml-auto text-xs ${trendColor} flex items-center gap-1`}>
              <TrendIcon className="h-3 w-3" />
              {trend > 0 ? "+" : ""}{trend.toFixed(1)} {unit}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-1 h-20">
            {data.map((d, i) => {
              const max = Math.max(...data.map(x => x.value))
              const min = Math.min(...data.map(x => x.value))
              const range = max - min || 1
              const height = ((d.value - min) / range) * 100
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-muted-foreground">{d.value.toFixed(1)}</span>
                  <div
                    className={`w-full rounded-t ${color}`}
                    style={{ height: `${Math.max(height, 10)}%` }}
                  />
                  <span className="text-xs text-muted-foreground truncate w-full text-center">
                    {new Date(d.date).toLocaleDateString("es-CO", { day: "2-digit", month: "short" })}
                  </span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Historial del Paciente ({encounters.length} encuentros)</h3>

      {/* Trend Charts from Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <TrendChart title="Fenotipo (numérico)" icon={<Scale className="h-4 w-4" />} data={phenotypeTrend} unit="" color="bg-blue-500/30" />
        <TrendChart title="Edad Biológica" icon={<Activity className="h-4 w-4" />} data={bioAgeTrend} unit="años" color="bg-purple-500/30" />
        <TrendChart title="Estadio EOSS" icon={<Heart className="h-4 w-4" />} data={eossTrend} unit="" color="bg-yellow-500/30" />
      </div>

      {/* Encounter List */}
      <div className="space-y-2">
        {encounters.slice().reverse().map((enc) => (
          <Card key={enc.id} className="border-muted">
            <CardContent className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    {new Date(enc.created_at).toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" })}
                  </p>
                  {enc.reason_for_visit && (
                    <p className="text-xs text-muted-foreground">{enc.reason_for_visit}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  {enc.phenotype_result?.["AcostaPhenotypeMotor"] && (
                    <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                      {enc.phenotype_result["AcostaPhenotypeMotor"].calculated_value}
                    </span>
                  )}
                  {enc.phenotype_result?.["EOSSStagingMotor"] && (
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
                      {enc.phenotype_result["EOSSStagingMotor"].calculated_value}
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
