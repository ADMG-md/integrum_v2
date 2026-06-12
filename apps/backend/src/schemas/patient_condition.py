from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.models.encounter import ConditionStatus

class PatientConditionBase(BaseModel):
    code: str
    title: str
    system: str = "CIE-10"
    status: ConditionStatus = ConditionStatus.ACTIVE

class PatientConditionCreate(PatientConditionBase):
    patient_id: str
    onset_encounter_id: Optional[str] = None

class PatientConditionUpdate(BaseModel):
    status: ConditionStatus

class PatientConditionRead(PatientConditionBase):
    id: str
    patient_id: str
    onset_encounter_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
