from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.eoss import EOSSStagingMotor
from src.engines.sarcopenia import SarcopeniaMonitorMotor
from src.engines.specialty.bio_age import BiologicalAgeMotor
from src.engines.specialty.lifestyle import Lifestyle360Motor
from src.engines.specialty.metabolic import MetabolicPrecisionMotor
from src.engines.specialty.metabolomics import DeepMetabolicProxyMotor
from src.engines.specialty.guidelines import ClinicalGuidelinesMotor
from src.engines.risk import (
    CVDHazardMotor,
    MarkovProgressionMotor,
)
from src.engines.obesity_master import ObesityMasterMotor, ObesityClinicalStoryInput
from src.engines.specialty.anthropometry import AnthropometryPrecisionMotor
from src.engines.specialty.endocrine import EndocrinePrecisionMotor
from src.engines.specialty.hypertension import HypertensionSecondaryMotor
from src.engines.specialty.inflammation import InflammationMotor
from src.engines.specialty.sleep_apnea import SleepApneaPrecisionMotor
from src.engines.specialty.stewardship import LaboratoryStewardshipMotor
from src.engines.specialty.lab_suggestion import LaboratorySuggestionMotor
from src.engines.specialty.functional_sarcopenia import FunctionalSarcopeniaMotor
from src.engines.specialty.fatty_liver import FLIMotor
from src.engines.specialty.visceral_adiposity import VAIMotor
from src.engines.specialty.cardiometabolic import CMIMotor
from src.engines.specialty.apob_ratio import ApoBApoA1Motor
from src.engines.specialty.lipid_risk import LipidRiskPrecisionMotor
from src.engines.specialty.hemodynamics import PulsePressureMotor
from src.engines.specialty.nafld_fibrosis import NFSMotor
from src.engines.specialty.glp1_monitor import GLP1MonitoringMotor
from src.engines.specialty.ace_integration import ACEScoreEngine
from src.engines.specialty.metformin_b12 import MetforminB12Motor
from src.engines.specialty.cancer_screening import CancerScreeningMotor
from src.engines.specialty.sglt2i_benefit import SGLT2iBenefitMotor
from src.engines.specialty.kfre import KFREMotor
from src.engines.specialty.charlson import CharlsonMotor
from src.engines.specialty.free_testosterone import FreeTestosteroneMotor
from src.engines.specialty.vitamin_d import VitaminDMotor
from src.engines.specialty.fried_frailty import FriedFrailtyMotor
from src.engines.specialty.tyg_bmi import TyGBMIMotor
from src.engines.specialty.cvd_reclassifier import CVDReclassifierMotor
from src.engines.specialty.womens_health import WomensHealthMotor
from src.engines.specialty.mens_health import MensHealthMotor
from src.engines.specialty.body_comp_trend import BodyCompositionTrendMotor
from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor
from src.engines.specialty.glp1_titration import GLP1TitrationMotor
from src.engines.specialty.drug_interaction import DrugInteractionMotor
from src.engines.protein_engine import ProteinEngineMotor
from src.engines.specialty.pediatric_nutrition import PediatricNutritionMotor
from src.engines.specialty.precision_nutrition import PrecisionNutritionMotor
from src.engines.specialty.pharma_precision import PharmaPrecisionMotor
from src.engines.specialty.psychometabolic_axis import PsychometabolicAxisMotor
from src.engines.specialty.pharmacogenomics import PharmacogenomicProxyMotor
from src.engines.domain import Encounter, AdjudicationResult
from typing import Dict, Any, List, Optional, Literal
import structlog
import re

logger = structlog.get_logger()

