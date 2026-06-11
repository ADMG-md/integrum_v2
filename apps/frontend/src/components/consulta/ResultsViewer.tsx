"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label, Textarea } from "@/components/ui/form"
import { AdjudicationResult, DataReadinessReport, AdjudicationLogRead, ReasonCode, AdjudicationOverridePayload } from "@/types"
import type { MotorGroup } from "./results-viewer-metadata"
import { api } from "@/lib/api"
import {
  AlertTriangle, CheckCircle, Loader2, FileText, ClipboardList, X, Save,
  Utensils, Pill,
} from "lucide-react"

import MotorResultCard from "./motor-result-card"
import DrugInteractionPanel from "./drug-interaction-panel"
import DeltaPanel from "./delta-panel"
import DataReadinessBanner from "./data-readiness-banner"

// New modular components
import { MOTOR_GROUPS, useMotorGroups } from "./results-viewer-metadata"
import { SoapNote } from "./results-soap-note"
import { ResultsSummaryCards } from "./results-summary-cards"
import { PatientActionPlan } from "./patient-action-plan"
import { CoreDecisionsPanel } from "./core-decisions-panel"
import { toast } from "sonner"

interface ResultsViewerProps {
  encounterId: string
  results: Record<string, AdjudicationResult>
  dataReadiness?: DataReadinessReport | null
  baselineResults?: Record<string, AdjudicationResult> | null
  baselineDate?: string | null
  onFinalize: () => void
  onBack: () => void
}

