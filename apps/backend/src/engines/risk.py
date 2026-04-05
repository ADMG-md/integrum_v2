from pydantic import BaseModel
from typing import Dict, Any, Optional, Literal
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
import math


# ============================================================
# CVDHazardMotor — ACC/AHA Pooled Cohort Equations (US)
# ============================================================


class CVDHazardInput(BaseModel):
    age_years: float
    sex: Literal["male", "female"]
    race: Literal["white", "aa"] = "white"
    total_cholesterol_mg_dl: float
    hdl_mg_dl: float
    sbp_mm_hg: float
    sbp_treated: bool = False
    smoker: bool = False
    diabetic: bool = False


class CVDHazardOutput(AdjudicationResult):
    risk_pct_10y: Optional[float] = None
    risk_category: Optional[Literal["low", "borderline", "intermediate", "high"]] = None


class CVDHazardMotor:
    """
    10-year ASCVD risk using ACC/AHA Pooled Cohort Equations.
    """

    REQUIREMENT_ID = "CVDHAZARD-PCE"
    ENGINE_NAME = "CVDHazardMotor"
    ENGINE_VERSION = "1.0.0"

    def get_version_hash(self) -> str:
        return f"{self.ENGINE_NAME}-v{self.ENGINE_VERSION}"

    def run(
        self, encounter: Encounter, context: Optional[Dict[str, Any]] = None
    ) -> CVDHazardOutput:
        d = encounter.demographics
        sbp_obs = encounter.get_observation("8480-6")
        sbp = safe_float(sbp_obs.value) if sbp_obs else 0.0
        age = d.age_years or 50.0
        is_aa = False  # Would need explicit race field
        is_treated = encounter.has_condition("I10")
        smoker = encounter.metadata.get("smoker", False)
        diabetic = encounter.history.has_type2_diabetes if encounter.history else False

        tc = encounter.cardio_panel.total_cholesterol_mg_dl
        hdl = encounter.cardio_panel.hdl_mg_dl
        if not tc or not hdl:
            return CVDHazardOutput(
                risk_pct_10y=None,
                risk_category=None,
                calculated_value="Datos insuficientes para ASCVD",
                confidence=0.0,
                explanation="Se requieren colesterol total y HDL para calcular riesgo ASCVD.",
                estado_ui="INDETERMINATE_LOCKED",
                evidence=[],
            )

        data = CVDHazardInput(
            age_years=age,
            sex=d.gender if d.gender in ("male", "female") else "male",
            race="aa" if is_aa else "white",
            total_cholesterol_mg_dl=tc,
            hdl_mg_dl=hdl,
            sbp_mm_hg=sbp,
            sbp_treated=is_treated,
            smoker=smoker,
            diabetic=diabetic,
        )
        return self(data)

    def __call__(self, data: CVDHazardInput) -> CVDHazardOutput:
        risk = self._calculate_pce(data)
        if risk < 5:
            cat = "low"
        elif risk < 7.5:
            cat = "borderline"
        elif risk < 20:
            cat = "intermediate"
        else:
            cat = "high"

        return CVDHazardOutput(
            risk_pct_10y=risk,
            risk_category=cat,
            calculated_value=f"ASCVD 10y: {risk}% ({cat})",
            confidence=0.88,
            explanation=f"Riesgo ASCVD a 10 años (ACC/AHA PCE): {risk}%. Categoría: {cat}.",
            estado_ui="CONFIRMED_ACTIVE"
            if cat in ("intermediate", "high")
            else "INDETERMINATE_LOCKED",
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="ASCVD-10Y",
                    value=risk,
                    threshold="<7.5%",
                    display="ASCVD 10-Year Risk",
                )
            ],
        )

    def _calculate_pce(self, d: CVDHazardInput) -> float:
        ln_age = math.log(d.age_years)
        ln_tot = math.log(d.total_cholesterol_mg_dl)
        ln_hdl = math.log(d.hdl_mg_dl)
        ln_sbp = math.log(d.sbp_mm_hg)
        is_smoker = 1.0 if d.smoker else 0.0
        is_diabetic = 1.0 if d.diabetic else 0.0
        is_treated = d.sbp_treated
        is_aa = d.race == "aa"

        if d.sex == "female" and not is_aa:
            coef_age, coef_age2, coef_tot_chol = 12.344, 0.0, 11.853
            coef_age_tot_chol, coef_hdl, coef_age_hdl = -2.664, -7.990, 1.769
            coef_sbp_untreated = 1.764 if not is_treated else 0.0
            coef_age_sbp_untreated = 0.0
            coef_sbp_treated = 1.797 if is_treated else 0.0
            coef_age_sbp_treated = 0.0
            coef_smoker, coef_age_smoker = 7.837, -1.795
            coef_diabetes, mean_sum, baseline = 0.658, 61.18, 0.9144
        elif d.sex == "female" and is_aa:
            coef_age, coef_age2, coef_tot_chol = 17.114, 0.0, 0.940
            coef_age_tot_chol, coef_hdl, coef_age_hdl = 0.0, -18.920, 4.475
            coef_sbp_untreated = 27.820 if not is_treated else 0.0
            coef_age_sbp_untreated = -6.087 if not is_treated else 0.0
            coef_sbp_treated = 29.291 if is_treated else 0.0
            coef_age_sbp_treated = -6.432 if is_treated else 0.0
            coef_smoker, coef_age_smoker = 0.691, 0.0
            coef_diabetes, mean_sum, baseline = 0.874, 86.61, 0.9533
        elif d.sex == "male" and not is_aa:
            coef_age, coef_age2, coef_tot_chol = 12.344, 0.0, 11.853
            coef_age_tot_chol, coef_hdl, coef_age_hdl = -2.664, -7.990, 1.769
            coef_sbp_untreated = 1.764 if not is_treated else 0.0
            coef_age_sbp_untreated = 0.0
            coef_sbp_treated = 1.797 if is_treated else 0.0
            coef_age_sbp_treated = 0.0
            coef_smoker, coef_age_smoker = 7.837, -1.795
            coef_diabetes, mean_sum, baseline = 0.658, 61.18, 0.9144
        else:
            coef_age, coef_age2, coef_tot_chol = 2.469, 0.0, 0.302
            coef_age_tot_chol, coef_hdl, coef_age_hdl = 0.0, -0.307, 0.0
            coef_sbp_untreated = 1.809 if not is_treated else 0.0
            coef_age_sbp_untreated = 0.0
            coef_sbp_treated = 1.916 if is_treated else 0.0
            coef_age_sbp_treated = 0.0
            coef_smoker, coef_age_smoker = 0.549, 0.0
            coef_diabetes, mean_sum, baseline = 0.645, 19.54, 0.8954

        ind_sum = (
            coef_age * ln_age
            + coef_age2 * (ln_age**2)
            + coef_tot_chol * ln_tot
            + coef_age_tot_chol * ln_age * ln_tot
            + coef_hdl * ln_hdl
            + coef_age_hdl * ln_age * ln_hdl
            + coef_sbp_untreated * ln_sbp
            + coef_age_sbp_untreated * ln_age * ln_sbp
            + coef_sbp_treated * ln_sbp
            + coef_age_sbp_treated * ln_age * ln_sbp
            + coef_smoker * is_smoker
            + coef_age_smoker * ln_age * is_smoker
            + coef_diabetes * is_diabetic
        )

        risk = 1.0 - (baseline ** math.exp(ind_sum - mean_sum))
        return round(max(risk * 100, 0), 2)


