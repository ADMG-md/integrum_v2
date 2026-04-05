from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class DecisionType(str, Enum):
    AGREEMENT = "AGREEMENT"
    OVERRIDE = "OVERRIDE"

class ReasonCode(str, Enum):
    AGREE_INSIGHT = "AGREE_INSIGHT"
    OVERRIDE_CLINICAL_INTUITION = "OVERRIDE_CLINICAL_INTUITION"
    OVERRIDE_ECONOMIC_BARRIER = "OVERRIDE_ECONOMIC_BARRIER"
    OVERRIDE_MISSING_CONTEXT = "OVERRIDE_MISSING_CONTEXT"
    OVERRIDE_PATIENT_REFUSAL = "OVERRIDE_PATIENT_REFUSAL"

class DecisionAuditSchema(BaseModel):
    engine_name: str
    engine_version_hash: str
    decision_type: DecisionType
    reason_code: ReasonCode
    physician_id: str

class AdjudicationOverride(BaseModel):
    log_id: str
    physician_value: str
    override_reason: str
    physician_id: str = "DR-001"
