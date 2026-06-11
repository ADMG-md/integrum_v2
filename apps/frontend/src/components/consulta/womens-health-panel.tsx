"use client"

import { Label } from "@/components/ui/form"
import { Input } from "@/components/ui/form"
import { Checkbox, LabField, Section, ConsultationFormState } from "./consultation-form-types"

interface WomensHealthPanelProps {
  form: ConsultationFormState
  set: (field: string, value: string) => void
  toggle: (field: string) => void
  expandedSections: Record<string, boolean>
  toggleSection: (key: string) => void
  limits?: Record<string, [number, number]>
}

export default function WomensHealthPanel({ form, set, toggle, expandedSections, toggleSection, limits }: WomensHealthPanelProps) {
  return (
    <Section sectionKey="womens" title="👩 Salud de la Mujer" expanded={expandedSections.womens || false} onToggle={toggleSection}>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label>Estado embarazo</Label>
          <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.pregnancy_status} onChange={(e) => set("pregnancy_status", e.target.value)}>
            <option value="unknown">Desconocido</option><option value="not_pregnant">No embarazada</option>
            <option value="pregnant">Embarazada</option><option value="postpartum">Postparto</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label>Estado menopáusico</Label>
          <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.menopausal_status} onChange={(e) => set("menopausal_status", e.target.value)}>
            <option value="unknown">Desconocido</option><option value="pre">Pre</option>
            <option value="peri">Peri</option><option value="post">Post</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label>Regularidad ciclos</Label>
          <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm" value={form.cycle_regularity} onChange={(e) => set("cycle_regularity", e.target.value)}>
            <option value="unknown">Desconocido</option><option value="regular">Regular</option>
            <option value="irregular">Irregular</option><option value="amenorrhea">Amenorrea</option>
          </select>
        </div>
        <LabField label="Ferriman-Gallwey" value={form.ferriman_gallwey_score} onChange={(v) => set("ferriman_gallwey_score", v)} placeholder="0" step="1" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <LabField label="Testosterona total" value={form.testosterone_total_ng_dl} onChange={(v) => set("testosterone_total_ng_dl", v)} placeholder="30" />
        <LabField label="AMH" value={form.amh_ng_ml} onChange={(v) => set("amh_ng_ml", v)} placeholder="3.0" />
        <LabField label="LH" value={form.lh_u_l} onChange={(v) => set("lh_u_l", v)} placeholder="5" />
        <LabField label="FSH" value={form.fsh_u_l} onChange={(v) => set("fsh_u_l", v)} placeholder="5" />
        <LabField label="Estradiol" value={form.estradiol_pg_ml} onChange={(v) => set("estradiol_pg_ml", v)} placeholder="30" />
        <LabField label="Prolactina" value={form.prolactin_ng_ml} onChange={(v) => set("prolactin_ng_ml", v)} placeholder="15" />
        <LabField label="DHEA-S" value={form.dhea_s_mcg_dl} onChange={(v) => set("dhea_s_mcg_dl", v)} placeholder="200" />
        <LabField label="Vitamina D" value={form.vitamin_d_ng_ml} onChange={(v) => set("vitamin_d_ng_ml", v)} placeholder="30" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <Checkbox label="Endometriosis" checked={form.has_endometriosis} onChange={() => toggle("has_endometriosis")} />
        <Checkbox label="Preeclampsia previa" checked={form.has_history_preeclampsia} onChange={() => toggle("has_history_preeclampsia")} />
        <Checkbox label="Diabetes gestacional" checked={form.has_history_gestational_diabetes} onChange={() => toggle("has_history_gestational_diabetes")} />
        <Checkbox label="Terapia hormonal (HRT)" checked={form.on_hrt} onChange={() => toggle("on_hrt")} />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div className="space-y-2">
          <Label>Método anticoncepción</Label>
          <Input value={form.contraception_method} onChange={(e) => set("contraception_method", e.target.value)} placeholder="DIU, pastillas, etc." className="h-8 text-sm" />
        </div>
        <div className="space-y-2">
          <Label>Última menstruación</Label>
          <Input type="date" value={form.last_menstrual_period} onChange={(e) => set("last_menstrual_period", e.target.value)} className="h-8 text-sm" />
        </div>
      </div>
    </Section>
  )
}
