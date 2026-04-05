from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
import uuid

class ConditionBase(BaseModel):
    code: str = Field(..., description="CIE-11 Code")
    title: str = Field(..., description="Condition title")
    description: Optional[str] = None
    system: str = "CIE-11"

class ConditionCreate(ConditionBase):
    pass

class ConditionRead(ConditionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
