from pydantic import BaseModel
from typing import List
from src.engines.base_models import AdjudicationResult, ClinicalEvidence
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class KleiberBMRInput(BaseModel):
    weight_kg: float


class KleiberBMROutput(AdjudicationResult):
    bmr_kcal_day: float = 0.0
    explanation: str = ""  # type: ignore[assignment]

    # AdjudicationResult standard fields overrides
    calculated_value: str = ""
    confidence: float = 0.8
    evidence: List[ClinicalEvidence] = []


from src.engines.domain import Encounter
from typing import Tuple


class KleiberBMRMotor:
    ENGINE_NAME = "KleiberBMRMotor"
    ENGINE_VERSION = "0.2.0"

    def get_version_hash(self) -> str:
        return "0.2.0"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        if not encounter.bmi:
            return False, "BMR requires weight/height."
        return True, ""

    def __call__(self, weight_kg: float) -> KleiberBMROutput:
        # Legacy DTO-style wrapper
        return self._execute_calculation(weight_kg)

    def compute(self, encounter: Encounter) -> KleiberBMROutput:
        weight_obs = encounter.get_observation("29463-7") or encounter.get_observation(
            "W-001"
        )
        if not weight_obs:
            # Although validate passed, safe-check
            return KleiberBMROutput(
                calculated_value="ERROR",
                confidence=0.0,
                explanation="Missing Weight Obs",
                bmr_kcal_day=0.0,
            )

        return self._execute_calculation(float(weight_obs.value))

    KLEIBER_SCALING_FACTOR = 70.0
    KLEIBER_EXPONENT = 0.75

    def _execute_calculation(self, weight_kg: float) -> KleiberBMROutput:
        # Kleiber’s law: BMR ≈ 70 * weight^0.75 (clásico en humanos, ajustable)
        bmr = self.KLEIBER_SCALING_FACTOR * (weight_kg**self.KLEIBER_EXPONENT)
        explanation = (
            f"BMR estimado con ley de Kleiber ({self.KLEIBER_SCALING_FACTOR} * peso^{self.KLEIBER_EXPONENT}). "
            "Uso: referencia metabólica, no prescripción calórica directa."
        )
        return KleiberBMROutput(
            bmr_kcal_day=round(bmr),
            calculated_value=f"{round(bmr)} kcal/día",
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PEER_REVIEWED],  # Kleiber's law approximation
            explanation=explanation,
            estado_ui="CONFIRMED_ACTIVE",
            evidence=[
                ClinicalEvidence(
                    type="Observation",
                    code="29463-7",
                    value=weight_kg,
                    display="Peso corporal",
                )
            ],
        )
