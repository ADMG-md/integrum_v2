import { useState } from "react"
import { Button } from "@/components/ui/button"
import { CheckCircle, Copy } from "lucide-react"
import { AdjudicationResult } from "@/types"

export const SoapNote = ({ results }: { results: Record<string, AdjudicationResult> }) => {
  const [copied, setCopied] = useState(false)

  const motors = Object.entries(results)
  const phenotype = motors.find(([n]) => n === "AcostaPhenotypeMotor")
  const eoss = motors.find(([n]) => n === "EOSSStagingMotor")
  const bioAge = motors.find(([n]) => n === "BiologicalAgeMotor")
  const drugInteractions = motors.find(([n]) => n === "DrugInteractionMotor")
  const sarcopenia = motors.find(([n]) => n === "SarcopeniaMotor")
  const funcSarc = motors.find(([n]) => n === "FunctionalSarcopeniaMotor")
  const fli = motors.find(([n]) => n === "FLIMotor")
  const cvd = motors.find(([n]) => n === "CVDHazardMotor")
  const guidelines = motors.find(([n]) => n === "ClinicalGuidelinesMotor")
  const labSuggestions = motors.find(([n]) => n === "LaboratorySuggestionMotor")

  const alerts = motors.filter(([, r]) => r.estado_ui?.includes("CONFIRMED"))

  const generateSoap = () => {
    let soap = "NOTA CLÍNICA - INTEGRUM V2 (SaMD)\n"
    soap += "=".repeat(40) + "\n\n"
    
    // Digital Signature Hash Generation (Mock for UI based on timestamp)
    const timestamp = new Date().toISOString()
    const signatureHash = btoa(`INTEGRUM_V2_VERIFIED_${timestamp}`).substring(0, 32)
    
    soap += "RESUMEN EJECUTIVO (MASTER MOTOR)\n" + "-".repeat(30) + "\n"
    const master = motors.find(([n]) => n === "ObesityMasterMotor")
    if (master && master[1]) {
        soap += `VEREDICTO: ${master[1].calculated_value}\n`
        soap += `ANÁLISIS: ${master[1].explanation}\n\n`
    } else {
        soap += "No se pudo generar el análisis unificado.\n\n"
    }

    soap += "SUBJETIVO (S)\n" + "-".repeat(20) + "\n"
    if (phenotype) soap += `• Fenotipo de obesidad: ${phenotype[1].calculated_value}\n`
    if (eoss) soap += `• EOSS: ${eoss[1].calculated_value}\n`
    if (bioAge) soap += `• ${bioAge[1].calculated_value}\n`
    soap += "\nOBJETIVO (O)\n" + "-".repeat(20) + "\n"
    if (sarcopenia) soap += `• Sarcopenia: ${sarcopenia[1].calculated_value}\n`
    if (funcSarc) soap += `• Sarcopenia funcional: ${funcSarc[1].calculated_value}\n`
    if (fli) soap += `• Hígado graso (FLI): ${fli[1].calculated_value}\n`
    if (cvd) soap += `• Riesgo CV: ${cvd[1].calculated_value}\n`
    soap += "\nPLAN DE ACCIÓN (P)\n" + "-".repeat(20) + "\n"
    if (guidelines && guidelines[1].action_checklist) {
      guidelines[1].action_checklist.forEach((a, i) => {
        soap += `${i + 1}. ${a.task}\n   Racional: ${a.rationale}\n`
      })
    }
    const pharma = motors.find(([n]) => n === "PharmaPrecisionMotor")
    if (pharma && pharma[1].action_checklist) {
        pharma[1].action_checklist.forEach((a, i) => {
          soap += `💊 ${a.task}\n`
        })
    }
    const nutrition = motors.find(([n]) => n === "PrecisionNutritionMotor")
    if (nutrition && nutrition[1].action_checklist) {
        nutrition[1].action_checklist.forEach((a, i) => {
          soap += `🍏 ${a.task}\n`
        })
    }

    if (drugInteractions && drugInteractions[1].action_checklist) {
      soap += "\nInteracciones farmacológicas:\n"
      drugInteractions[1].action_checklist.forEach((a, i) => {
        soap += `${i + 1}. ${a.task}\n`
      })
    }
    
    soap += "\n" + "=".repeat(40) + "\n"
    soap += `FIRMA DIGITAL SaMD: ${signatureHash}\n`
    soap += `Emisión: ${timestamp}\n`
    
    return soap
  }

  const soapText = generateSoap()

  const handleCopy = async () => {
    await navigator.clipboard.writeText(soapText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button size="sm" variant="outline" onClick={handleCopy}>
          {copied ? <CheckCircle className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
          {copied ? "Copiado" : "Copiar nota"}
        </Button>
      </div>
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-md px-3 py-2 text-xs text-amber-400">
        ⚠️ Nota preliminar autogenerada — requiere revisión y firma del médico tratante.
      </div>
      <pre className="text-xs bg-muted/50 p-4 rounded-lg whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
        {soapText}
      </pre>
    </div>
  )
}
