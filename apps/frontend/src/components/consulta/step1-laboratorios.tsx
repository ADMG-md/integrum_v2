"use client"

import { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/form"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, ClipboardList, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { LabField, CsvImport, ConsultationFormState, Checkbox } from "./consultation-form-types"

interface Step1LabsProps {
  form: ConsultationFormState
  set: (field: string, value: string) => void
  toggle: (field: string) => void
  limits?: Record<string, [number, number]>
}

export default function Step1Laboratorios({ form, set, toggle, limits }: Step1LabsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [pdfUpload, setPdfUpload] = useState<{ status: "idle" | "uploading" | "success" | "error"; count: number; message: string }>({ status: "idle", count: 0, message: "" })

  const loincToField: Record<string, string> = {
    "2339-0": "glucose_mg_dl", "4548-4": "hba1c_percent", "20448-7": "insulin_mu_u_ml",
    "17858-5": "c_peptide_ng_ml", "2160-0": "creatinine_mg_dl", "3084-1": "uric_acid_mg_dl",
    "1920-8": "ast_u_l", "1742-6": "alt_u_l", "2324-2": "ggt_u_l",
    "6768-6": "alkaline_phosphatase_u_l", "6690-2": "wbc_k_ul",
    "26474-7": "lymphocyte_percent", "26512-4": "neutrophil_percent",
    "787-2": "mcv_fl", "788-0": "rdw_percent", "777-3": "platelets_k_u_l",
    "30522-7": "hs_crp_mg_l", "2276-4": "ferritin_ng_ml", "1751-7": "albumin_g_dl",
    "11579-0": "tsh_uIU_ml", "3024-7": "ft4_ng_dl", "3053-3": "ft3_pg_ml",
    "2093-3": "total_cholesterol_mg_dl", "13457-7": "ldl_mg_dl",
    "2085-9": "hdl_mg_dl", "2571-8": "triglycerides_mg_dl",
    "30388-3": "vldl_mg_dl", "13456-9": "apob_mg_dl", "35199-8": "lpa_mg_dl",
  }

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPdfUpload({ status: "uploading", count: 0, message: "" })
    try {
      const { api } = await import("@/lib/api")
      const formData = new FormData()
      formData.append("file", file)
      const result = await api.uploadFile<Record<string, unknown>>("/extraction/upload-pdf", formData)
      const findings = (result.findings as Array<{ code: string; physiological: boolean; value: number }>) || []
      let filledCount = 0
      for (const f of findings) {
        const field = loincToField[f.code]
        if (field && f.physiological) {
          set(field, String(f.value))
          filledCount++
        }
      }
      setPdfUpload({ status: "success", count: filledCount, message: `${filledCount} labs extraídos${result.pii_scrubbed ? " (PII eliminado)" : ""}` })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error procesando PDF"
      setPdfUpload({ status: "error", count: 0, message })
    }
  }

  return (
    <div className="space-y-6">
      {/* Import Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Upload className="h-4 w-4" /> PDF de Laboratorios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 border-2 border-dashed rounded-lg border-muted-foreground/25 text-center">
              {pdfUpload.status === "success" && (
                <p className="text-xs text-green-400 mb-2"><CheckCircle className="h-4 w-4 inline mr-1" />{pdfUpload.message}</p>
              )}
              {pdfUpload.status === "error" && (
                <p className="text-xs text-destructive mb-2"><AlertCircle className="h-4 w-4 inline mr-1" />{pdfUpload.message}</p>
              )}
              <input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={handlePdfUpload} disabled={pdfUpload.status === "uploading"} />
              <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={pdfUpload.status === "uploading"}>
                {pdfUpload.status === "uploading" ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Procesando...</> : <><Upload className="h-4 w-4 mr-2" />Subir PDF</>}
              </Button>
              <p className="text-xs text-muted-foreground mt-2">Extrae labs automáticamente. PII eliminado.</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <ClipboardList className="h-4 w-4" /> CSV de Laboratorios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CsvImport onImport={(labs) => {
              for (const [key, value] of Object.entries(labs)) {
                if (key in form) set(key, String(value))
              }
            }} />
          </CardContent>
        </Card>
      </div>

      {/* Glucosa/Insulina */}
      <div>
        <Label className="mb-2 block text-sm font-medium">Glucosa / Insulina</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="Glucosa (mg/dL)" value={form.glucose_mg_dl} onChange={(v) => set("glucose_mg_dl", v)} placeholder="100" min="40" max="600" />
          <LabField label="HbA1c (%)" value={form.hba1c_percent} onChange={(v) => set("hba1c_percent", v)} placeholder="5.7" min="3" max="18" />
          <LabField label="Insulina (μU/mL)" value={form.insulin_mu_u_ml} onChange={(v) => set("insulin_mu_u_ml", v)} placeholder="10" min="0.5" max="500" />
          <LabField label="Péptido C" value={form.c_peptide_ng_ml} onChange={(v) => set("c_peptide_ng_ml", v)} placeholder="2.0" min="0.1" max="50" />
          <div className="flex items-end"><Checkbox label="GADA (+)" checked={form.gada_antibodies} onChange={() => toggle("gada_antibodies")} /></div>
        </div>
      </div>

      {/* Hepático/Renal */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Hepático / Renal</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="AST (U/L)" value={form.ast_u_l} onChange={(v) => set("ast_u_l", v)} placeholder="25" />
          <LabField label="ALT (U/L)" value={form.alt_u_l} onChange={(v) => set("alt_u_l", v)} placeholder="25" />
          <LabField label="GGT (U/L)" value={form.ggt_u_l} onChange={(v) => set("ggt_u_l", v)} placeholder="30" />
          <LabField label="FA (U/L)" value={form.alkaline_phosphatase_u_l} onChange={(v) => set("alkaline_phosphatase_u_l", v)} placeholder="80" />
          <LabField label="Creatinina" value={form.creatinine_mg_dl} onChange={(v) => set("creatinine_mg_dl", v)} placeholder="1.0" />
          <LabField label="Ácido úrico" value={form.uric_acid_mg_dl} onChange={(v) => set("uric_acid_mg_dl", v)} placeholder="5.0" />
        </div>
      </div>

      {/* Hemograma */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Hemograma</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="WBC (K/μL)" value={form.wbc_k_ul} onChange={(v) => set("wbc_k_ul", v)} placeholder="7.0" />
          <LabField label="Linfocitos (%)" value={form.lymphocyte_percent} onChange={(v) => set("lymphocyte_percent", v)} placeholder="30" />
          <LabField label="Neutrófilos (%)" value={form.neutrophil_percent} onChange={(v) => set("neutrophil_percent", v)} placeholder="55" />
          <LabField label="MCV (fL)" value={form.mcv_fl} onChange={(v) => set("mcv_fl", v)} placeholder="90" />
          <LabField label="RDW (%)" value={form.rdw_percent} onChange={(v) => set("rdw_percent", v)} placeholder="13" />
          <LabField label="Plaquetas (K/μL)" value={form.platelets_k_u_l} onChange={(v) => set("platelets_k_u_l", v)} placeholder="250" />
        </div>
      </div>

      {/* Inflamación/Hierro */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Inflamación / Hierro</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="hs-CRP (mg/L)" value={form.hs_crp_mg_l} onChange={(v) => set("hs_crp_mg_l", v)} placeholder="1.0" />
          <LabField label="Ferritina (ng/mL)" value={form.ferritin_ng_ml} onChange={(v) => set("ferritin_ng_ml", v)} placeholder="100" />
          <LabField label="Albúmina (g/dL)" value={form.albumin_g_dl} onChange={(v) => set("albumin_g_dl", v)} placeholder="4.0" />
        </div>
      </div>

      {/* Tiroides */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Tiroides / Hormonal</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="TSH (μIU/mL)" value={form.tsh_uIU_ml} onChange={(v) => set("tsh_uIU_ml", v)} placeholder="2.5" />
          <LabField label="FT4 (ng/dL)" value={form.ft4_ng_dl} onChange={(v) => set("ft4_ng_dl", v)} placeholder="1.2" />
          <LabField label="FT3 (pg/mL)" value={form.ft3_pg_ml} onChange={(v) => set("ft3_pg_ml", v)} placeholder="3.2" />
          <LabField label="rT3 (ng/dL)" value={form.rt3_ng_dl} onChange={(v) => set("rt3_ng_dl", v)} placeholder="15" />
          <LabField label="SHBG (nmol/L)" value={form.shbg_nmol_l} onChange={(v) => set("shbg_nmol_l", v)} placeholder="40" />
          <LabField label="Cortisol AM" value={form.cortisol_am_mcg_dl} onChange={(v) => set("cortisol_am_mcg_dl", v)} placeholder="15" />
        </div>
      </div>

      {/* Lípidos */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Perfil Lipídico</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="Col. Total" value={form.total_cholesterol_mg_dl} onChange={(v) => set("total_cholesterol_mg_dl", v)} placeholder="200" />
          <LabField label="LDL" value={form.ldl_mg_dl} onChange={(v) => set("ldl_mg_dl", v)} placeholder="130" />
          <LabField label="HDL" value={form.hdl_mg_dl} onChange={(v) => set("hdl_mg_dl", v)} placeholder="45" />
          <LabField label="Triglicéridos" value={form.triglycerides_mg_dl} onChange={(v) => set("triglycerides_mg_dl", v)} placeholder="150" />
          <LabField label="VLDL" value={form.vldl_mg_dl} onChange={(v) => set("vldl_mg_dl", v)} placeholder="30" />
          <LabField label="ApoB" value={form.apob_mg_dl} onChange={(v) => set("apob_mg_dl", v)} placeholder="100" />
          <LabField label="Lp(a)" value={form.lpa_mg_dl} onChange={(v) => set("lpa_mg_dl", v)} placeholder="30" />
          <LabField label="ApoA1" value={form.apoa1_mg_dl} onChange={(v) => set("apoa1_mg_dl", v)} placeholder="140" />
        </div>
      </div>

      {/* Hipertensión */}
      <div className="border-t pt-4">
        <Label className="mb-2 block text-sm font-medium">Screening Hipertensión Secundaria</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <LabField label="Aldosterona" value={form.aldosterone_ng_dl} onChange={(v) => set("aldosterone_ng_dl", v)} placeholder="10" />
          <LabField label="Renina" value={form.renin_ng_ml_h} onChange={(v) => set("renin_ng_ml_h", v)} placeholder="1.5" />
        </div>
      </div>
    </div>
  )
}
