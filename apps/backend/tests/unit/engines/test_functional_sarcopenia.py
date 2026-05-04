"""
V&V Tests for FunctionalSarcopeniaMotor (EWGSOP2-FUNC).

Tests cover:
1. Validation (missing data scenarios)
2. 5x Chair Stand Test (normal, abnormal, boundary)
3. Grip Strength (male/female thresholds)
4. Gait Speed (normal, abnormal)
5. SARC-F (positive, negative)
6. Combined scoring (single abnormal, multiple abnormal, all normal)
7. Integration with SpecialtyRunner
"""

import pytest
from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    AdjudicationResult,
)
from src.engines.specialty.functional_sarcopenia import FunctionalSarcopeniaMotor


def _make_encounter(observations=None, sex="male"):
    return Encounter(
        id="test-func-sarc",
        demographics=DemographicsSchema(age_years=70.0, gender=sex),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=100,
            creatinine_mg_dl=1.0,
            albumin_g_dl=4.0,
            alkaline_phosphatase_u_l=80,
            mcv_fl=90,
            rdw_percent=13,
            wbc_k_ul=7,
            lymphocyte_percent=30,
            ferritin_ng_ml=100,
            hs_crp_mg_l=1.5, 
            total_cholesterol_mg_dl=200,
            ldl_mg_dl=130,
            hdl_mg_dl=45,
            triglycerides_mg_dl=150,
        ),
        observations=observations or [],
        metadata={"sex": sex},
    )


class TestFunctionalSarcopeniaValidation:
    def test_no_functional_data_returns_false(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter()
        is_valid, reason = motor.validate(enc)
        assert is_valid is False
        assert "5XSTS-SEC" in reason

    def test_only_5xsts_validates(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="5XSTS-SEC", value=12.0, unit="s")]
        )
        is_valid, reason = motor.validate(enc)
        assert is_valid is True

    def test_only_grip_validates(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=30.0, unit="kg")]
        )
        is_valid, reason = motor.validate(enc)
        assert is_valid is True

    def test_only_gait_speed_validates(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GAIT-SPEED", value=1.0, unit="m/s")]
        )
        is_valid, reason = motor.validate(enc)
        assert is_valid is True

    def test_only_sarcf_validates(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(observations=[Observation(code="SARCF-SCORE", value=2)])
        is_valid, reason = motor.validate(enc)
        assert is_valid is True


class TestFiveXSts:
    def test_normal_5xsts(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="5XSTS-SEC", value=10.0, unit="s")]
        )
        result = motor.compute(enc)
        assert result.metadata["five_x_sts_status"] == "normal"
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_abnormal_5xsts_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="5XSTS-SEC", value=15.1, unit="s")]
        )
        result = motor.compute(enc)
        assert result.metadata["five_x_sts_status"] == "abnormal"
        assert result.estado_ui == "PROBABLE_WARNING"

    def test_abnormal_5xsts_clear(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="5XSTS-SEC", value=20.0, unit="s")]
        )
        result = motor.compute(enc)
        assert result.metadata["five_x_sts_status"] == "abnormal"
        assert "bajo rendimiento" in result.explanation

    def test_exact_boundary_15s_is_normal(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="5XSTS-SEC", value=15.0, unit="s")]
        )
        result = motor.compute(enc)
        assert result.metadata["five_x_sts_status"] == "normal"


class TestGripStrength:
    def test_male_normal_grip(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=35.0, unit="kg")],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.metadata["best_grip_kg"] == 35.0
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_male_low_grip(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=25.0, unit="kg")],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.metadata["best_grip_kg"] == 25.0
        assert result.estado_ui == "PROBABLE_WARNING"

    def test_female_normal_grip(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=20.0, unit="kg")],
            sex="female",
        )
        result = motor.compute(enc)
        assert result.metadata["best_grip_kg"] == 20.0
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_female_low_grip(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=14.0, unit="kg")],
            sex="female",
        )
        result = motor.compute(enc)
        assert result.metadata["best_grip_kg"] == 14.0
        assert result.estado_ui == "PROBABLE_WARNING"

    def test_uses_best_of_both_hands(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="GRIP-STR-R", value=22.0, unit="kg"),
                Observation(code="GRIP-STR-L", value=28.0, unit="kg"),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.metadata["best_grip_kg"] == 28.0
        assert result.metadata["tests_evaluated"] == 2
        assert isinstance(result, AdjudicationResult)

    def test_male_grip_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=27.0, unit="kg")],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_male_grip_just_below_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GRIP-STR-R", value=26.9, unit="kg")],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "PROBABLE_WARNING"


