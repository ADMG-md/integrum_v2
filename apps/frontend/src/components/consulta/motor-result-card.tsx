import { AdjudicationResult } from "@/types"

interface MotorResultCardProps {
  name: string
  result: AdjudicationResult
  isExpanded: boolean
  onToggle: () => void
  onOverride?: (engineName: string, currentValue: string) => void
  isOverridden?: boolean
}

const statusBadge = (estado?: string) => {
  if (!estado) return "bg-muted text-muted-foreground"
  if (estado.includes("CONFIRMED")) return "bg-red-500/20 text-red-400"
  if (estado.includes("WARNING")) return "bg-yellow-500/20 text-yellow-400"
  if (estado.includes("ERROR")) return "bg-red-500/20 text-red-400"
  if (estado.includes("LOCKED")) return "bg-blue-500/20 text-blue-400"
  return "bg-muted text-muted-foreground"
}

export default function MotorResultCard({ name, result, isExpanded, onToggle, onOverride, isOverridden }: MotorResultCardProps) {
  const displayName = name.replace("Motor", "").replace("Engine", "")

  return (
    <div className="border rounded-md overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-3 hover:bg-accent/50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">{displayName}</span>
          {isOverridden && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-green-500/20 text-green-400">
              Override
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {onOverride && !isOverridden && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onOverride(name, result.calculated_value)
              }}
              className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 transition-colors"
            >
              Override
            </button>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadge(result.estado_ui)}`}>
            {result.estado_ui?.replace("_", " ") || "N/A"}
          </span>
          <span className="text-xs text-muted-foreground">
            {Math.round(result.confidence * 100)}%
          </span>
        </div>
      </button>
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2 border-t bg-muted/30">
          <p className="text-sm mt-2 font-medium">{result.calculated_value}</p>
          {isOverridden && (
            <p className="text-xs text-green-400 mt-1">✓ Valor sobrescrito por médico</p>
          )}
          {result.explanation && (
            <p className="text-xs text-muted-foreground">{result.explanation}</p>
          )}
          {result.evidence && result.evidence.length > 0 && (
            <div className="space-y-1 mt-2">
              <p className="text-xs font-medium text-muted-foreground">Evidencia:</p>
              {result.evidence.slice(0, 5).map((ev, i) => (
                <p key={i} className="text-xs text-muted-foreground">
                  • {ev.display || ev.code}: {String(ev.value)}{" "}
                  {ev.threshold ? `(umbral: ${ev.threshold})` : ""}
                </p>
              ))}
            </div>
          )}
          {result.action_checklist && result.action_checklist.length > 0 && (
            <div className="space-y-1 mt-2">
              <p className="text-xs font-medium text-amber-400">Acciones recomendadas:</p>
              {result.action_checklist.map((action, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className={`mt-0.5 ${
                    action.priority === 'high' ? 'text-red-400' : 
                    action.priority === 'medium' ? 'text-yellow-400' : 
                    'text-blue-400'
                  }`}>
                    {action.priority === 'high' ? '🔴' : action.priority === 'medium' ? '🟡' : '🔵'}
                  </span>
                  <div>
                    <p className="font-medium">{action.task}</p>
                    <p className="text-muted-foreground">{action.rationale}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
