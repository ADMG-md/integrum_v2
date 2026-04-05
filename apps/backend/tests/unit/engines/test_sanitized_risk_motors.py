import pytest
from src.engines.risk import (
    CVDHazardMotor,
    CVDHazardInput,
    MarkovProgressionMotor,
    MarkovProgressionInput,
)


def test_cvd_hazard_reference_case_white_male():
    motor = CVDHazardMotor()
    data = CVDHazardInput(
        age_years=55,
        sex="male",
        race="white",
        total_cholesterol_mg_dl=213,
        hdl_mg_dl=50,
        sbp_mm_hg=120,
        sbp_treated=False,
        smoker=False,
        diabetic=False,
    )
    res = motor(data)
    assert res.risk_pct_10y is not None
    assert res.risk_pct_10y == pytest.approx(5.4, abs=1.0)


def test_cvd_hazard_reference_case_aa_female():
    motor = CVDHazardMotor()
    data = CVDHazardInput(
        age_years=65,
        sex="female",
        race="aa",
        total_cholesterol_mg_dl=180,
        hdl_mg_dl=45,
        sbp_mm_hg=140,
        sbp_treated=True,
        smoker=True,
        diabetic=True,
    )
    res = motor(data)
    assert res.risk_pct_10y > 20.0
    assert res.risk_category == "high"


def test_cvd_hazard_age_boundaries():
    motor = CVDHazardMotor()
    data = CVDHazardInput(
        age_years=39,
        sex="male",
        race="white",
        total_cholesterol_mg_dl=180,
        hdl_mg_dl=50,
        sbp_mm_hg=120,
        sbp_treated=False,
        smoker=False,
        diabetic=False,
    )
    res_under = motor(data)
    assert res_under.risk_pct_10y is not None  # PCE still computes, just less validated


def test_markov_progression_calibrated():
    motor = MarkovProgressionMotor()
    data = MarkovProgressionInput(
        current_state="pre_dm", age_years=45, bmi_kg_m2=32, hba1c_percent=6.2
    )
    result = motor(data)
    assert result.status == "calibrated"
    assert result.state_probabilities_5y is not None
    assert result.state_probabilities_10y is not None
    assert result.metadata["dm_risk_5y"] > 0