class TestGaitSpeed:
    def test_normal_gait_speed(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GAIT-SPEED", value=1.0, unit="m/s")]
        )
        result = motor.compute(enc)
        assert result.metadata["gait_speed_status"] == "normal"
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_slow_gait_speed(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GAIT-SPEED", value=0.7, unit="m/s")]
        )
        result = motor.compute(enc)
        assert result.metadata["gait_speed_status"] == "abnormal"
        assert result.estado_ui == "PROBABLE_WARNING"

    def test_gait_speed_exact_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[Observation(code="GAIT-SPEED", value=0.8, unit="m/s")]
        )
        result = motor.compute(enc)
        assert result.metadata["gait_speed_status"] == "abnormal"


class TestSarcF:
    def test_negative_sarcf(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(observations=[Observation(code="SARCF-SCORE", value=2)])
        result = motor.compute(enc)
        assert result.metadata["sarcf_status"] == "negative"
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_positive_sarcf(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(observations=[Observation(code="SARCF-SCORE", value=5)])
        result = motor.compute(enc)
        assert result.metadata["sarcf_status"] == "positive"
        assert result.estado_ui == "PROBABLE_WARNING"

    def test_sarcf_exact_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(observations=[Observation(code="SARCF-SCORE", value=4)])
        result = motor.compute(enc)
        assert result.metadata["sarcf_status"] == "positive"

    def test_sarcf_just_below_boundary(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(observations=[Observation(code="SARCF-SCORE", value=3)])
        result = motor.compute(enc)
        assert result.metadata["sarcf_status"] == "negative"


class TestCombinedScoring:
    def test_all_normal_returns_no_indicators(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="5XSTS-SEC", value=10.0, unit="s"),
                Observation(code="GRIP-STR-R", value=35.0, unit="kg"),
                Observation(code="GAIT-SPEED", value=1.1, unit="m/s"),
                Observation(code="SARCF-SCORE", value=1),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "INDETERMINATE_LOCKED"
        assert "conservada" in result.explanation
        assert result.metadata["functional_score"] == 0

    def test_single_abnormal_returns_possible_sarcopenia(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="5XSTS-SEC", value=18.0, unit="s"),
                Observation(code="GRIP-STR-R", value=35.0, unit="kg"),
                Observation(code="GAIT-SPEED", value=1.1, unit="m/s"),
                Observation(code="SARCF-SCORE", value=1),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "PROBABLE_WARNING"
        assert "POSIBLE" in result.calculated_value
        assert result.metadata["functional_score"] == 2

    def test_multiple_abnormal_returns_probable_sarcopenia(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="5XSTS-SEC", value=20.0, unit="s"),
                Observation(code="GRIP-STR-R", value=20.0, unit="kg"),
                Observation(code="GAIT-SPEED", value=0.6, unit="m/s"),
                Observation(code="SARCF-SCORE", value=6),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "CONFIRMED_ACTIVE"
        assert "PROBABLE" in result.calculated_value
        assert result.metadata["functional_score"] == 8
        assert result.metadata["tests_evaluated"] == 4

    def test_two_abnormal_with_partial_data(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="5XSTS-SEC", value=18.0, unit="s"),
                Observation(code="GRIP-STR-R", value=20.0, unit="kg"),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "CONFIRMED_ACTIVE"
        assert result.metadata["functional_score"] == 4
        assert result.metadata["tests_evaluated"] == 2

    def test_one_abnormal_with_partial_data(self):
        motor = FunctionalSarcopeniaMotor()
        enc = _make_encounter(
            observations=[
                Observation(code="5XSTS-SEC", value=18.0, unit="s"),
                Observation(code="GRIP-STR-R", value=35.0, unit="kg"),
            ],
            sex="male",
        )
        result = motor.compute(enc)
        assert result.estado_ui == "PROBABLE_WARNING"
        assert result.metadata["functional_score"] == 2


class TestVersionHash:
    def test_version_hash_is_consistent(self):
        motor = FunctionalSarcopeniaMotor()
        hash1 = motor.get_version_hash()
        hash2 = motor.get_version_hash()
        assert hash1 == hash2
        assert len(hash1) == 64
