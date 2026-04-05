"""
Re-exports base models from the canonical location.

This module is kept for backward compatibility. All imports from
`src.engines.base_models` continue to work but now resolve to `src.domain.models`.
"""

from src.domain.models import (
    ClinicalEvidence,
    ActionItem,
    MedicationGap,
    AdjudicationResult,
)

__all__ = [
    "ClinicalEvidence",
    "ActionItem",
    "MedicationGap",
    "AdjudicationResult",
]
