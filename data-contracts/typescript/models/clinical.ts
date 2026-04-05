export interface ClinicalEvidence {
  type: string;
  code: string;
  display?: string;
  value?: any;
  threshold?: string;
}

export interface AdjudicationResult {
  calculated_value: string;
  confidence: number;
  evidence: ClinicalEvidence[];
  metadata: Record<string, any>;
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

export interface Encounter {
  id: string;
  conditions: Condition[];
  observations: Observation[];
  medications: MedicationStatement[];
}
