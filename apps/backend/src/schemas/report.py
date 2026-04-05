from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.schemas.encounter import AdjudicationResultSchema

class ClinicalSuggestionSchema(BaseModel):
    title: str
    description: str
    priority: str # "High" | "Medium" | "Low"
    category: str # "Therapeutic" | "Diagnostic" | "Preventive"
    evidence_codes: List[str] = []

class ClinicalReportSchema(BaseModel):
    report_id: str
    patient_id: Optional[str] = "P-101"
    generated_at: datetime = Field(default_factory=datetime.now)
    technical_summary: str
    engine_adjudications: Dict[str, AdjudicationResultSchema]
    suggestions: List[ClinicalSuggestionSchema] = []
    phenotype_radar_data: Dict[str, float] = {}
    captured_data: List[Any] = [] # List of raw observations (Mission 4 Fix)
    
    # Mission 6: Hybrid Intelligence
    clinician_prompt: Optional[str] = None
    patient_narrative: Optional[str] = None
    
    # Narrative History (Mission 4 Regression Fix)
    reason_for_visit: Optional[str] = None
    personal_history: Optional[str] = None
    family_history: Optional[str] = None

class ClinicalReportResponse(BaseModel):
    id: str
    report: ClinicalReportSchema
