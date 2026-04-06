from pydantic import BaseModel
from typing import Optional
from enum import Enum


class DecisionType(str, Enum):
    AGREEMENT = "AGREEMENT"
    OVERRIDE = "OVERRIDE"


class ReasonCode(str, Enum):
    """
    Controlled vocabulary for physician-AI concordance decisions.
    Used in DecisionAuditLog (finalize) and AdjudicationOverride (manual override).

    Research note: these codes are the unit of analysis for concordance studies.
    Text-free rationale is noise; structured codes are signal.
    """
    # Agreement codes
    AGREE_INSIGHT = "AGREE_INSIGHT"                   # Motor output matches clinical judgment

    # Override codes — why the physician disagreed
    OVERRIDE_CLINICAL_INTUITION = "OVERRIDE_CLINICAL_INTUITION"    # Gut/experience overrides algo
    OVERRIDE_ECONOMIC_BARRIER = "OVERRIDE_ECONOMIC_BARRIER"        # Correct but not affordable/available
    OVERRIDE_MISSING_CONTEXT = "OVERRIDE_MISSING_CONTEXT"          # Data missing that changes interpretation
    OVERRIDE_PATIENT_REFUSAL = "OVERRIDE_PATIENT_REFUSAL"          # Patient declined recommendation

    # Extended for research granularity
    BIOLOGICAL_IMPOSSIBILITY = "BIOLOGICAL_IMPOSSIBILITY"   # Motor output is clinically impossible given full context
    PARTIAL_AGREEMENT = "PARTIAL_AGREEMENT"                 # Direction correct, magnitude/classification wrong
    TECHNICAL_ERROR = "TECHNICAL_ERROR"                     # Suspected data entry error affected motor output


class DecisionAuditSchema(BaseModel):
    engine_name: str
    engine_version_hash: str
    decision_type: DecisionType
    reason_code: ReasonCode
    physician_id: str


class AdjudicationOverride(BaseModel):
    """
    Manual post-hoc override of a specific motor's adjudication result.
    override_reason_code uses controlled vocabulary (ReasonCode) for research analyzability.
    override_reason_text is optional free text for additional context — stored but not indexed.
    """
    log_id: str
    physician_value: str
    override_reason_code: ReasonCode                        # Structured — primary field for analysis
    override_reason_text: Optional[str] = None             # Free text — supplementary only
    physician_id: str = "DR-001"
