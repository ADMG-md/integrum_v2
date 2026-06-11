"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DataReadinessReport } from "@/types"
import {
  ListChecks, CheckCircle, AlertTriangle, FlaskRound,
  ChevronDown, ChevronUp,
} from "lucide-react"

interface DataReadinessBannerProps {
  readiness: DataReadinessReport
}

const tierColor = (tier: string) => {
  if (tier === "Básica") return "text-amber-400"
  if (tier === "Estándar") return "text-blue-400"
  if (tier === "Completa") return "text-green-400"
  return "text-emerald-400"
}

export default function DataReadinessBanner({ readiness }: DataReadinessBannerProps) {
  const [showBlocked, setShowBlocked] = useState(false)
  const pct = Math.round(readiness.feasibility_score * 100)

  return (
    <Card className="border-blue-500/30 bg-blue-500/5">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ListChecks className="h-5 w-5 text-blue-400" />
            <span className="text-blue-300 text-base">
              {readiness.ready_count}/{readiness.total_motors} motores evaluables ({pct}%) · Tier:{" "}
              <span className={tierColor(readiness.tier)}>{readiness.tier}</span>
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowBlocked(!showBlocked)}
            className="text-blue-300 text-xs"
          >
            {showBlocked ? <ChevronUp className="h-4 w-4 mr-1" /> : <ChevronDown className="h-4 w-4 mr-1" />}
            {showBlocked ? "Ocultar" : "Ver"} {readiness.blocked_count} con datos insuficientes
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-1.5 text-green-400">
            <CheckCircle className="h-4 w-4" />
            <span>{readiness.ready_count} alta confianza</span>
          </div>
          {readiness.quickwin_count > 0 && (
            <div className="flex items-center gap-1.5 text-yellow-400">
              <FlaskRound className="h-4 w-4" />
              <span>{readiness.quickwin_count} desbloqueables con 1 lab</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <AlertTriangle className="h-4 w-4" />
            <span>{readiness.blocked_count} sin datos suficientes</span>
          </div>
        </div>

        {readiness.priority_labs.length > 0 && (
          <div className="border-t border-blue-500/20 pt-3">
            <p className="text-xs font-semibold text-blue-300 mb-2">
              Ordenar estos labs para desbloquear motores adicionales:
            </p>
            <div className="flex flex-wrap gap-2">
              {readiness.priority_labs.slice(0, 6).map((lab) => (
                <div
                  key={lab.code}
                  className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/30 rounded-full text-xs"
                >
                  <FlaskRound className="h-3 w-3 text-yellow-400 shrink-0" />
                  <span className="text-yellow-200">{lab.name}</span>
                  <span className="text-yellow-500 font-mono">×{lab.unlocks}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {showBlocked && readiness.blocked_count > 0 && (
          <div className="border-t border-blue-500/20 pt-3">
            <p className="text-xs font-semibold text-muted-foreground mb-2">
              Motores con datos insuficientes:
            </p>
            <div className="flex flex-wrap gap-1">
              {readiness.blocked_motors?.map((b) => (
                <span
                  key={b.motor}
                  className="text-xs px-2 py-1 bg-muted rounded text-muted-foreground"
                >
                  {b.motor.replace("Motor", "")}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