# --- Registered Motor Categories ---
PRIMARY_MOTORS = {
    # Core clinical engines
    "AcostaPhenotypeMotor": AcostaPhenotypeMotor,
    "EOSSStagingMotor": EOSSStagingMotor,
    "SarcopeniaMotor": SarcopeniaMonitorMotor,
    "BiologicalAgeMotor": BiologicalAgeMotor,
    "MetabolicPrecisionMotor": MetabolicPrecisionMotor,
    "DeepMetabolicProxyMotor": DeepMetabolicProxyMotor,
    "Lifestyle360Motor": Lifestyle360Motor,
    # Specialty engines
    "AnthropometryMotor": AnthropometryPrecisionMotor,
    "EndocrineMotor": EndocrinePrecisionMotor,
    "HypertensionMotor": HypertensionSecondaryMotor,
    "InflammationMotor": InflammationMotor,
    "SleepApneaMotor": SleepApneaPrecisionMotor,
    "LaboratoryStewardshipMotor": LaboratoryStewardshipMotor,
    "LaboratorySuggestionMotor": LaboratorySuggestionMotor,
    "FunctionalSarcopeniaMotor": FunctionalSarcopeniaMotor,
    # NAFLD screening + staging
    "FLIMotor": FLIMotor,
    "VAIMotor": VAIMotor,
    "CMIMotor": CMIMotor,
    "ApoBApoA1Motor": ApoBApoA1Motor,
    "PulsePressureMotor": PulsePressureMotor,
    "NFSMotor": NFSMotor,
    # Lipid risk (ACC/AHA 2026)
    "LipidRiskPrecisionMotor": LipidRiskPrecisionMotor,
    # Safety + screening
    "GLP1MonitoringMotor": GLP1MonitoringMotor,
    "ACEScoreEngine": ACEScoreEngine,
    "MetforminB12Motor": MetforminB12Motor,
    "CancerScreeningMotor": CancerScreeningMotor,
    "SGLT2iBenefitMotor": SGLT2iBenefitMotor,
    # Risk stratification + endocrine
    "KFREMotor": KFREMotor,
    "CharlsonMotor": CharlsonMotor,
    "FreeTestosteroneMotor": FreeTestosteroneMotor,
    "VitaminDMotor": VitaminDMotor,
    # Sprint 5: Clinical utility (data we already have)
    "FriedFrailtyMotor": FriedFrailtyMotor,
    "TyGBMIMotor": TyGBMIMotor,
    "CVDReclassifierMotor": CVDReclassifierMotor,
    # Sprint 6: Gender-specific health
    "WomensHealthMotor": WomensHealthMotor,
    "MensHealthMotor": MensHealthMotor,
    # Sprint 7: Therapy optimization
    "BodyCompositionTrendMotor": BodyCompositionTrendMotor,
    "ObesityPharmaEligibilityMotor": ObesityPharmaEligibilityMotor,
    "GLP1TitrationMotor": GLP1TitrationMotor,
    # Sprint 8: Medication safety
    "DrugInteractionMotor": DrugInteractionMotor,
    "ProteinEngineMotor": ProteinEngineMotor,
    # Sprint 9: Pediatric nutrition
    "PediatricNutritionMotor": PediatricNutritionMotor,
    # Sprint 10: Precision adult nutrition & pharma
    "PrecisionNutritionMotor": PrecisionNutritionMotor,
    "PharmaPrecisionMotor": PharmaPrecisionMotor,
    # Sprint 11: Psychometabolic Axis (Gut-Brain)
    "PsychometabolicAxisMotor": PsychometabolicAxisMotor,
    # Sprint 12: Precision Proxies
    "PharmacogenomicProxyMotor": PharmacogenomicProxyMotor,
}

GATED_MOTORS = {
    "CVDHazardMotor": CVDHazardMotor,
    "MarkovProgressionMotor": MarkovProgressionMotor,
}

AGGREGATOR_MOTORS = {
    "ObesityMasterMotor": ObesityMasterMotor,
    "ClinicalGuidelinesMotor": ClinicalGuidelinesMotor,
}


