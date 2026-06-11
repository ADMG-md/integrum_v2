"use client"

import { Label } from "@/components/ui/form"
import { Checkbox, LabField, Section, ConsultationFormState } from "./consultation-form-types"

interface MensHealthPanelProps {
  form: ConsultationFormState
  set: (field: string, value: string) => void
  toggle: (field: string) => void
  expandedSections: Record<string, boolean>
  toggleSection: (key: string) => void
  limits?: Record<string, [number, number]>
}

export default function MensHealthPanel({ form, set, toggle, expandedSections, toggleSection, limits }: MensHealthPanelProps) {
  return (
    <Section sectionKey="mens" title="👨 Salud del Hombre" expanded={expandedSections.mens || false} onToggle={toggleSection}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <LabField label="Testosterona total" value={form.testosterone_total_ng_dl} onChange={(v) => set("testosterone_total_ng_dl", v)} placeholder="500" />
        <LabField label="LH" value={form.lh_u_l} onChange={(v) => set("lh_u_l", v)} placeholder="5" />
        <LabField label="FSH" value={form.fsh_u_l} onChange={(v) => set("fsh_u_l", v)} placeholder="5" />
        <LabField label="PSA" value={form.psa_ng_ml} onChange={(v) => set("psa_ng_ml", v)} placeholder="1.0" />
        <LabField label="Estradiol" value={form.estradiol_pg_ml} onChange={(v) => set("estradiol_pg_ml", v)} placeholder="30" />
        <LabField label="Prolactina" value={form.prolactin_ng_ml} onChange={(v) => set("prolactin_ng_ml", v)} placeholder="15" />
        <LabField label="DHEA-S" value={form.dhea_s_mcg_dl} onChange={(v) => set("dhea_s_mcg_dl", v)} placeholder="400" />
        <LabField label="IIEF-5" value={form.iief5_score} onChange={(v) => set("iief5_score", v)} placeholder="20" step="1" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <Checkbox label="Disfunción eréctil" checked={form.has_erectile_dysfunction} onChange={() => toggle("has_erectile_dysfunction")} />
        <Checkbox label="Problemas prostáticos" checked={form.has_prostate_issues} onChange={() => toggle("has_prostate_issues")} />
        <Checkbox label="Alopecia androgénica" checked={form.has_male_pattern_baldness} onChange={() => toggle("has_male_pattern_baldness")} />
        <Checkbox label="Ginecomastia" checked={form.has_gynecomastia} onChange={() => toggle("has_gynecomastia")} />
      </div>
    </Section>
  )
}
