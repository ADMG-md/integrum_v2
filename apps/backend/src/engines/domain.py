"""
Re-exports domain models from the canonical location.

This module is kept for backward compatibility. All imports from
`src.engines.domain` continue to work but now resolve to `src.domain.models`.
"""

from src.domain.models import (
    safe_float,
    ClinicalEvidence,
    ActionItem,
    MedicationGap,
    AdjudicationResult,
    ObesityOnsetTrigger,
    DrugEntry,
    TraumaHistory,
    ClinicalHistory,
    Observation,
    Condition,
    MedicationStatement,
    DemographicsSchema,
    MetabolicPanelSchema,
    Encounter,
)

__all__ = [
    "safe_float",
    "ClinicalEvidence",
    "ActionItem",
    "MedicationGap",
    "AdjudicationResult",
    "ObesityOnsetTrigger",
    "DrugEntry",
    "TraumaHistory",
    "ClinicalHistory",
    "Observation",
    "Condition",
    "MedicationStatement",
    "DemographicsSchema",
    "MetabolicPanelSchema",
    "MetabolicPanelSchema",
    "Encounter",
]