# ============================================================
# MarkovProgressionMotor — Diabetes Progression
# ============================================================


class MarkovProgressionInput(BaseModel):
    current_state: Literal["no_dm", "pre_dm", "dm", "dm_complications"]
    age_years: float
    bmi_kg_m2: float
    hba1c_percent: float


class MarkovProgressionOutput(AdjudicationResult):
    status: str
    state_probabilities_5y: Optional[Dict[str, float]] = None
    state_probabilities_10y: Optional[Dict[str, float]] = None

    calculated_value: str = ""
    confidence: float = 0.0
    evidence: list[ClinicalEvidence] = []


class MarkovProgressionMotor:
    """
    Markov Model for Diabetes Progression.

    Predicts 5-year and 10-year probability of transitioning between:
    - Normal glucose → Prediabetes → Type 2 DM → DM with complications

    Annual transition rates calibrated from:
    - UKPDS (United Kingdom Prospective Diabetes Study)
    - DPP (Diabetes Prevention Program)
    - Look AHEAD trial (remission rates)
    - ADA Standards of Care 2024

    Modifiers:
    - BMI > 30: +50% progression rate to DM
    - HbA1c > 6.0%: +100% progression rate
    - Age > 60: +30% complication rate

    REQUIREMENT_ID: MARKOV-DM-PROGRESSION
    """

    REQUIREMENT_ID = "MARKOV-DM-PROGRESSION"
    ENGINE_NAME = "MarkovProgressionMotor"
    ENGINE_VERSION = "1.0.0"

    BASE_TRANSITION_MATRIX = {
        "no_dm": {"no_dm": 0.96, "pre_dm": 0.04, "dm": 0.0, "dm_complications": 0.0},
        "pre_dm": {"no_dm": 0.08, "pre_dm": 0.82, "dm": 0.10, "dm_complications": 0.0},
        "dm": {"no_dm": 0.0, "pre_dm": 0.03, "dm": 0.89, "dm_complications": 0.08},
        "dm_complications": {
            "no_dm": 0.0,
            "pre_dm": 0.0,
            "dm": 0.82,
            "dm_complications": 0.18,
        },
    }

    def get_version_hash(self) -> str:
        return f"{self.ENGINE_NAME}-v{self.ENGINE_VERSION}"

    def run(
        self, encounter: "Encounter", context: Optional[Dict[str, Any]] = None
    ) -> MarkovProgressionOutput:
        from src.engines.domain import safe_float

        hba1c = encounter.metabolic_panel.hba1c_percent
        age_obs = encounter.get_observation("AGE-001")
        age = safe_float(age_obs.value) if age_obs else 50.0
        bmi = encounter.bmi or 25.0

        if hba1c is None:
            return MarkovProgressionOutput(
                status="insufficient_data",
                calculated_value="HbA1c no disponible",
                confidence=0.0,
                explanation="Se requiere HbA1c para estimar progresión de diabetes.",
                estado_ui="INDETERMINATE_LOCKED",
            )

        if hba1c < 5.7:
            current_state = "no_dm"
        elif hba1c < 6.5:
            current_state = "pre_dm"
        else:
            has_complications = (
                encounter.has_condition("E11.2")
                or encounter.has_condition("E11.3")
                or encounter.has_condition("E11.4")
                or encounter.has_condition("E11.5")
                or encounter.has_condition("I25")
                or encounter.has_condition("N18")
            )
            current_state = "dm_complications" if has_complications else "dm"

        data = MarkovProgressionInput(
            current_state=current_state,
            age_years=age,
            bmi_kg_m2=bmi,
            hba1c_percent=hba1c,
        )
        return self(data)

    def __call__(
        self, data: Optional[MarkovProgressionInput]
    ) -> MarkovProgressionOutput:
        import copy

        if data is None:
            return MarkovProgressionOutput(
                status="insufficient_data",
                calculated_value="Datos insuficientes",
                confidence=0.0,
                explanation="Se requieren: estado actual, edad, BMI, HbA1c.",
                estado_ui="INDETERMINATE_LOCKED",
            )

        matrix = copy.deepcopy(self.BASE_TRANSITION_MATRIX)

        bmi_factor = 1.5 if data.bmi_kg_m2 >= 30 else 1.0
        hba1c_factor = 2.0 if data.hba1c_percent >= 6.0 else 1.0
        age_factor = 1.3 if data.age_years >= 60 else 1.0

        if data.current_state == "pre_dm":
            dm_rate = matrix["pre_dm"]["dm"] * bmi_factor * hba1c_factor
            matrix["pre_dm"]["dm"] = min(dm_rate, 0.25)
            matrix["pre_dm"]["pre_dm"] = (
                1.0 - matrix["pre_dm"]["no_dm"] - matrix["pre_dm"]["dm"]
            )

        if data.current_state == "dm":
            comp_rate = matrix["dm"]["dm_complications"] * bmi_factor * age_factor
            matrix["dm"]["dm_complications"] = min(comp_rate, 0.20)
            matrix["dm"]["dm"] = (
                1.0 - matrix["dm"]["pre_dm"] - matrix["dm"]["dm_complications"]
            )

        if data.current_state == "dm_complications":
            prog_rate = matrix["dm_complications"]["dm_complications"] * age_factor
            matrix["dm_complications"]["dm_complications"] = min(prog_rate, 0.30)
            matrix["dm_complications"]["dm"] = (
                1.0 - matrix["dm_complications"]["dm_complications"]
            )

        states = ["no_dm", "pre_dm", "dm", "dm_complications"]
        probs = {s: 0.0 for s in states}
        probs[data.current_state] = 1.0

        for _ in range(5):
            new_probs = {s: 0.0 for s in states}
            for from_state in states:
                for to_state in states:
                    new_probs[to_state] += (
                        probs[from_state] * matrix[from_state][to_state]
                    )
            probs = new_probs

        probs_5y = {k: round(v, 3) for k, v in probs.items()}

        probs = {s: 0.0 for s in states}
        probs[data.current_state] = 1.0
        for _ in range(10):
            new_probs = {s: 0.0 for s in states}
            for from_state in states:
                for to_state in states:
                    new_probs[to_state] += (
                        probs[from_state] * matrix[from_state][to_state]
                    )
            probs = new_probs

        probs_10y = {k: round(v, 3) for k, v in probs.items()}

        dm_risk_5y = probs_5y.get("dm", 0) + probs_5y.get("dm_complications", 0)
        dm_risk_10y = probs_10y.get("dm", 0) + probs_10y.get("dm_complications", 0)

        state_labels = {
            "no_dm": "Glucosa normal",
            "pre_dm": "Prediabetes",
            "dm": "Diabetes tipo 2",
            "dm_complications": "Diabetes con complicaciones",
        }

        if data.current_state == "no_dm":
            estado = "INDETERMINATE_LOCKED" if dm_risk_5y < 0.05 else "PROBABLE_WARNING"
            verdict = f"Riesgo de diabetes a 5 años: {dm_risk_5y * 100:.1f}%"
        elif data.current_state == "pre_dm":
            estado = "CONFIRMED_ACTIVE" if dm_risk_5y > 0.30 else "PROBABLE_WARNING"
            verdict = f"Progresión a diabetes a 5 años: {dm_risk_5y * 100:.1f}%"
        elif data.current_state == "dm":
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Riesgo de complicaciones a 5 años: {probs_5y.get('dm_complications', 0) * 100:.1f}%"
        else:
            estado = "CONFIRMED_ACTIVE"
            verdict = f"Progresión de complicaciones a 5 años: {probs_5y.get('dm_complications', 0) * 100:.1f}%"

        explanation = (
            f"Estado actual: {state_labels[data.current_state]} (HbA1c {data.hba1c_percent}%). "
            f"Proyección a 5 años: "
            f"{', '.join([f'{state_labels[k]}: {v * 100:.1f}%' for k, v in probs_5y.items()])}. "
            f"Proyección a 10 años: "
            f"{', '.join([f'{state_labels[k]}: {v * 100:.1f}%' for k, v in probs_10y.items()])}"
        )

        return MarkovProgressionOutput(
            status="calibrated",
            state_probabilities_5y=probs_5y,
            state_probabilities_10y=probs_10y,
            calculated_value=verdict,
            confidence=0.78,
            explanation=explanation,
            estado_ui=estado,
            evidence=[
                ClinicalEvidence(
                    type="Calculation",
                    code="MARKOV-5Y",
                    value=round(dm_risk_5y * 100, 1),
                    threshold="<10%",
                    display="Riesgo de Diabetes a 5 años",
                ),
                ClinicalEvidence(
                    type="Calculation",
                    code="MARKOV-10Y",
                    value=round(dm_risk_10y * 100, 1),
                    threshold="<20%",
                    display="Riesgo de Diabetes a 10 años",
                ),
            ],
            metadata={
                "current_state": data.current_state,
                "dm_risk_5y": round(dm_risk_5y * 100, 1),
                "dm_risk_10y": round(dm_risk_10y * 100, 1),
                "complication_risk_5y": round(
                    probs_5y.get("dm_complications", 0) * 100, 1
                ),
            },
        )
