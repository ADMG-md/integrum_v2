export interface ClinicalEvidence {
  type: string;
  code: string;
  display?: string;
  value?: any;
  threshold?: string;
}

export interface ActionItem {
  category: "pharmacological" | "lifestyle" | "referral" | "diagnostic";
  priority: "low" | "medium" | "high" | "critical";
  task: string;
  rationale: string;
  status?: string;
}

export interface AdjudicationResult {
  calculated_value: string;
  confidence: number;
  evidence: ClinicalEvidence[];
  metadata: Record<string, any>;
  requirement_id?: string;
  explanation?: string;
  estado_ui?: string;
  action_checklist?: ActionItem[];
}

export interface Observation {
  code: string;
  value: any;
  unit?: string;
  category: "Clinical" | "Genomic" | "Epigenetic" | "Proteomic";
  metadata: Record<string, any>;
  timestamp: string;
}

export interface Condition {
  code: string;
  title: string;
  system: string;
}

export interface MedicationStatement {
  code: string;
  name: string;
  is_active: boolean;
}

export interface ClinicalHistory {
  has_type2_diabetes: boolean;
  has_hypertension: boolean;
  has_dyslipidemia: boolean;
  has_ckd: boolean;
  has_osa: boolean;
  has_nafld: boolean;
  pregnancy_status: string;
  has_eating_disorder_history: boolean;
  has_seizures_history: boolean;
  has_history_medullary_thyroid_carcinoma: boolean;
  has_history_men2: boolean;
  has_history_pancreatitis: boolean;
  has_gastroparesis: boolean;
  phq9_item_9_score?: number;
}

export interface Encounter {
  id: string;
  conditions: Condition[];
  observations: Observation[];
  medications: MedicationStatement[];
  history?: ClinicalHistory;
}
