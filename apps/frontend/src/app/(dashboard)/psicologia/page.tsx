"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Activity, Heart, Scale } from "lucide-react"

export default function PsicologiaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Psicología</h2>
        <p className="text-muted-foreground">Seleccione un paciente para aplicar cuestionarios</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: <Brain className="h-5 w-5" />, label: "PHQ-9", desc: "Depresión" },
          { icon: <Activity className="h-5 w-5" />, label: "GAD-7", desc: "Ansiedad" },
          { icon: <Scale className="h-5 w-5" />, label: "TFEQ-R18", desc: "Conducta alimentaria" },
          { icon: <Heart className="h-5 w-5" />, label: "FNQ", desc: "Food Noise" },
        ].map((q) => (
          <Card key={q.label}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                {q.icon}
                {q.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{q.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
