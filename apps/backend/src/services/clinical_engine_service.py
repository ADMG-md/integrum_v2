"""
ClinicalIntelligenceBridge — DT-02 refactor.

BEFORE: Reimplementaba BMI, WHtR, HOMA-IR, TyG, VAI, FIB-4 inline.
        Dos fuentes de verdad matemática → riesgo de divergencia silenciosa.

AFTER:  Delega TODOS los cálculos a calculators.py (SSOT).
        Este módulo solo es responsable de inyectar los resultados como
        Observation objects en el encounter para consumo de los motores.
"""
from src.engines.domain import Encounter, Observation
from src.engines.calculators import MetabolicIndices, AnthropometricData, LipidProfile
from typing import Optional
import math


class ClinicalIntelligenceBridge:
    """
    Enriches an Encounter with pre-computed clinical indices before engine execution.
    All math is delegated to calculators.py (Single Source of Truth).
    """

    # Derived observation codes injected into the encounter
    BMI    = "CALC-BMI"
    WHTR   = "CALC-WHTR"
    HOMA_IR = "CALC-HOMA-IR"
    TYG    = "CALC-TYG"
    VAI    = "CALC-VAI"
    FIB4   = "CALC-FIB4"

    # Raw lab codes still needed for FIB-4 (not in calculators yet)
    AST = "29230-0"
    ALT = "22538-3"
    PLT = "PLT-001"
    AGE = "AGE-001"

    def enrich(self, encounter: Encounter) -> Encounter:
        """
        Single entry point. Computes all indices via calculators.py and
        injects them as synthetic Observation objects.
        """
        self._inject_anthropometry(encounter)
        self._inject_metabolic(encounter)
        self._inject_vai(encounter)
        self._inject_fib4(encounter)
        return encounter

    # ── Anthropometry (delegates to AnthropometricData) ──────────────────────

    def _inject_anthropometry(self, encounter: Encounter) -> None:
        try:
            data = AnthropometricData.from_encounter(encounter)
        except Exception:
            return

        if data.bmi is not None:
            self._add_obs(encounter, self.BMI, data.bmi, "kg/m²")

        if data.waist_to_height is not None:
            self._add_obs(encounter, self.WHTR, data.waist_to_height, "Ratio")

    # ── Metabolic Indices (delegates to MetabolicIndices) ────────────────────

    def _inject_metabolic(self, encounter: Encounter) -> None:
        try:
            data = MetabolicIndices.from_encounter(encounter)
        except Exception:
            return

        if data.homa_ir is not None:
            self._add_obs(encounter, self.HOMA_IR, round(data.homa_ir, 2), "Score")

        if data.tyg_index is not None:
            self._add_obs(encounter, self.TYG, round(data.tyg_index, 2), "Score")

    # ── VAI (delegates to LipidProfile geometry + anthropometry) ─────────────

    def _inject_vai(self, encounter: Encounter) -> None:
        """
        Visceral Adiposity Index.
        SOURCE: Amato MC et al. Clin Endocrinol (Oxf). 2010;72(5):658-65.
        Men:   VAI = (WC/(39.68+1.88×BMI)) × (TG/1.03) × (1.31/HDL)
        Women: VAI = (WC/(36.58+1.89×BMI)) × (TG/0.81) × (1.52/HDL)
        Units: WC in cm, BMI in kg/m², TG in mmol/L, HDL in mmol/L
        """
        try:
            anthr = AnthropometricData.from_encounter(encounter)
            waist = anthr.waist_to_height  # need raw waist — get directly
        except Exception:
            return

        waist_obs = encounter.get_observation("WAIST-001")
        bmi_obs = encounter.get_observation(self.BMI)  # already injected above
        tg = encounter.cardio_panel.triglycerides_mg_dl
        hdl = encounter.cardio_panel.hdl_mg_dl
        gender = encounter.demographics.gender or ""

        if not all([waist_obs, bmi_obs, tg, hdl]) or hdl <= 0:
            return

        try:
            wc = float(waist_obs.value)
            bmi_val = float(bmi_obs.value)
            # Convert mg/dL → mmol/L for VAI formula
            tg_mmol = tg / 88.57
            hdl_mmol = hdl / 38.67

            if gender.lower() in ("male", "m"):
                vai = (wc / (39.68 + 1.88 * bmi_val)) * (tg_mmol / 1.03) * (1.31 / hdl_mmol)
            else:
                vai = (wc / (36.58 + 1.89 * bmi_val)) * (tg_mmol / 0.81) * (1.52 / hdl_mmol)

            self._add_obs(encounter, self.VAI, round(vai, 2), "Score")
        except (ValueError, ZeroDivisionError, TypeError):
            pass

    # ── FIB-4 (not yet in calculators.py) ────────────────────────────────────

    def _inject_fib4(self, encounter: Encounter) -> None:
        """
        FIB-4 Index: (Age × AST) / (PLT × √ALT)
        SOURCE: Sterling RK et al. Hepatology. 2006;43(6):1317-25.
        """
        ast_obs = encounter.get_observation(self.AST)
        alt_obs = encounter.get_observation(self.ALT)
        plt_obs = encounter.get_observation(self.PLT)
        age_obs = encounter.get_observation(self.AGE)

        if not all([ast_obs, alt_obs, plt_obs, age_obs]):
            return

        try:
            alt_val = float(alt_obs.value)
            plt_val = float(plt_obs.value)
            if alt_val <= 0 or plt_val <= 0:
                return
            fib4 = (float(age_obs.value) * float(ast_obs.value)) / (plt_val * math.sqrt(alt_val))
            self._add_obs(encounter, self.FIB4, round(fib4, 2), "Score")
        except (ValueError, ZeroDivisionError, TypeError):
            pass

    # ── Helpers ──────────────────────────────────────────────────────────────

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
