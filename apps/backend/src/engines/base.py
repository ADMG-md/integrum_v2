from abc import ABC, abstractmethod
from typing import Tuple, List
from src.engines.domain import Encounter, AdjudicationResult
import inspect
import hashlib

class BaseClinicalMotor(ABC):
    """
    Standard interface for all clinical engines.
    Ensures deterministic output and regulatory compliance (IEC 62304).
    """

    REQUIREMENT_ID: str = "GENERIC-001"

    @abstractmethod
    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        """
        Verifies if the encounter has the minimum necessary data.
        Returns (is_valid, error_message).
        """
        pass

    @abstractmethod
    def compute(self, encounter: Encounter) -> AdjudicationResult:
        """
        Pure deterministic computation of the clinical metric.
        """
        pass

    def get_version_hash(self) -> str:
        """Returns a hash of the engine source code for Audit Trail (IEC 62304)."""
        source = inspect.getsource(self.__class__)
        return hashlib.sha256(source.encode()).hexdigest()

    def explain(self, result: AdjudicationResult) -> str:
        """
        Generates a standard technical narrative from the adjudication result.
        """
        evidence_str = ", ".join([
            f"{ev.type}[{ev.code}]={ev.value}" 
            for ev in result.evidence
        ])
        return f"Calculated {result.calculated_value} based on: {evidence_str}"
