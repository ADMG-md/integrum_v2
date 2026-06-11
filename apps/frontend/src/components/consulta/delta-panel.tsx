"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AdjudicationResult } from "@/types"
import {
  Activity, ChevronDown, ChevronUp,
  ArrowUp, ArrowDown, ArrowRight, Minus,
} from "lucide-react"

interface DeltaPanelProps {
  baselineResults: Record<string, AdjudicationResult>
  currentResults: Record<string, AdjudicationResult>
  baselineDate: string | null | undefined
}

export default function DeltaPanel({
  baselineResults,
  currentResults,
  baselineDate,
}: DeltaPanelProps) {
  const [expanded, setExpanded] = useState(false)

  const deltas = Object.entries(currentResults)
    .filter(([name]) => baselineResults[name] !== undefined)
    .map(([name, current]) => {
      const prev = baselineResults[name]
      const currentVal = current.calculated_value || ""
      const prevVal = prev.calculated_value || ""
      const currentState = current.estado_ui || "INDETERMINATE_LOCKED"
      const prevState = prev.estado_ui || "INDETERMINATE_LOCKED"

      const stateChanged =
        (prevState.includes("CONFIRMED") && !currentState.includes("CONFIRMED")) ||
        (!prevState.includes("CONFIRMED") && currentState.includes("CONFIRMED")) ||
        (prevState.includes("WARNING") && !currentState.includes("WARNING") && !currentState.includes("CONFIRMED")) ||
        (!prevState.includes("WARNING") && !prevState.includes("CONFIRMED") && currentState.includes("WARNING"))

      return {
        name,
        prevVal,
        currentVal,
        prevState,
        currentState,
        prevConfidence: prev.confidence || 0,
        currentConfidence: current.confidence || 0,
        stateChanged,
      }
    })
    .filter((d) => d.prevVal !== d.currentVal || d.stateChanged)

  if (deltas.length === 0) {
    return (
      <Card className="border-muted/50">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-5 w-5 text-primary" />
            Comparación con consulta anterior
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            {baselineDate
              ? `Sin cambios significativos`
              : "No hay consulta anterior para comparar"}
          </p>
        </CardContent>
      </Card>
    )
  }

  const improved = deltas.filter((d) => {
    const worse = d.prevState.includes("CONFIRMED") && !d.currentState.includes("CONFIRMED")
    const betterWarning = !d.prevState.includes("WARNING") && d.currentState.includes("WARNING") && !d.currentState.includes("CONFIRMED")
    return worse || betterWarning
  })
  const worsened = deltas.filter((d) => {
    const better = !d.prevState.includes("CONFIRMED") && d.currentState.includes("CONFIRMED")
    const worseWarning = d.prevState.includes("WARNING") && !d.currentState.includes("WARNING") && !d.currentState.includes("CONFIRMED")
    return better || worseWarning
  })
  const neutral = deltas.filter((d) => !d.stateChanged && d.prevVal !== d.currentVal)

  const stateBadge = (state?: string) => {
    if (!state) return "bg-muted text-muted-foreground"
    if (state.includes("CONFIRMED")) return "bg-red-500/20 text-red-400"
    if (state.includes("WARNING")) return "bg-yellow-500/20 text-yellow-400"
    return "bg-muted text-muted-foreground"
  }

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-base">
            <Activity className="h-5 w-5 text-primary" />
            Comparación con consulta anterior
            {baselineDate && (
              <span className="text-xs text-muted-foreground font-normal">
                vs {new Date(baselineDate).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" })}
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-xs"
          >
            {expanded ? "Colapsar" : `Ver ${deltas.length} cambio(s)`}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-4 text-sm">
          {worsened.length > 0 && (
            <div className="flex items-center gap-1.5 text-red-400">
              <ArrowUp className="h-4 w-4" />
              <span>{worsened.length} empeoró</span>
            </div>
          )}
          {improved.length > 0 && (
            <div className="flex items-center gap-1.5 text-green-400">
              <ArrowDown className="h-4 w-4" />
              <span>{improved.length} mejoró</span>
            </div>
          )}
          {neutral.length > 0 && (
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Minus className="h-4 w-4" />
              <span>{neutral.length} cambió (sin cambio de estado)</span>
            </div>
          )}
        </div>

        {expanded && (
          <div className="border-t border-primary/20 pt-3 space-y-2">
            {deltas.map((d) => (
              <div key={d.name} className="flex items-start gap-3 text-sm">
                <div className="mt-0.5">
                  {d.stateChanged && d.currentState.includes("CONFIRMED") ? (
                    <ArrowUp className="h-4 w-4 text-red-400" />
                  ) : d.stateChanged && d.currentState.includes("WARNING") ? (
                    <ArrowUp className="h-4 w-4 text-yellow-400" />
                  ) : d.stateChanged && !d.currentState.includes("CONFIRMED") && !d.currentState.includes("WARNING") ? (
                    <ArrowDown className="h-4 w-4 text-green-400" />
                  ) : (
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-xs truncate">
                      {d.name.replace("Motor", "").replace("Engine", "")}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full shrink-0 ${stateBadge(d.prevState)}`}>
                      {d.prevState.replace("_", " ")}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span className={`text-xs px-1.5 py-0.5 rounded-full shrink-0 ${stateBadge(d.currentState)}`}>
                      {d.currentState.replace("_", " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground line-through">
                      {d.prevVal}
                    </span>
                    <span className="text-xs text-muted-foreground">→</span>
                    <span className="text-xs font-medium">{d.currentVal}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
