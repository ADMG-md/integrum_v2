"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/form"
import { Brain, ChevronRight, CheckCircle, AlertCircle } from "lucide-react"

interface AcostaSurveyProps {
  patientId: string
  onComplete: (scores: AcostaSurveyResults) => void
}

export interface AcostaSurveyResults {
  saciacion_alterada_score: number
  saciedad_acelerada_score: number
  hambre_hedonica_score: number
  gasto_energetico_reducido_score: number
  saciedad_temprana_score: number
}

const saciacionAlteradaQuestions = [
  { id: "sa1", text: "¿Cuántas porciones come normalmente en una comida principal?", options: [{ label: "1 porción", value: 0 }, { label: "2 porciones", value: 1 }, { label: "3 o más porciones", value: 2 }] },
  { id: "sa2", text: "¿Come hasta sentirse completamente lleno/a?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Siempre", value: 2 }] },
  { id: "sa3", text: "¿Le cuesta dejar de comer cuando empieza una comida?", options: [{ label: "No, me detengo fácilmente", value: 0 }, { label: "A veces me cuesta", value: 1 }, { label: "Sí, me cuesta mucho", value: 2 }] },
  { id: "sa4", text: "¿Come más rápido que las personas a su alrededor?", options: [{ label: "No, como normal", value: 0 }, { label: "Un poco más rápido", value: 1 }, { label: "Sí, mucho más rápido", value: 2 }] },
  { id: "sa5", text: "¿Sabe cuándo ha terminado de comer o sigue comiendo por inercia?", options: [{ label: "Generalmente sé cuándo parar", value: 0 }, { label: "A veces no me doy cuenta", value: 1 }, { label: "Casi nunca sé cuándo parar", value: 2 }] },
]

const saciedadAceleradaQuestions = [
  { id: "sac1", text: "¿Con qué frecuencia siente hambre entre comidas?", options: [{ label: "Rara vez", value: 0 }, { label: "1-2 veces al día", value: 1 }, { label: "Cada 1-2 horas", value: 2 }] },
  { id: "sac2", text: "¿Cuánto tiempo después de comer siente hambre nuevamente?", options: [{ label: "3-4 horas o más", value: 0 }, { label: "2-3 horas", value: 1 }, { label: "Menos de 2 horas", value: 2 }] },
  { id: "sac3", text: "¿Necesita hacer meriendas/snacks entre comidas para no sentir hambre?", options: [{ label: "No, aguanto bien entre comidas", value: 0 }, { label: "A veces necesito un snack", value: 1 }, { label: "Sí, siempre necesito algo", value: 2 }] },
  { id: "sac4", text: "¿Siente molestias estomacales o 'vacío' poco después de comer?", options: [{ label: "No", value: 0 }, { label: "A veces", value: 1 }, { label: "Frecuentemente", value: 2 }] },
  { id: "sac5", text: "¿Le cuesta pasar más de 3 horas sin comer?", options: [{ label: "No, puedo esperar", value: 0 }, { label: "Me cuesta un poco", value: 1 }, { label: "Sí, me cuesta mucho", value: 2 }] },
]

const hambreHedonicaQuestions = [
  { id: "hh1", text: "¿Come cuando se siente estresado/a o ansioso/a?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Casi siempre", value: 2 }] },
  { id: "hh2", text: "¿Come cuando se siente triste o deprimido/a?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Casi siempre", value: 2 }] },
  { id: "hh3", text: "¿Come cuando se siente aburrido/a?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Casi siempre", value: 2 }] },
  { id: "hh4", text: "¿Come cuando se siente solo/a?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Casi siempre", value: 2 }] },
  { id: "hh5", text: "¿Tiene antojos intensos de alimentos específicos (dulces, carbohidratos, snacks)?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Casi siempre", value: 2 }] },
  { id: "hh6", text: "¿Come más de lo planeado en eventos sociales o reuniones?", options: [{ label: "No, mantengo el control", value: 0 }, { label: "A veces como de más", value: 1 }, { label: "Sí, siempre como más", value: 2 }] },
]

