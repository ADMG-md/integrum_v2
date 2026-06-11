import { ReactNode } from "react"
import { Activity, FileText, Pill, Utensils } from "lucide-react"

export const MOTOR_GROUP_ICONS: Record<string, ReactNode> = {
  "core": <Activity className="h-4 w-4" />,
  "specialty": <Activity className="h-4 w-4" />,
  "liver": <Activity className="h-4 w-4" />,
  "safety": <Activity className="h-4 w-4" />,
  "labs": <Activity className="h-4 w-4" />,
  "pediatric": <Activity className="h-4 w-4" />,
  "clinical": <Activity className="h-4 w-4" />,
  "gender": <Activity className="h-4 w-4" />,
  "therapy": <Activity className="h-4 w-4" />,
  "risk": <Activity className="h-4 w-4" />,
  "precision": <Pill className="h-4 w-4" />,
  "guidelines": <FileText className="h-4 w-4" />,
  "other": <Activity className="h-4 w-4" />,
}

export const MOTOR_GROUP_LABELS: Record<string, string> = {
  "core": "Perfil Metabólico",
  "specialty": "Especialidad",
  "liver": "Hígado + Adiposidad",
  "safety": "Seguridad + Screening",
  "labs": "Sugerencias de Laboratorio",
  "pediatric": "Nutrición Pediátrica",
  "clinical": "Integración Clínica",
  "gender": "Salud Sexual",
  "therapy": "Terapia + Optimización",
  "risk": "Riesgo Cardiovascular",
  "precision": "Medicina de Precisión (Genómica)",
  "guidelines": "Guías Clínicas",
  "other": "Otros Motores",
}
