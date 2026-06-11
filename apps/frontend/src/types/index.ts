export type UserRole =
  | "SUPERADMIN"
  | "ADMINSTAFF"
  | "PHYSICIAN"
  | "NUTRITION_PHYSICIAN"
  | "PSYCHOLOGIST"
  | "AUDITOR"
  | "MEDICAL_DIRECTOR"
  | "EPS_MANAGER"
  | "PATIENT"

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  tenant_id: string
  is_active: boolean
}

export interface Token {
  access_token: string
  token_type: string
  role: string
}

export interface Patient {
  id: string
  external_id: string
  full_name: string
  date_of_birth: string | null
  gender: string | null
  email: string | null
  phone: string | null
  created_at: string
}

export interface Observation {
  code: string
  value: string | number | boolean
  unit?: string
  category?: string
  metadata_json?: Record<string, unknown>
  timestamp?: string
}

export interface Condition {
  code: string
  title: string
  system?: string
  clinical_status?: string
  verification_status?: string
  severity?: string
  onset_date?: string
  notes?: string
}

export interface AdjudicationResult {
  calculated_value: string
  confidence: number
  evidence: Array<{ type: string; code: string; value: string | number | boolean; display?: string; threshold?: string }>
  explanation?: string
  estado_ui?: string
  dato_faltante?: string | null
  recomendacion_farmacologica?: string[]
  action_checklist?: Array<{ category: string; priority: string; task: string; rationale: string }>
  critical_omissions?: Array<{ drug_class: string; gap_type: string; severity: string; clinical_rationale: string }>
  log_id?: string
  requirement_id?: string
  metadata?: Record<string, unknown>
  clinical_profile?: string
  status?: string
}

export interface DataReadinessReport {
  feasibility_score: number
  tier: string
  total_motors: number
  ready_count: number
  quickwin_count: number
  blocked_count: number
  ready_motors: string[]
  quickwins: Array<{ motor: string; missing: string[] }>
  priority_labs: Array<{ code: string; name: string; unlocks: number }>
  blocked_motors?: Array<{ motor: string; missing_codes: string[] }>
}

export interface EncounterResult {
  encounter_id: string
  results: Record<string, AdjudicationResult>
  data_readiness?: DataReadinessReport
}

export enum ReasonCode {
  AGREE_INSIGHT = "AGREE_INSIGHT",
  OVERRIDE_CLINICAL_INTUITION = "OVERRIDE_CLINICAL_INTUITION",
  OVERRIDE_ECONOMIC_BARRIER = "OVERRIDE_ECONOMIC_BARRIER",
  OVERRIDE_MISSING_CONTEXT = "OVERRIDE_MISSING_CONTEXT",
  OVERRIDE_PATIENT_REFUSAL = "OVERRIDE_PATIENT_REFUSAL",
  BIOLOGICAL_IMPOSSIBILITY = "BIOLOGICAL_IMPOSSIBILITY",
  PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT",
  TECHNICAL_ERROR = "TECHNICAL_ERROR",
}

export interface AdjudicationLogRead {
  id: string
  encounter_id: string
  engine_name: string
  engine_version_hash: string
  calculated_value: string
  confidence: number
  evidence: Array<Record<string, unknown>>
  requirement_id?: string | null
  created_at: string
  is_overridden: boolean
  physician_value?: string | null
  override_reason?: string | null
  physician_id?: string | null
  integrity_hash?: string | null
}

export interface AdjudicationOverridePayload {
  log_id: string
  physician_value: string
  override_reason_code: ReasonCode
  override_reason_text?: string
  physician_id?: string
}

export interface QuestionnaireResponse {
  questionnaire: string
  score: number
  responses: Record<string, number>
  severity?: string
}

export interface ClinicalRecommendation {
  recommendation_code: string
  domain: "nutrition" | "protein" | "behavioral" | "pharmacotherapy" | "sleep" | "risk"
  recommendation_type: "treatment" | "referral" | "sequencing" | "alert"
  requirement_id: string
  priority: "standard" | "high" | "critical"
  status: "active" | "suppressed" | "modified" | "informational"
  depends_on: string[]
  trigger_summary: string[]
  human_readable_basis: string
  evidence_note?: string
  superseded_by?: string
  suppression_reason?: string
  audit_payload: Record<string, unknown>
}
