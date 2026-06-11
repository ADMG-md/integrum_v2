import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Share2 } from "lucide-react"
import { AdjudicationResult } from "@/types"

export const PatientActionPlan = ({ results }: { results: Record<string, AdjudicationResult> }) => {
  
  const generatePatientMessage = () => {
    let msg = "Hola! Este es tu plan de acción personalizado de Integrum V2:\n\n"
    
    // Nutrition Plan
    const nutrition = Object.entries(results).find(([n]) => n === "PrecisionNutritionMotor")
    if (nutrition && nutrition[1].action_checklist) {
      msg += "🍏 *Nutrición y Estilo de Vida*\n"
      nutrition[1].action_checklist.forEach(a => {
        msg += `• ${a.task}\n`
      })
      msg += "\n"
    }
    
    // Pharma Plan
    const pharma = Object.entries(results).find(([n]) => n === "PharmaPrecisionMotor")
    if (pharma && pharma[1].action_checklist) {
      msg += "💊 *Recomendaciones Médicas*\n"
      pharma[1].action_checklist.forEach(a => {
        msg += `• ${a.task}\n`
      })
      msg += "\n"
    }

    // Labs
    const labs = Object.entries(results).find(([n]) => n === "LaboratorySuggestionMotor")
    if (labs && labs[1].action_checklist) {
      msg += "🧪 *Sugerencias de Laboratorios*\n"
      labs[1].action_checklist.forEach(a => {
        msg += `• ${a.task}\n`
      })
      msg += "\n"
    }

    msg += "Recuerda que este es un resumen generado por tu equipo médico. Ante cualquier duda, consúltanos."
    
    return encodeURIComponent(msg)
  }

  const handleShare = () => {
    const text = generatePatientMessage()
    window.open(`https://wa.me/?text=${text}`, '_blank')
  }

  return (
    <Button onClick={handleShare} className="bg-green-600 hover:bg-green-700 text-white">
      <Share2 className="h-4 w-4 mr-2" />
      Compartir por WhatsApp
    </Button>
  )
}
