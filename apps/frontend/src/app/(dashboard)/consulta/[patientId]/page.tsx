"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import ConsultationForm from "@/components/consulta/ConsultationForm"
import ResultsViewer from "@/components/consulta/ResultsViewer"
import { DataReadinessReport, AdjudicationResult, EncounterResult } from "@/types"
import { api } from "@/lib/api"
import { BaselineEncounter } from "@/components/consulta/consultation-form-types"

export default function ConsultaPage() {
  const params = useParams()
  const patientId = params.patientId as string
  const [results, setResults] = useState<Record<string, AdjudicationResult>>({})
  const [encounterId, setEncounterId] = useState("")
  const [dataReadiness, setDataReadiness] = useState<DataReadinessReport | null>(null)
  const [baseline, setBaseline] = useState<BaselineEncounter | null>(null)

  useEffect(() => {
    api.get<BaselineEncounter | null>(`/encounters/patient/${patientId}/latest`)
      .then((data) => setBaseline(data))
      .catch(() => setBaseline(null))
  }, [patientId])

  const handleResults = (data: EncounterResult) => {
    setResults(data.results)
    setEncounterId(data.encounter_id)
    setDataReadiness(data.data_readiness || null)
  }

  const handleFinalize = () => {
    alert("Encuentro finalizado exitosamente")
    setResults({})
    setEncounterId("")
    setDataReadiness(null)
  }

  const handleBack = () => {
    setResults({})
    setDataReadiness(null)
  }

  if (Object.keys(results).length > 0 && encounterId) {
    return (
      <ResultsViewer
        encounterId={encounterId}
        results={results}
        dataReadiness={dataReadiness}
        baselineResults={(baseline?.phenotype_result as Record<string, AdjudicationResult> | null) || null}
        baselineDate={baseline?.created_at || null}
        onFinalize={handleFinalize}
        onBack={handleBack}
      />
    )
  }

  return (
    <ConsultationForm
      patientId={patientId}
      baseline={baseline}
      onSubmit={handleResults}
    />
  )
}
