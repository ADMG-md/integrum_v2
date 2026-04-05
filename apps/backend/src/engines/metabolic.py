from pydantic import BaseModel
from typing import List
from src.engines.base_models import AdjudicationResult, ClinicalEvidence


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

    def _execute_calculation(self, weight_kg: float) -> KleiberBMROutput:
        # Kleiber’s law: BMR ≈ 70 * weight^0.75 (clásico en humanos, ajustable)
        bmr = 70.0 * (weight_kg**0.75)
        explanation = (
            "BMR estimado con ley de Kleiber (70 * peso^0.75). "
            "Uso: referencia metabólica, no prescripción calórica directa."
        )
        return KleiberBMROutput(
            bmr_kcal_day=round(bmr),
            calculated_value=f"{round(bmr)} kcal/día",
            confidence=0.85,
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
