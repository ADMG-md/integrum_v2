from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ConsentCreate(BaseModel):
    patient_id: str
    encounter_id: Optional[str] = None
    consent_type: str = "SAMD_ANALYSIS_V1"
    is_granted: bool = True
    signature_data: Optional[str] = None # Base64 or simple string for demo
    terms_version: str = "2026.03.14-ES"

class ConsentRead(BaseModel):
    id: str
    patient_id: str
    encounter_id: Optional[str]
    consent_type: str
    is_granted: bool
    terms_version: str
    created_at: datetime

    class Config:
        from_attributes = True
