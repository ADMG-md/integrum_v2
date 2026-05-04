"""
Clinical Confidence Scoring Rubric for Integrum CDSS

Evidence-based confidence levels aligned with GRADE methodology.

Usage:
    from src.engines.confidence_standards import CONFIDENCE_LEVELS
    confidence = CONFIDENCE_LEVELS["ESTABLISHED_GUIDELINE"]

References:
    - GRADE Working Group. BMJ 2004;328:1490-1494.
    - Balshem et al. J Clin Oncol 2011;29:2537-2544.
"""

from enum import Enum
from typing import Final


class ConfidenceLevel(str, Enum):
    """Standardized confidence levels with clinical justification."""
    ESTABLISHED_GUIDELINE = "ESTABLISHED_GUIDELINE"
    VALIDATED_BIOMARKER = "VALIDATED_BIOMARKER"
    PEER_REVIEWED = "PEER_REVIEWED"
    INDIRECT_EVIDENCE = "INDIRECT_EVIDENCE"
    PROXY_MARKER = "PROXY_MARKER"


CONFIDENCE_VALUES: Final[dict[ConfidenceLevel, float]] = {
    # Established clinical guidelines (GRADE High/++++)
    # - Consensus from multiple RCTs or meta-analyses
    # - Adopted by major societies (ADA, AHA, EASL, etc.)
    ConfidenceLevel.ESTABLISHED_GUIDELINE: 0.95,

    # Validated biomarkers with strong observational evidence (GRADE Moderate/+++)
    # - Prospective cohort studies with consistent results
    # - Well-established clinical utility
    ConfidenceLevel.VALIDATED_BIOMARKER: 0.90,

    # Peer-reviewed literature with moderate evidence (GRADE Moderate/+++)
    # - Multiple studies showing consistent direction of effect
    # - Some limitations in study design or population
    ConfidenceLevel.PEER_REVIEWED: 0.85,

    # Indirect evidence or surrogate markers (GRADE Low/++)
    # - Biological plausibility with limited clinical validation
    # - Used when direct measures unavailable
    ConfidenceLevel.INDIRECT_EVIDENCE: 0.75,

    # Proxy markers with weak but non-zero predictive value (GRADE Very Low/+)
    # - Single studies or mechanistic reasoning only
    # - High uncertainty, included for completeness
    ConfidenceLevel.PROXY_MARKER: 0.60,
}

# Error/failure states
CONFIDENCE_UNKNOWN: Final[float] = 0.0
CONFIDENCE_MISSING_DATA: Final[float] = 0.0
