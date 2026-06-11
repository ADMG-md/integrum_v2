"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ClinicalRecommendation } from "@/types"
import { ShieldAlert, CheckCircle2, AlertTriangle, Info, Pill, Utensils, BrainCircuit, Activity } from "lucide-react"

interface CoreDecisionsPanelProps {
  recommendations: ClinicalRecommendation[]
}

const getDomainIcon = (domain: string) => {
  switch (domain) {
    case "nutrition":
    case "protein":
      return <Utensils className="h-5 w-5" />
    case "behavioral":
    case "sleep":
      return <BrainCircuit className="h-5 w-5" />
    case "pharmacotherapy":
      return <Pill className="h-5 w-5" />
    case "risk":
      return <Activity className="h-5 w-5" />
    default:
      return <Info className="h-5 w-5" />
  }
}

const getStatusStyles = (status: string, priority: string) => {
  if (status === "suppressed") {
    return "bg-slate-50 border-slate-300 dark:bg-slate-900/50 dark:border-slate-700"
  }
  if (status === "modified") {
    return "bg-amber-500/10 border-amber-500/30"
  }
  if (priority === "critical") {
    return "bg-red-500/10 border-red-500/30"
  }
  if (priority === "high") {
    return "bg-orange-500/10 border-orange-500/30"
  }
  return "bg-green-500/10 border-green-500/30"
}

export function CoreDecisionsPanel({ recommendations }: CoreDecisionsPanelProps) {
  if (!recommendations || recommendations.length === 0) return null

  return (
    <Card className="border-primary/20 shadow-md">
      <CardHeader className="bg-primary/5 pb-4">
        <CardTitle className="flex items-center gap-2 text-primary">
          <ShieldAlert className="h-6 w-6" />
          Decisiones Clínicas Nucleares (CDS)
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6 grid gap-4 sm:grid-cols-1 md:grid-cols-2">
        {recommendations.map((rec, i) => (
          <div
            key={i}
            className={`flex flex-col p-4 rounded-xl border ${getStatusStyles(rec.status, rec.priority)} transition-all`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-background/50">
                  {getDomainIcon(rec.domain)}
                </span>
                <h4 className="font-bold text-sm tracking-tight">
                  {rec.recommendation_code.replace(/_/g, " ")}
                </h4>
              </div>
              <div className="flex flex-col items-end gap-1">
                {rec.status === "suppressed" && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300 uppercase flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" /> Abstención Explícita
                  </span>
                )}
                {rec.status === "modified" && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-600 uppercase flex items-center gap-1">
                    <Info className="h-3 w-3" /> Modificada
                  </span>
                )}
                {rec.status === "active" && rec.priority === "critical" && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-600 uppercase">
                    Crítica
                  </span>
                )}
                {rec.status === "active" && rec.priority === "high" && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-600 uppercase">
                    Alta Prioridad
                  </span>
                )}
              </div>
            </div>

            <p className={`text-sm mt-1 leading-relaxed ${rec.status === "suppressed" ? "text-muted-foreground" : ""}`}>
              {rec.human_readable_basis}
            </p>

            {/* Structured Basis (Triggers & Dependencies) */}
            {(rec.trigger_summary?.length > 0 || rec.depends_on?.length > 0) && (
              <div className="mt-3 bg-muted/30 p-2.5 rounded-md border border-muted/50">
                <p className="text-[10px] uppercase font-bold text-muted-foreground mb-2 flex items-center gap-1.5">
                  <Activity className="h-3 w-3" /> Base Estructurada
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {rec.depends_on?.map((dep, idx) => (
                    <span key={`dep-${idx}`} className="text-[10px] font-medium bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded">
                      {dep}
                    </span>
                  ))}
                  {rec.trigger_summary?.map((trigger, idx) => (
                    <span key={`trig-${idx}`} className="text-[10px] font-medium bg-background border px-2 py-0.5 rounded text-muted-foreground">
                      {trigger}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {rec.status === "suppressed" && rec.suppression_reason && (
              <div className="mt-3 p-3 bg-slate-100 dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700">
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Motivo de Abstención
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  {rec.suppression_reason}
                </p>
              </div>
            )}

            {rec.status === "modified" && rec.superseded_by && (
              <div className="mt-3 p-3 bg-amber-500/10 rounded-md border border-amber-500/20">
                <p className="text-xs font-bold text-amber-700 dark:text-amber-500 flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5" />
                  Modificada por Restricción Clínica
                </p>
                <p className="text-xs text-amber-600/90 dark:text-amber-400/90 mt-1">
                  <span className="font-semibold block mb-0.5">Reemplaza a: <span className="font-mono bg-amber-500/20 px-1 rounded">{rec.superseded_by}</span></span>
                  <span className="block mt-1">{rec.suppression_reason}</span>
                </p>
              </div>
            )}
            
            <div className="mt-auto pt-3 flex items-center justify-between">
               <span className="text-[10px] font-mono text-muted-foreground/60">{rec.requirement_id}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
