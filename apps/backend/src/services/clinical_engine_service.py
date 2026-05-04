"""
ClinicalIntelligenceBridge — DT-02 refactor.

BEFORE: Reimplementaba BMI, WHtR, HOMA-IR, TyG, VAI, FIB-4 inline.
        Dos fuentes de verdad matemática → riesgo de divergencia silenciosa.

AFTER:  Delega TODOS los cálculos a calculators.py (SSOT).
        Este módulo solo es responsable de inyectar los resultados como
        Observation objects en el encounter para consumo de los motores.
"""
from src.engines.domain import Encounter, Observation
from src.domain.calculators import MetabolicIndices, AnthropometricData, HepaticIndices
from typing import Optional

class ClinicalIntelligenceBridge:
    """
    Enriches an Encounter with pre-computed clinical indices before engine execution.
    All math is delegated to calculators.py (Single Source of Truth).
    """

    BMI    = "CALC-BMI"
    WHTR   = "CALC-WHTR"
    HOMA_IR = "CALC-HOMA-IR"
    TYG    = "CALC-TYG"
    VAI    = "CALC-VAI"
    FIB4   = "CALC-FIB4"

    WEIGHT = "29463-7"
    HEIGHT = "8302-2"
    WAIST = "WAIST-001"
    HIP = "HIP-001"
    GLUCOSE = "GLUC-001"
    TRIGLYCERIDES = "TG-001"
    AST = "29230-0"
    ALT = "22538-3"
    PLT = "PLT-001"
    AGE = "AGE-001"

    def enrich(self, encounter: Encounter) -> Encounter:
        """
        Single entry point. Computes all indices via calculators.py and
        injects them as synthetic Observation objects.
        """
        # 1. Anthropometry
        try:
            anthr = AnthropometricData.from_encounter(encounter)
            if anthr.bmi is not None:
                self._add_obs(encounter, self.BMI, anthr.bmi, "kg/m²")
            if anthr.waist_to_height is not None:
                self._add_obs(encounter, self.WHTR, anthr.waist_to_height, "Ratio")
        except Exception:
            pass

        # 2. Metabolic
        try:
            meta = MetabolicIndices.from_encounter(encounter)
            if meta.homa_ir is not None:
                self._add_obs(encounter, self.HOMA_IR, round(meta.homa_ir, 2), "Score")
            if meta.tyg_index is not None:
                self._add_obs(encounter, self.TYG, round(meta.tyg_index, 2), "Score")
            if meta.visceral_adiposity_index is not None:
                self._add_obs(encounter, self.VAI, meta.visceral_adiposity_index, "Score")
        except Exception:
            pass

        # 3. Hepatic
        try:
            hep = HepaticIndices.from_encounter(encounter)
            if hep.fib4 is not None:
                self._add_obs(encounter, self.FIB4, hep.fib4, "Score")
        except Exception:
            pass

        return encounter

    @staticmethod
    def _add_obs(encounter: Encounter, code: str, value: float, unit: str) -> None:
        """Injects a synthetic Observation only if not already present."""
        if encounter.get_observation(code) is None:
            encounter.observations.append(
                Observation(
                    code=code,
                    value=value,
                    unit=unit,
                    category="Clinical",
                    metadata={"source": "calculators-ssot"},
                )
            )

clinical_bridge = ClinicalIntelligenceBridge()