export default function ResultsViewer({
  encounterId, results, dataReadiness, baselineResults, baselineDate, onFinalize, onBack
}: ResultsViewerProps) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("core")
  const [finalizing, setFinalizing] = useState(false)
  const [notes, setNotes] = useState("")
  const [plan, setPlan] = useState("")
  const [adjudicationLogs, setAdjudicationLogs] = useState<AdjudicationLogRead[]>([])
  const [overrideModal, setOverrideModal] = useState<{
    open: boolean
    logId?: string
    engineName?: string
    currentValue?: string
  }>({ open: false })
  const [overrideValue, setOverrideValue] = useState("")
  const [overrideReason, setOverrideReason] = useState<ReasonCode>(ReasonCode.OVERRIDE_CLINICAL_INTUITION)
  const [overrideText, setOverrideText] = useState("")
  const [overrideLoading, setOverrideLoading] = useState(false)

  // Dynamic motor groups from API
  const { groups: dynamicGroups, loading: groupsLoading, error: groupsError } = useMotorGroups()
  const motorGroups: MotorGroup[] = dynamicGroups.length > 0 ? dynamicGroups : MOTOR_GROUPS as MotorGroup[]

  useEffect(() => {
    if (encounterId) {
      api.get<AdjudicationLogRead[]>(`/audit/logs/${encounterId}`)
        .then(setAdjudicationLogs)
        .catch(() => setAdjudicationLogs([]))
    }
  }, [encounterId])

  const getLogIdForMotor = (engineName: string): string | undefined => {
    const log = adjudicationLogs.find(l => l.engine_name === engineName && !l.is_overridden)
    return log?.id
  }

  const handleOpenOverride = (engineName: string, currentValue: string) => {
    const logId = getLogIdForMotor(engineName)
    if (!logId) return
    setOverrideModal({ open: true, logId, engineName, currentValue })
    setOverrideValue(currentValue)
    setOverrideReason(ReasonCode.OVERRIDE_CLINICAL_INTUITION)
    setOverrideText("")
  }

  const handleSubmitOverride = async () => {
    if (!overrideModal.logId) return
    setOverrideLoading(true)
    try {
      const payload: AdjudicationOverridePayload = {
        log_id: overrideModal.logId,
        physician_value: overrideValue,
        override_reason_code: overrideReason,
        override_reason_text: overrideText || undefined,
      }
      await api.post("/audit/override", payload)
      setOverrideModal({ open: false })
      const updated = await api.get<AdjudicationLogRead[]>(`/audit/logs/${encounterId}`)
      setAdjudicationLogs(updated)
      toast.success("Decisión médica registrada con éxito")
    } catch {
      toast.error("Error al aplicar la decisión médica")
    } finally {
      setOverrideLoading(false)
    }
  }

  const motors = Object.entries(results)
  const phenotype = results["AcostaPhenotypeMotor"]
  const eoss = results["EOSSStagingMotor"]
  const bioAge = results["BiologicalAgeMotor"]
  const drugInteraction = results["DrugInteractionMotor"]

  const criticalOmissions = motors
    .filter(([, r]) => r.critical_omissions && r.critical_omissions.length > 0)
    .flatMap(([name, r]) =>
      r.critical_omissions!.map((o) => ({ motor: name, ...o })),
    )

  const coreDecisionsResult = results["CoreClinicalDecisionEngine"]
  const coreRecommendations = (coreDecisionsResult?.metadata?.recommendations as any[]) || []

  const alertCounts: Record<string, number> = {}
  for (const group of motorGroups) {
    alertCounts[group.key] = group.motors.filter((name: string) => {
      const r = results[name]
      return r && r.estado_ui && r.estado_ui.includes("CONFIRMED")
    }).length
  }

  const totalCritical = Object.values(alertCounts).reduce((a, b) => a + b, 0)
  const activeGroup = motorGroups.find((g: typeof motorGroups[0]) => g.key === activeTab)
  const activeMotors = motors.filter(([name]) => activeGroup?.motors.includes(name as string))

  const handleFinalize = async () => {
    setFinalizing(true)
    try {
      await api.post(`/encounters/${encounterId}/finalize`, {
        clinical_notes: notes || null,
        plan_of_action: plan ? { summary: plan } : null,
      })
      toast.success("Encuentro finalizado con éxito")
      onFinalize()
    } catch {
      toast.error("Error al finalizar el encuentro")
    } finally {
      setFinalizing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Resultados del Análisis</h2>
          <p className="text-muted-foreground">{motors.length} motores ejecutados</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {totalCritical > 0 && (
            <div className="flex items-center gap-1 px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg text-sm font-medium">
              <AlertTriangle className="h-4 w-4" />
              {totalCritical} alerta{totalCritical > 1 ? "s" : ""}
            </div>
          )}
          <PatientActionPlan results={results} />
          {/* Export Buttons */}
          <Button variant="outline" size="sm" onClick={() => window.open(`/api/v1/export/csv/${encounterId}`, '_blank')}>
            <FileText className="h-4 w-4 mr-2" />
            Exportar CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.open(`/api/v1/fhir/encounter/${encounterId}/$export`, '_blank')}>
            <FileText className="h-4 w-4 mr-2" />
            Exportar FHIR
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.open(`/api/v1/export/anonymized/${encounterId}`, '_blank')}>
            <FileText className="h-4 w-4 mr-2" />
            Exportar JSON (Anon)
          </Button>
          <Button variant="outline" onClick={onBack}>Volver al formulario</Button>
          <Button onClick={handleFinalize} disabled={finalizing}>
            {finalizing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
            Finalizar encuentro
          </Button>
        </div>
      </div>

      {/* Data Readiness Banner */}
      {dataReadiness && <DataReadinessBanner readiness={dataReadiness} />}

      {/* Delta Panel */}
      {baselineResults && (
        <DeltaPanel
          baselineResults={baselineResults}
          currentResults={results}
          baselineDate={baselineDate}
        />
      )}

      {/* Summary Cards */}
      <ResultsSummaryCards 
        phenotype={phenotype} 
        eoss={eoss} 
        bioAge={bioAge} 
      />

      {/* Drug Interaction Panel */}
      {drugInteraction && (
        <DrugInteractionPanel result={drugInteraction} />
      )}

      {/* Critical Omissions Section */}
      {criticalOmissions.length > 0 && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Omisiones Críticas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {criticalOmissions.map((om, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-destructive/10 rounded-md">
                <span className="text-destructive mt-0.5">✕</span>
                <div>
                  <p className="text-sm font-medium">{om.clinical_rationale}</p>
                  <p className="text-xs text-muted-foreground">
                    {om.drug_class} · {om.gap_type} · Severidad: {om.severity}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Core Clinical Decisions Panel */}
      <CoreDecisionsPanel recommendations={coreRecommendations} />

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2">
        {motorGroups.map((group: typeof motorGroups[0]) => (
          <button
            key={group.key}
            onClick={() => setActiveTab(group.key)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === group.key
                ? "bg-primary/20 text-primary"
                : "bg-muted/50 text-muted-foreground hover:bg-muted"
            }`}
          >
            {group.icon}
            {group.label}
            {alertCounts[group.key] > 0 && (
              <span className="bg-red-500/20 text-red-400 text-xs px-1.5 py-0.5 rounded-full">
                {alertCounts[group.key]}
              </span>
            )}
          </button>
        ))}
      </div>

       {/* Active Group Content */}
      {activeGroup && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {activeGroup.icon}
              {activeGroup.label}
              <span className="text-sm font-normal text-muted-foreground">
                ({activeMotors.length} motores)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {activeMotors.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">Sin resultados en esta categoría</p>
            ) : (
              activeMotors.map(([name, result]) => {
                const overridden = adjudicationLogs.some(l => l.engine_name === name && l.is_overridden)
                const hasLog = adjudicationLogs.some(l => l.engine_name === name && !l.is_overridden)
                return (
                  <MotorResultCard
                    key={name}
                    name={name}
                    result={result}
                    isExpanded={expanded === name}
                    onToggle={() => setExpanded(expanded === name ? null : name)}
                    onOverride={hasLog ? handleOpenOverride : undefined}
                    isOverridden={overridden}
                  />
                )
              })
            )}
          </CardContent>
        </Card>
      )}

      {/* Auto-generated SOAP Note */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5" />
            Nota SOAP (Auto-generada)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <SoapNote results={results} />
        </CardContent>
      </Card>

      {/* Interactive Clinical Notes */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Notas Clínicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Notas de la consulta</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Observaciones clínicas..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Plan de acción</Label>
            <Textarea
              value={plan}
              onChange={(e) => setPlan(e.target.value)}
              placeholder="Plan terapéutico..."
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Override Modal */}
      {overrideModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setOverrideModal({ open: false })}>
          <div className="bg-card border rounded-lg w-full max-w-md p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold">Physician Override</h3>
              <button onClick={() => setOverrideModal({ open: false })} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-muted-foreground">
              Motor: <span className="font-medium text-foreground">{overrideModal.engineName}</span>
            </p>
            <div className="space-y-2">
              <Label>Valor calculado por el motor</Label>
              <p className="text-sm p-2 bg-muted rounded">{overrideModal.currentValue}</p>
            </div>
            <div className="space-y-2">
              <Label>Valor corregido (médico)</Label>
              <input
                value={overrideValue}
                onChange={(e) => setOverrideValue(e.target.value)}
                className="w-full p-2 text-sm border rounded bg-background"
                placeholder="Ingrese el valor corregido..."
              />
            </div>
            <div className="space-y-2">
              <Label>Razón del override</Label>
              <select
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value as ReasonCode)}
                className="w-full p-2 text-sm border rounded bg-background"
              >
                <option value={ReasonCode.OVERRIDE_CLINICAL_INTUITION}>Intuición clínica</option>
                <option value={ReasonCode.OVERRIDE_ECONOMIC_BARRIER}>Barrera económica</option>
                <option value={ReasonCode.OVERRIDE_MISSING_CONTEXT}>Contexto faltante</option>
                <option value={ReasonCode.OVERRIDE_PATIENT_REFUSAL}>Paciente rechaza</option>
                <option value={ReasonCode.BIOLOGICAL_IMPOSSIBILITY}>Imposibilidad biológica</option>
                <option value={ReasonCode.PARTIAL_AGREEMENT}>Acuerdo parcial</option>
                <option value={ReasonCode.TECHNICAL_ERROR}>Error técnico</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Notas adicionales (opcional)</Label>
              <Textarea
                value={overrideText}
                onChange={(e) => setOverrideText(e.target.value)}
                placeholder="Contexto adicional..."
                rows={2}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setOverrideModal({ open: false })}>Cancelar</Button>
              <Button onClick={handleSubmitOverride} disabled={overrideLoading || !overrideValue}>
                {overrideLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                Guardar Override
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
