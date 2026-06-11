"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/form"
import { api } from "@/lib/api"
import { Brain, Loader2, CheckCircle, ChevronRight } from "lucide-react"

interface Questionnaire {
  id: string
  name: string
  fullName: string
  description: string
  maxScore: number
  severityLabels: string[]
  severityColors: string[]
  options: string[]
  specialItem?: { index: number; label: string; range: [number, number] }
  questions: string[]
}

export default function PsicologiaPage() {
  const params = useParams()
  const patientId = params.patientId as string
  const [selected, setSelected] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState<Record<string, { score: number; max: number }>>({})
  const [questionnaires, setQuestionnaires] = useState<Questionnaire[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Questionnaire[]>("/metadata/questionnaires")
      .then(setQuestionnaires)
      .catch(() => setQuestionnaires([]))
      .finally(() => setLoading(false))
  }, [])

  const current = questionnaires.find((q) => q.id === selected)

  const handleAnswer = (questionIdx: number, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionIdx]: value }))
  }

  const handleSubmit = async () => {
    if (!current) return
    setSubmitting(true)
    try {
      const score = Object.values(answers).reduce((a, b) => a + b, 0)
      const responses: Record<string, number> = {}
      current.questions.forEach((q, i) => { responses[`q${i + 1}`] = answers[i] || 0 })

      const fieldMap: Record<string, string> = {
        phq9: "phq9_score",
        gad7: "gad7_score",
        tfq: "tfq_uncontrolled",
        atenas: "atenas_score",
        fnq: "fnq_intrusive",
      }

      const backendField = fieldMap[current.id] || `${current.id}_score`

      let psychometrics: Record<string, number> = {}
      if (current.id === "tfq") {
        psychometrics = {
          tfq_uncontrolled: answers[0] || 0,
          tfq_cognitive: answers[1] || 0,
          tfq_emotional: answers[2] || 0,
        }
      } else if (current.id === "atenas") {
        psychometrics["atenas_score"] = score
      } else if (current.id === "fnq") {
        psychometrics["fnq_intrusive"] = answers[0] || 0
        psychometrics["fnq_control"] = answers[3] || 0
      } else {
        psychometrics[backendField] = score
      }

      await api.post("/encounters/process", {
        patient_id: patientId,
        reason_for_visit: `Evaluación psicológica - ${current.name}`,
        psychometrics,
        observations: [],
        conditions: [],
        medications: [],
        history: {},
        metabolic: {},
        lifestyle: {},
      })

      setSubmitted((prev) => ({ ...prev, [current.id]: { score, max: current.maxScore } }))
      setAnswers({})
      setSelected(null)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido"
      alert(`Error guardando evaluación: ${message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const getSeverity = (score: number, max: number, currentQ: Questionnaire) => {
    if (!currentQ) return { label: "", color: "" }
    const labels = currentQ.severityLabels ?? []
    const colors = currentQ.severityColors ?? []
    if (!labels.length || !colors.length || max <= 0) return { label: "", color: "" }
    const ratio = score / max
    const thresholds = [0.25, 0.5, 0.75]
    let idx = thresholds.length // default: last bucket
    for (let i = 0; i < thresholds.length; i++) {
      if (ratio <= thresholds[i]) { idx = i; break }
    }
    return {
      label: labels[Math.min(idx, labels.length - 1)],
      color: colors[Math.min(idx, colors.length - 1)],
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Evaluación Psicológica</h2>
        <p className="text-muted-foreground">Cuestionarios psicométricos validados con preguntas completas</p>
      </div>

      {/* Questionnaire cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {questionnaires.map((q) => {
          const isDone = submitted[q.id]
          return (
            <Card key={q.id} className={isDone ? "border-green-500/30" : ""}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Brain className="h-4 w-4 text-primary" />
                  {q.name}
                  {isDone && <CheckCircle className="h-4 w-4 text-green-400 ml-auto" />}
                </CardTitle>
                <CardDescription>{q.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">{q.questions.length} preguntas · Puntaje máx: {q.maxScore}</p>
                {isDone && (
                  <div className="text-sm">
                    <span className="font-medium">Puntaje: {isDone.score}/{isDone.max}</span>
                    <span className={`ml-2 ${(getSeverity(isDone.score, isDone.max, q)).color}`}>
                      {(getSeverity(isDone.score, isDone.max, q)).label}
                    </span>
                  </div>
                )}
                <Button
                  size="sm"
                  className="w-full"
                  variant={isDone ? "outline" : "default"}
                  onClick={() => { setSelected(q.id); setAnswers({}) }}
                >
                  {isDone ? "Re-evaluar" : "Aplicar cuestionario"}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Active questionnaire */}
      {current && selected && (
        <Card className="border-primary/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{current.fullName}</CardTitle>
                <CardDescription>{current.description}</CardDescription>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{Object.values(answers).reduce((a, b) => a + b, 0)}/{current.maxScore}</p>
                {Object.keys(answers).length === current.questions.length && (
                  <p className={`text-sm ${(getSeverity(Object.values(answers).reduce((a, b) => a + b, 0), current.maxScore, current)).color}`}>
                    {(getSeverity(Object.values(answers).reduce((a, b) => a + b, 0), current.maxScore, current)).label}
                  </p>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {current.questions.map((q, i) => {
              const isSpecial = current.specialItem?.index === i
              if (isSpecial && current.specialItem) {
                return (
                  <div key={i} className="space-y-3 p-4 rounded-lg bg-muted/30">
                    <p className="text-sm font-medium">{current.specialItem.label}</p>
                    <div className="flex flex-wrap gap-2">
                      {Array.from({ length: current.specialItem.range[1] - current.specialItem.range[0] + 1 }, (_, j) => j + current.specialItem!.range[0]).map((val) => (
                        <button
                          key={val}
                          onClick={() => handleAnswer(i, val)}
                          className={`w-10 h-10 rounded-md text-sm font-medium transition-colors ${
                            answers[i] === val
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted hover:bg-accent text-muted-foreground"
                          }`}
                        >
                          {val}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              }
              return (
                <div key={i} className="space-y-3 p-4 rounded-lg bg-muted/30">
                  <p className="text-sm font-medium">
                    <span className="text-muted-foreground mr-2">{i + 1}.</span>
                    {q}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {current.options.map((opt, j) => (
                      <button
                        key={j}
                        onClick={() => handleAnswer(i, j + 1)}
                        className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                          answers[i] === j + 1
                            ? "bg-primary text-primary-foreground font-medium"
                            : "bg-muted hover:bg-accent text-muted-foreground"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}

            <div className="flex items-center justify-between pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                {Object.keys(answers).length}/{current.questions.length} respondidas
              </p>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setSelected(null)}>
                  Volver a cuestionarios
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={submitting || Object.keys(answers).length < current.questions.length}
                >
                  {submitting ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Guardando...</>
                  ) : (
                    <><CheckCircle className="h-4 w-4 mr-2" />Guardar evaluación</>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