const gastoEnergeticoReducidoQuestions = [
  { id: "ge1", text: "¿Cuántos minutos de actividad física hace por semana?", options: [{ label: "150+ minutos", value: 0 }, { label: "60-150 minutos", value: 1 }, { label: "Menos de 60 minutos", value: 2 }] },
  { id: "ge2", text: "¿Se siente cansado/a la mayor parte del día?", options: [{ label: "No, tengo energía", value: 0 }, { label: "A veces", value: 1 }, { label: "Sí, casi siempre", value: 2 }] },
  { id: "ge3", text: "¿Evita subir escaleras o caminar distancias cortas?", options: [{ label: "No, me muevo normalmente", value: 0 }, { label: "A veces evito", value: 1 }, { label: "Sí, siempre evito", value: 2 }] },
  { id: "ge4", text: "¿Siente que no suda ni se cansa incluso con actividad moderada?", options: [{ label: "No, sudo y me canso normal", value: 0 }, { label: "A veces me cuesta", value: 1 }, { label: "Sí, casi no sudo ni me canso", value: 2 }] },
  { id: "ge5", text: "¿Pasa más de 8 horas sentado/a al día?", options: [{ label: "No, me muevo regularmente", value: 0 }, { label: "Entre 6-8 horas", value: 1 }, { label: "Sí, más de 8 horas", value: 2 }] },
]

const saciedadTempranaQuestions = [
  { id: "st1", text: "¿Se siente lleno/a después de comer solo unas pocas cucharadas?", options: [{ label: "No, como porciones normales", value: 0 }, { label: "A veces me lleno rápido", value: 1 }, { label: "Sí, muy rápido", value: 2 }] },
  { id: "st2", text: "¿Ha perdido el apetito en las últimas semanas?", options: [{ label: "No, mi apetito es normal", value: 0 }, { label: "Un poco", value: 1 }, { label: "Sí, bastante", value: 2 }] },
  { id: "st3", text: "¿Siente náuseas o malestar estomacal después de comer?", options: [{ label: "No", value: 0 }, { label: "A veces", value: 1 }, { label: "Frecuentemente", value: 2 }] },
  { id: "st4", text: "¿Deja comida en el plato porque ya no puede más?", options: [{ label: "Rara vez", value: 0 }, { label: "A veces", value: 1 }, { label: "Frecuentemente", value: 2 }] },
]

const phenotypeInfo: Record<string, { name: string; description: string; diet: string; exercise: string }> = {
  falla_de_saciedad: {
    name: "Falla de Saciedad",
    description: "El paciente no reconoce la señal de saciedad durante la comida. Consume más calorías por comida de lo esperado para su sexo y complexión.",
    diet: "Dieta volumétrica, alta en fibra, baja en densidad calórica. 1-2 comidas/día.",
    exercise: "Actividad física regular, caminatas 150 min/semana.",
  },
  intestino_hambriento: {
    name: "Intestino Hambriento",
    description: "Vaciado gástrico acelerado. El paciente siente hambre poco tiempo después de haber completado una comida.",
    diet: "Dieta baja en calorías con suplementación proteica pre-comida. 3-5 comidas/día.",
    exercise: "Ejercicio regular, evitar largos períodos sin comer.",
  },
  hambre_emocional: {
    name: "Hambre Emocional",
    description: "Ingesta alimentaria desencadenada por estímulos emocionales (positivos o negativos) más que por señales homeostáticas de hambre.",
    diet: "Terapia conductual + sesiones semanales de TCC.",
    exercise: "Actividad física como regulador emocional.",
  },
  metabolismo_lento: {
    name: "Metabolismo Lento",
    description: "Gasto energético en reposo por debajo del predicho para su composición corporal. Baja actividad física espontánea (NEAT reducido).",
    diet: "Dieta baja en calorías con proteína post-entrenamiento.",
    exercise: "HIIT + entrenamiento de resistencia supervisado.",
  },
}