class SpecialtyRunner:
    """
    Singleton orchestrator for Specialty Micro-Engines.
    Executes multiple specialized clinical audits in two phases:
    1. Primary Engines (Independent)
    2. Aggregator Engines (Dependent on Primary Outputs)

    Clinical Mode (T1/T2 only):
    When clinical_mode=True, only T1 (validated clinical scores) and
    T2 (guideline-based rules) motors are executed. T3 (research proxies)
    and T4 (experimental) motors are skipped. This is the mode required
    for regulatory submissions and production clinical use.

    See: docs/qms/motor_evidence_registry.md for T1-T4 classification.
    """

    # T3/T4 motors excluded from clinical mode
    _RESEARCH_MOTORS = {
        "DeepMetabolicProxyMotor",  # T4: Experimental metabolic proxies
        "BiologicalAgeMotor",  # T3: Research proxy (PhenoAge)
        "ObesityMasterMotor",  # T3: Internal aggregation
    }

    _RESEARCH_MOTORS = {
        "DeepMetabolicProxyMotor",  # T4: Experimental metabolic proxies
        "BiologicalAgeMotor",  # T3: Research proxy (PhenoAge)
        "ObesityMasterMotor",  # T3: Internal aggregation
    }

    def run_all(
        self, encounter: Encounter, clinical_mode: bool = False
    ) -> Dict[str, Any]:
        results = {}
        h = encounter.history

        # 1. Primary Engines (Independent Phase)
        for name, motor_cls in PRIMARY_MOTORS.items():
            # Clinical mode: skip T3/T4 research/experimental motors
            if clinical_mode and name in self._RESEARCH_MOTORS:
                logger.info(
                    "motor_clinical_mode_skip",
                    motor=name,
                    reason="T3/T4 motor excluded",
                )
                continue

            # Instantiate per-request to avoid state leakage (C-02)
            motor = motor_cls()

            try:
                if hasattr(motor, "run"):
                    results[name] = motor.run(encounter)
                elif hasattr(motor, "compute"):
                    is_valid, reason = motor.validate(encounter)
                    if is_valid:
                        results[name] = motor.compute(encounter)

                # Contract validation: all motors must return AdjudicationResult
                if name in results and results[name] is not None:
                    if not isinstance(results[name], AdjudicationResult):
                        logger.error(
                            "motor_contract_violation",
                            motor=name,
                            expected="AdjudicationResult",
                            actual=type(results[name]).__name__,
                        )
            except Exception as e:
                logger.error(
                    "motor_execution_error", motor=name, error_type=type(e).__name__
                )
                # C-03: Do not silence clinical errors
                results[name] = AdjudicationResult(
                    calculated_value=f"System Error: {str(e)}",
                    confidence=0.0,
                    estado_ui="INDETERMINATE_LOCKED"
                )

        # 2. Risk Engines (Gated / Experimental Phase)
        cvd_risk_category = None
        for name, motor_cls in GATED_MOTORS.items():
            try:
                # Gate: CVDHazardMotor runs only if patient has CVD risk factors
                if name == "CVDHazardMotor":
                    has_risk = (
                        (
                            h
                            and (
                                h.has_type2_diabetes
                                or h.has_hypertension
                                or h.has_dyslipidemia
                            )
                        )
                        or encounter.bmi >= 30
                        or (
                            encounter.demographics.age_years
                            and encounter.demographics.age_years >= 40
                        )
                    )
                    if not has_risk:
                        logger.info(
                            "motor_gated_skip", motor=name, reason="No CVD risk factors"
                        )
                        continue

                # Gate: MarkovProgressionMotor runs only if DM2 or prediabetes
                if name == "MarkovProgressionMotor":
                    has_dm = (
                        encounter.has_condition("E11")
                        or encounter.has_condition("E11.9")
                        or (h and h.has_type2_diabetes)
                        or (h and h.has_prediabetes)
                    )
                    if not has_dm:
                        logger.info(
                            "motor_gated_skip",
                            motor=name,
                            reason="No diabetes/prediabetes",
                        )
                        continue

                # Instantiate per-request
                motor = motor_cls()

                if hasattr(motor, "run"):
                    res = motor.run(encounter)
                    results[name] = res
                    if name == "CVDHazardMotor" and hasattr(res, "risk_category"):
                        cvd_risk_category = res.risk_category
            except Exception as e:
                logger.warning(
                    "gated_motor_error", motor=name, error_type=type(e).__name__
                )
                results[name] = AdjudicationResult(
                    calculated_value=f"System Error: {str(e)}",
                    confidence=0.0,
                    estado_ui="INDETERMINATE_LOCKED"
                )

        # 3. Aggregator Engines (Decision Support Phase)
        if "AcostaPhenotypeMotor" in results and "EOSSStagingMotor" in results:
            try:
                # Instantiate per-request
                ob_motor = AGGREGATOR_MOTORS["ObesityMasterMotor"]()
                if clinical_mode:
                    logger.info(
                        "motor_clinical_mode_skip",
                        motor="ObesityMasterMotor",
                        reason="T3 motor excluded from clinical mode",
                    )
                else:
                    ob_input = self._build_obesity_input(
                        encounter, results, cvd_risk_category
                    )
                    results["ObesityMasterMotor"] = ob_motor(ob_input)
            except Exception as e:
                logger.error(
                    "aggregator_error",
                    motor="ObesityMasterMotor",
                    error_type=type(e).__name__,
                )
                results["ObesityMasterMotor"] = AdjudicationResult(
                    calculated_value=f"System Error: {str(e)}",
                    confidence=0.0,
                    estado_ui="INDETERMINATE_LOCKED"
                )

        if "ClinicalGuidelinesMotor" in AGGREGATOR_MOTORS:
            try:
                gui_motor = AGGREGATOR_MOTORS["ClinicalGuidelinesMotor"]()
                context = {"cvd_risk_category": cvd_risk_category}
                results["ClinicalGuidelinesMotor"] = gui_motor.compute(
                    encounter, context
                )
            except Exception as e:
                logger.error(
                    "aggregator_error",
                    motor="ClinicalGuidelinesMotor",
                    error_type=type(e).__name__,
                )
                results["ClinicalGuidelinesMotor"] = AdjudicationResult(
                    calculated_value=f"System Error: {str(e)}",
                    confidence=0.0,
                    estado_ui="INDETERMINATE_LOCKED"
                )

        return results

    def get_all_motors(self) -> List[Any]:
        for name, motor_cls in PRIMARY_MOTORS.items():
            if name not in self._primary_motors:
                self._primary_motors[name] = motor_cls()
        for name, motor_cls in AGGREGATOR_MOTORS.items():
            if name not in self._aggregator_motors:
                self._aggregator_motors[name] = motor_cls()
        for name, motor_cls in GATED_MOTORS.items():
            if name not in self._gated_motors:
                self._gated_motors[name] = motor_cls()
                
        return (
            list(self._primary_motors.values())
            + list(self._aggregator_motors.values())
            + list(self._gated_motors.values())
        )

    def _build_obesity_input(
        self,
        encounter: Encounter,
        primary_results: Dict[str, Any],
        cvd_risk_category: Optional[
            Literal["low", "borderline", "intermediate", "high"]
        ] = None,
    ) -> ObesityClinicalStoryInput:
        acosta = primary_results.get("AcostaPhenotypeMotor")
        eoss = primary_results.get("EOSSStagingMotor")
        sarcopenia = primary_results.get("SarcopeniaMotor")
        func_sarcopenia = primary_results.get("FunctionalSarcopeniaMotor")

        stage = 0
        if eoss:
            match = re.search(r"Stage\s+(\d+)", eoss.calculated_value)
            if match:
                stage = int(match.group(1))

        sarcopenia_risk = "low"
        if sarcopenia:
            if sarcopenia.metadata.get("alerta_roja"):
                sarcopenia_risk = "high"
            elif (
                sarcopenia.metadata.get("asmi")
                and sarcopenia.estado_ui == "PROBABLE_WARNING"
            ):
                sarcopenia_risk = "moderate"

        if func_sarcopenia and func_sarcopenia.estado_ui == "CONFIRMED_ACTIVE":
            if sarcopenia_risk == "low":
                sarcopenia_risk = "moderate"
            elif sarcopenia_risk in ("moderate", "high"):
                sarcopenia_risk = "high"

        waist_obs = encounter.get_observation("WAIST-001")
        waist_cm = float(waist_obs.value) if waist_obs else 0.0

        metabolic_proxies = primary_results.get("DeepMetabolicProxyMotor")
        nutrition = primary_results.get("PrecisionNutritionMotor")
        pharma = primary_results.get("PharmaPrecisionMotor")

        return ObesityClinicalStoryInput(
            acosta_phenotype=acosta.calculated_value if acosta else "Unknown",
            eoss_stage=stage,
            sarcopenia_risk=sarcopenia_risk,
            bmi_kg_m2=encounter.bmi or 0.0,
            waist_cm=waist_cm,
            cvd_risk_category=cvd_risk_category,
            metabolic_proxies_summary=metabolic_proxies.calculated_value
            if metabolic_proxies
            else None,
            metabolic_proxies_active=metabolic_proxies.estado_ui == "CONFIRMED_ACTIVE"
            if metabolic_proxies
            else False,
            nutrition_precision_summary=nutrition.calculated_value if nutrition else None,
            pharma_precision_summary=pharma.calculated_value if pharma else None,
        )


# Export a singleton instance
specialty_runner = SpecialtyRunner()
