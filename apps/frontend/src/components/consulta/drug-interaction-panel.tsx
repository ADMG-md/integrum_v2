"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AdjudicationResult } from "@/types"
import { AlertTriangle, XCircle } from "lucide-react"

interface DrugInteractionPanelProps {
  result: AdjudicationResult
}

const isStringArray = (val: unknown): val is string[] =>
  Array.isArray(val) && val.every((item): item is string => typeof item === "string")

export default function DrugInteractionPanel({ result }: DrugInteractionPanelProps) {
  if (result.estado_ui?.includes("INDETERMINATE")) {
    return (
      <Card className="border-blue-500/30 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-400">
            <AlertTriangle className="h-5 w-5" />
            DrugInteraction — Base de datos limitada
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2 p-3 bg-blue-500/10 rounded-md">
            <AlertTriangle className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-300">No evaluable — cobertura limitada</p>
              <p className="text-xs text-blue-200 mt-1">
                {result.dato_faltante ||
                  "La base de datos embebida no cubre esta combinación. Consultar Lexicomp o Micromedex antes de prescribir."}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!result.metadata) return null

  return (
    <Card className="border-red-500/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-400">
          <AlertTriangle className="h-5 w-5" />
          Alertas de Interacciones Farmacológicas
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isStringArray(result.metadata.critical_alerts) && result.metadata.critical_alerts.length > 0 && (
          <div>
            <p className="text-sm font-semibold text-red-400 mb-2">Contraindicaciones Críticas</p>
            {result.metadata.critical_alerts.map((alert: string, i: number) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-red-500/10 rounded mb-1">
                <XCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                <p className="text-sm">{alert}</p>
              </div>
            ))}
          </div>
        )}
        {isStringArray(result.metadata.major_alerts) && result.metadata.major_alerts.length > 0 && (
          <div>
            <p className="text-sm font-semibold text-yellow-400 mb-2">Interacciones Mayores</p>
            {result.metadata.major_alerts.map((alert: string, i: number) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-yellow-500/10 rounded mb-1">
                <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 shrink-0" />
                <p className="text-sm">{alert}</p>
              </div>
            ))}
          </div>
        )}
        {isStringArray(result.metadata.qt_meds) && result.metadata.qt_meds.length >= 2 && (
          <div className="p-2 bg-orange-500/10 rounded">
            <p className="text-sm text-orange-400">
              ⚡ Riesgo QT prolongado: {result.metadata.qt_meds.join(", ")}
            </p>
          </div>
        )}
        {isStringArray(result.metadata.obesity_meds) && result.metadata.obesity_meds.length > 0 && (
          <div className="p-2 bg-blue-500/10 rounded">
            <p className="text-sm text-blue-400">
              💊 Medicamentos con efecto en peso: {result.metadata.obesity_meds.join("; ")}
            </p>
          </div>
        )}
        {result.action_checklist && result.action_checklist.length > 0 && (
          <div className="mt-2">
            <p className="text-sm font-semibold text-amber-400 mb-2">Acciones Recomendadas</p>
            {result.action_checklist.map((action, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-amber-500/10 rounded mb-1">
                <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium">{action.task}</p>
                  <p className="text-xs text-muted-foreground">{action.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
