export interface Condition {
  id: string; // UUID
  code: string;
  title: string;
  description?: string;
  system: string;
  created_at: string; // ISO Date
  updated_at: string; // ISO Date
}

export type ConditionCreate = Omit<Condition, 'id' | 'created_at' | 'updated_at'>;
