import { ReactNode } from "react"
import { Activity, FileText, Pill } from "lucide-react"
import { useMotorGroups as hookUseMotorGroups } from "@/hooks/useMotorGroups"

export interface MotorGroup {
  key: string
  label: string
  icon: ReactNode
  motors: string[]
}

// Re-export the hook for backward compatibility
export const useMotorGroups = hookUseMotorGroups

// Static fallback groups for backward compatibility during transition
export const MOTOR_GROUPS: MotorGroup[] = [
  {
    key: "core",
    label: "Perfil Metabólico",
    icon: <Activity className="h-4 w-4" />,
    motors: [
      "AcostaPhenotypeMotor", "EOSSStagingMotor", "SarcopeniaMotor",
      "BiologicalAgeMotor", "MetabolicPrecisionMotor", "DeepMetabolicProxyMotor",
      "Lifestyle360Motor",
    ],
  },
  {
    key: "specialty",
    label: "Especialidad",
    icon: <Activity className="h-4 w-4" />,
    motors: [
      "AnthropometryMotor", "EndocrineMotor", "HypertensionMotor",
      "InflammationMotor", "SleepApneaMotor", "LaboratoryStewardshipMotor",
      "FunctionalSarcopeniaMotor",
    ],
  },
  {
    key: "liver",
    label: "Hígado + Adiposidad",
    icon: <Activity className="h-4 w-4" />,
    motors: ["FLIMotor", "VAIMotor", "NFSMotor"],
  },
  {
    key: "safety",
    label: "Seguridad + Screening",
    icon: <Activity className="h-4 w-4" />,
    motors: [
      "GLP1MonitoringMotor", "MetforminB12Motor", "CancerScreeningMotor",
      "ApoBApoA1Motor", "PulsePressureMotor", "DrugInteractionMotor",
      "TyGBMIMotor", "CVDReclassifierMotor",
    ],
  },
  {
    key: "labs",
    label: "Sugerencias de Laboratorio",
    icon: <Activity className="h-4 w-4" />,
    motors: ["LaboratorySuggestionMotor"],
  },
  {
    key: "pediatric",
    label: "Nutrición Pediátrica",
    icon: <Activity className="h-4 w-4" />,
    motors: ["PediatricNutritionMotor"],
  },
  {
    key: "clinical",
    label: "Integración Clínica",
    icon: <Activity className="h-4 w-4" />,
    motors: [
      "ACEScoreEngine", "SGLT2iBenefitMotor", "FreeTestosteroneMotor",
      "VitaminDMotor", "CharlsonMotor",
    ],
  },
  {
    key: "gender",
    label: "Salud Sexual",
    icon: <Activity className="h-4 w-4" />,
    motors: ["WomensHealthMotor", "MensHealthMotor"],
  },
  {
    key: "therapy",
    label: "Terapia + Optimización",
    icon: <Activity className="h-4 w-4" />,
    motors: [
      "BodyCompositionTrendMotor", "ObesityPharmaEligibilityMotor",
      "GLP1TitrationMotor", "ProteinEngineMotor",
    ],
  },
  {
    key: "risk",
    label: "Riesgo Cardiovascular",
    icon: <Activity className="h-4 w-4" />,
    motors: ["CVDHazardMotor", "MarkovProgressionMotor", "KFREMotor"],
  },
  {
    key: "precision",
    label: "Medicina de Precisión (Genómica)",
    icon: <Pill className="h-4 w-4" />,
    motors: ["PrecisionNutritionMotor", "PharmaPrecisionMotor", "PharmacogenomicProxyMotor", "PsychometabolicAxisMotor"],
  },
  {
    key: "guidelines",
    label: "Guías Clínicas",
    icon: <FileText className="h-4 w-4" />,
    motors: ["ObesityMasterMotor", "ClinicalGuidelinesMotor"],
  },
]