export default function AcostaSurvey({ patientId, onComplete }: AcostaSurveyProps) {
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [completed, setCompleted] = useState(false)

  const sections = [
    { id: "falla_de_saciedad", label: "Falla de Saciedad", icon: "🧠", questions: saciacionAlteradaQuestions, maxScore: 10 },
    { id: "intestino_hambriento", label: "Intestino Hambriento", icon: "🫃", questions: saciedadAceleradaQuestions, maxScore: 10 },
    { id: "hambre_emocional", label: "Hambre Emocional", icon: "💭", questions: hambreHedonicaQuestions, maxScore: 12 },
    { id: "metabolismo_lento", label: "Metabolismo Lento", icon: "🔥", questions: gastoEnergeticoReducidoQuestions, maxScore: 10 },
    { id: "saciedad_temprana", label: "Saciedad Temprana", icon: "⏱️", questions: saciedadTempranaQuestions, maxScore: 8 },
  ]

  const getSectionScore = (sectionId: string) => {
    const section = sections.find((s) => s.id === sectionId)
    if (!section) return 0
    return section.questions.reduce((sum, q) => sum + (answers[q.id] ?? 0), 0)
  }

  const getSectionProgress = (sectionId: string) => {
    const section = sections.find((s) => s.id === sectionId)
    if (!section) return 0
    return section.questions.filter((q) => answers[q.id] !== undefined).length
  }

  const allAnswered = sections.every((s) => s.questions.every((q) => answers[q.id] !== undefined))

  const handleComplete = () => {
    const results: AcostaSurveyResults = {
      saciacion_alterada_score: getSectionScore("falla_de_saciedad"),
      saciedad_acelerada_score: getSectionScore("intestino_hambriento"),
      hambre_hedonica_score: getSectionScore("hambre_emocional"),
      gasto_energetico_reducido_score: getSectionScore("metabolismo_lento"),
      saciedad_temprana_score: getSectionScore("saciedad_temprana"),
    }
    setCompleted(true)
    onComplete(results)
  }

  if (completed) {
    const results: AcostaSurveyResults = {
      saciacion_alterada_score: getSectionScore("falla_de_saciedad"),
      saciedad_acelerada_score: getSectionScore("intestino_hambriento"),
      hambre_hedonica_score: getSectionScore("hambre_emocional"),
      gasto_energetico_reducido_score: getSectionScore("metabolismo_lento"),
      saciedad_temprana_score: getSectionScore("saciedad_temprana"),
    }

    const detectedPhenotypes = [
      results.saciacion_alterada_score >= 6 && "Falla de Saciedad",
      results.saciedad_acelerada_score >= 6 && "Intestino Hambriento",
      results.hambre_hedonica_score >= 8 && "Hambre Emocional",
      results.gasto_energetico_reducido_score >= 6 && "Metabolismo Lento",
    ].filter(Boolean) as string[]

    return (
      <div className="space-y-6">
        <Card className="border-green-500/30 bg-green-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-400">
              <CheckCircle className="h-5 w-5" />
              Encuesta de Fenotipo Acosta Completada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {sections.map((s) => {
                const score = getSectionScore(s.id)
                const pct = Math.round((score / s.maxScore) * 100)
                const isHigh = pct >= 60
                return (
                  <div key={s.id} className={`p-3 rounded-lg border ${isHigh ? "border-amber-500/30 bg-amber-500/10" : "border-muted"}`}>
                    <p className="text-xs text-muted-foreground">{s.label}</p>
                    <p className={`text-lg font-bold ${isHigh ? "text-amber-400" : "text-muted-foreground"}`}>
                      {score}/{s.maxScore}
                    </p>
                    <p className="text-xs text-muted-foreground">{pct}%</p>
                  </div>
                )
              })}
            </div>

            {detectedPhenotypes.length > 0 && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <p className="text-sm font-medium text-amber-400 mb-2">Fenotipos detectados:</p>
                {detectedPhenotypes.map((p) => {
                  const key = p.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, "_")
                  const info = phenotypeInfo[key]
                  return (
                    <div key={p} className="mt-2">
                      <p className="text-sm font-medium">{p}</p>
                      {info && (
                        <div className="text-xs text-muted-foreground mt-1 space-y-1">
                          <p>{info.description}</p>
                          <p><span className="text-green-400">Dieta:</span> {info.diet}</p>
                          <p><span className="text-blue-400">Ejercicio:</span> {info.exercise}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (activeSection) {
    const section = sections.find((s) => s.id === activeSection)
    if (!section) return null

    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>{section.icon}</span>
              {section.label}
            </CardTitle>
            <CardDescription>
              {getSectionProgress(activeSection)}/{section.questions.length} respondidas
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {section.questions.map((q, qi) => (
              <div key={q.id} className="space-y-3">
                <Label className="text-sm font-medium">
                  {qi + 1}. {q.text}
                </Label>
                <div className="flex flex-wrap gap-2">
                  {q.options.map((opt) => (
                    <Button
                      key={opt.label}
                      variant={answers[q.id] === opt.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.value }))}
                      className="text-xs"
                    >
                      {opt.label}
                    </Button>
                  ))}
                </div>
              </div>
            ))}

            <div className="flex items-center justify-between pt-4 border-t">
              <Button variant="outline" onClick={() => setActiveSection(null)}>
                Volver a secciones
              </Button>
              <Button
                onClick={() => {
                  if (getSectionProgress(activeSection) === section.questions.length) {
                    const nextIdx = sections.findIndex((s) => s.id === activeSection) + 1
                    if (nextIdx < sections.length) {
                      setActiveSection(sections[nextIdx].id)
                    } else {
                      setActiveSection(null)
                    }
                  }
                }}
                disabled={getSectionProgress(activeSection) < section.questions.length}
              >
                {getSectionProgress(activeSection) === section.questions.length ? (
                  <>
                    Siguiente
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </>
                ) : (
                  `Complete todas (${getSectionProgress(activeSection)}/${section.questions.length})`
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Encuesta de Fenotipo de Obesidad (Acosta)
          </CardTitle>
          <CardDescription>
            Basada en "Personalisation of Obesity Management" — Acosta et al. 2023 (Mayo Clinic)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-md px-4 py-3 mb-4">
            <p className="text-sm text-amber-300">
              Esta encuesta identifica el fenotipo de obesidad del paciente para personalizar el tratamiento.
              Se basa en los 4 fenotipos descritos por Acosta: Cerebro Hambriento, Intestino Hambriento, Hambre Emocional y Slow Burn.
            </p>
          </div>

          {sections.map((s) => {
            const progress = getSectionProgress(s.id)
            const score = getSectionScore(s.id)
            const isComplete = progress === s.questions.length
            const isHigh = score >= s.maxScore * 0.6

            return (
              <div
                key={s.id}
                className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-colors ${
                  isComplete
                    ? isHigh
                      ? "border-amber-500/30 bg-amber-500/5"
                      : "border-green-500/30 bg-green-500/5"
                    : "border-muted hover:border-primary/50"
                }`}
                onClick={() => setActiveSection(s.id)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{s.icon}</span>
                  <div>
                    <p className="font-medium text-sm">{s.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {progress}/{s.questions.length} respondidas
                      {isComplete && ` — Score: ${score}/${s.maxScore}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isComplete && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${isHigh ? "bg-amber-500/20 text-amber-400" : "bg-green-500/20 text-green-400"}`}>
                      {isHigh ? "Alto riesgo" : "Normal"}
                    </span>
                  )}
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            )
          })}

          <div className="flex items-center justify-between pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              {sections.reduce((sum, s) => sum + getSectionProgress(s.id), 0)}/{sections.reduce((sum, s) => sum + s.questions.length, 0)} preguntas respondidas
            </p>
            <Button onClick={handleComplete} disabled={!allAnswered}>
              {allAnswered ? (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Completar encuesta
                </>
              ) : (
                `Complete todas las secciones`
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
