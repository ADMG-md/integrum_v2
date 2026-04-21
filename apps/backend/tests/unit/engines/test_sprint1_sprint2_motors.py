"""
V&V Tests for Sprint 1 & Sprint 2 motors (18 motors, 54 tests).

Each motor gets 3 minimum tests:
1. validate_returns_false_without_data
2. compute_with_normal_values
3. compute_with_abnormal_values

Priority order: CRITICAL (patient safety) > HIGH (early diagnosis) > MEDIUM
"""

import pytest
from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
    AdjudicationResult,
)
from src.domain.models import ClinicalHistory, TraumaHistory
from src.schemas.encounter import MedicationSchema


# ============================================================
# CRITICAL - Patient Safety
# ============================================================


class TestGLP1MonitoringMotor:
    def test_validate_returns_false_without_glp1(self, minimal_encounter):
        from src.engines.specialty.glp1_monitor import GLP1MonitoringMotor

        motor = GLP1MonitoringMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid
        assert "GLP-1" in reason

    def test_compute_with_no_alerts(self, encounter_with_glp1_therapy):
        from src.engines.specialty.glp1_monitor import GLP1MonitoringMotor

        enc = encounter_with_glp1_therapy
        enc.metadata["prev_weight_kg"] = 96.0
        enc.metadata["prev_muscle_mass_kg"] = 64.0
        motor = GLP1MonitoringMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_compute_with_excessive_muscle_loss(self, encounter_with_glp1_therapy):
        from src.engines.specialty.glp1_monitor import GLP1MonitoringMotor

        enc = encounter_with_glp1_therapy
        enc.metadata["prev_muscle_mass_kg"] = 65.0
        motor = GLP1MonitoringMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["muscle_loss_pct"] > 10


class TestMetforminB12Motor:
    def test_validate_returns_false_without_metformin(self, minimal_encounter):
        from src.engines.specialty.metformin_b12 import MetforminB12Motor

        motor = MetforminB12Motor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid
        assert "metformin" in reason.lower()

    def test_compute_with_normal_b12(self, encounter_with_metformin):
        from src.engines.specialty.metformin_b12 import MetforminB12Motor

        enc = encounter_with_metformin
        for o in enc.observations:
            if o.code == "VITB12-001":
                o.value = 400.0
        motor = MetforminB12Motor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["b12_value"] == 400.0

    def test_compute_with_deficient_b12(self, encounter_with_metformin):
        from src.engines.specialty.metformin_b12 import MetforminB12Motor

        motor = MetforminB12Motor()
        result = motor.compute(encounter_with_metformin)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["b12_value"] == 180.0
        assert result.estado_ui == "CONFIRMED_ACTIVE"


class TestCancerScreeningMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.cancer_screening import CancerScreeningMotor

        motor = CancerScreeningMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_computes_for_young_patient(self, encounter_with_metabolic_data):
        from src.engines.specialty.cancer_screening import CancerScreeningMotor

        enc = encounter_with_metabolic_data
        for o in enc.observations:
            if o.code == "AGE-001":
                o.value = 30.0
        motor = CancerScreeningMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_multiple_gaps_older_obese_patient(self, encounter_with_metabolic_data):
        from src.engines.specialty.cancer_screening import CancerScreeningMotor

        enc = encounter_with_metabolic_data
        for o in enc.observations:
            if o.code == "AGE-001":
                o.value = 55.0
        motor = CancerScreeningMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["gaps"] > 0


# ============================================================
# HIGH - Early Diagnosis
# ============================================================


class TestFLIMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.fatty_liver import FLIMotor

        motor = FLIMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_with_normal_fli(self, encounter_with_metabolic_data):
        from src.engines.specialty.fatty_liver import FLIMotor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.triglycerides_mg_dl = 80.0
        enc.metabolic_panel.ggt_u_l = 20.0
        enc.metabolic_panel.ast_u_l = 25.0
        enc.metabolic_panel.alt_u_l = 20.0
        enc.observations = [o for o in enc.observations if o.code != "WAIST-001"]
        enc.observations.append(Observation(code="WAIST-001", value=80.0, unit="cm"))
        motor = FLIMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["category"] == "low"

    def test_compute_with_abnormal_fli(self, encounter_with_metabolic_data):
        from src.engines.specialty.fatty_liver import FLIMotor

        motor = FLIMotor()
        result = motor.compute(encounter_with_metabolic_data)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["category"] == "high"
        assert result.estado_ui == "CONFIRMED_ACTIVE"


class TestNFSMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.nafld_fibrosis import NFSMotor

        motor = NFSMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_with_low_nfs(self, encounter_with_metabolic_data):
        from src.engines.specialty.nafld_fibrosis import NFSMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.platelets_k_u_l = 250.0
        enc.metabolic_panel.ast_u_l = 20.0
        enc.metabolic_panel.alt_u_l = 25.0
        enc.metabolic_panel.albumin_g_dl = 4.5
        enc.history = ClinicalHistory(has_type2_diabetes=False)
        motor = NFSMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["category"] == "low"

    def test_compute_with_high_nfs(self, encounter_with_metabolic_data):
        from src.engines.specialty.nafld_fibrosis import NFSMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.platelets_k_u_l = 150.0
        enc.metabolic_panel.ast_u_l = 60.0
        enc.metabolic_panel.alt_u_l = 40.0
        enc.metabolic_panel.albumin_g_dl = 3.2
        enc.history = ClinicalHistory(has_type2_diabetes=True)
        motor = NFSMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["category"] == "high"


class TestApoBApoA1Motor:
    def test_validate_returns_false_without_data(self, minimal_encounter):
        from src.engines.specialty.apob_ratio import ApoBApoA1Motor

        enc = minimal_encounter
        enc.cardio_panel.apoa1_mg_dl = None
        motor = ApoBApoA1Motor()
        is_valid, reason = motor.validate(enc)
        assert not is_valid

    def test_compute_with_normal_ratio(self, encounter_with_metabolic_data):
        from src.engines.specialty.apob_ratio import ApoBApoA1Motor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.apob_mg_dl = 80.0
        enc.cardio_panel.apoa1_mg_dl = 150.0
        motor = ApoBApoA1Motor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["ratio"] < 0.6

    def test_compute_with_high_ratio(self, encounter_with_metabolic_data):
        from src.engines.specialty.apob_ratio import ApoBApoA1Motor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.apob_mg_dl = 140.0
        enc.cardio_panel.apoa1_mg_dl = 90.0
        motor = ApoBApoA1Motor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["ratio"] > 1.0
        assert result.estado_ui == "CONFIRMED_ACTIVE"


class TestVAIMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.visceral_adiposity import VAIMotor

        motor = VAIMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_with_normal_vai(self, encounter_with_metabolic_data):
        from src.engines.specialty.visceral_adiposity import VAIMotor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.triglycerides_mg_dl = 80.0
        enc.cardio_panel.hdl_mg_dl = 55.0
        enc.observations = [o for o in enc.observations if o.code != "WAIST-001"]
        enc.observations.append(Observation(code="WAIST-001", value=80.0, unit="cm"))
        motor = VAIMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert not result.metadata["is_high"]

    def test_compute_with_high_vai(self, encounter_with_metabolic_data):
        from src.engines.specialty.visceral_adiposity import VAIMotor

        motor = VAIMotor()
        result = motor.compute(encounter_with_metabolic_data)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["is_high"]
        assert result.estado_ui == "CONFIRMED_ACTIVE"


# ============================================================
# MEDIUM
# ============================================================


class TestPulsePressureMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.hemodynamics import PulsePressureMotor

        motor = PulsePressureMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_with_normal_pp(self, minimal_encounter):
        from src.engines.specialty.hemodynamics import PulsePressureMotor

        enc = minimal_encounter
        enc.observations = [
            o for o in enc.observations if o.code not in ("8480-6", "8462-4")
        ]
        enc.observations.extend(
            [
                Observation(code="8480-6", value=120.0, unit="mmHg"),
                Observation(code="8462-4", value=75.0, unit="mmHg"),
            ]
        )
        motor = PulsePressureMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["pulse_pressure"] == 45.0

    def test_compute_with_wide_pp(self, minimal_encounter):
        from src.engines.specialty.hemodynamics import PulsePressureMotor

        enc = minimal_encounter
        enc.observations = [
            o for o in enc.observations if o.code not in ("8480-6", "8462-4")
        ]
        enc.observations.extend(
            [
                Observation(code="8480-6", value=170.0, unit="mmHg"),
                Observation(code="8462-4", value=70.0, unit="mmHg"),
            ]
        )
        motor = PulsePressureMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["pulse_pressure"] == 100.0
        assert result.estado_ui == "CONFIRMED_ACTIVE"


class TestACEScoreEngine:
    def test_validate_returns_false_without_ace(self, minimal_encounter):
        from src.engines.specialty.ace_integration import ACEScoreEngine

        motor = ACEScoreEngine()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid
        assert "ACE" in reason

    def test_compute_with_low_ace(self, encounter_with_metabolic_data):
        from src.engines.specialty.ace_integration import ACEScoreEngine

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(trauma=TraumaHistory(ace_score=1))
        motor = ACEScoreEngine()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["ace_score"] == 1
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_compute_with_high_ace(self, encounter_with_metabolic_data):
        from src.engines.specialty.ace_integration import ACEScoreEngine

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(trauma=TraumaHistory(ace_score=7))
        motor = ACEScoreEngine()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["ace_score"] == 7
        assert result.estado_ui == "CONFIRMED_ACTIVE"


class TestSGLT2iBenefitMotor:
    def test_validate_returns_false_without_indication(self, minimal_encounter):
        from src.engines.specialty.sglt2i_benefit import SGLT2iBenefitMotor

        motor = SGLT2iBenefitMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid
        assert "T2DM" in reason or "CKD" in reason

    def test_compute_with_t2dm_ckd(self, encounter_with_t2dm_ckd):
        from src.engines.specialty.sglt2i_benefit import SGLT2iBenefitMotor

        motor = SGLT2iBenefitMotor()
        result = motor.compute(encounter_with_t2dm_ckd)
        assert isinstance(result, AdjudicationResult)
        assert len(result.metadata["benefits"]) > 0
        assert result.estado_ui == "CONFIRMED_ACTIVE"

    def test_compute_with_t2dm_only(self, encounter_with_metabolic_data):
        from src.engines.specialty.sglt2i_benefit import SGLT2iBenefitMotor

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(has_type2_diabetes=True)
        motor = SGLT2iBenefitMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert len(result.metadata["benefits"]) > 0


# ============================================================
# Sprint 3: Risk stratification + endocrine
# ============================================================


class TestKFREMotor:
    def test_validate_returns_false_without_data(self, minimal_encounter):
        from src.engines.specialty.kfre import KFREMotor

        motor = KFREMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_low_risk(self, encounter_with_metabolic_data):
        from src.engines.specialty.kfre import KFREMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(Observation(code="UACR-001", value=15.0, unit="mg/g"))
        motor = KFREMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["risk_5y"] < 5

    def test_compute_with_high_risk(self, encounter_with_metabolic_data):
        from src.engines.specialty.kfre import KFREMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.creatinine_mg_dl = 3.5
        enc.observations.append(Observation(code="UACR-001", value=1500.0, unit="mg/g"))
        motor = KFREMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["risk_5y"] > 25


class TestCharlsonMotor:
    def test_validate_returns_false_without_conditions(self, minimal_encounter):
        from src.engines.specialty.charlson import CharlsonMotor

        motor = CharlsonMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_no_comorbidity(self, encounter_with_metabolic_data):
        from src.engines.specialty.charlson import CharlsonMotor
        from src.domain.models import Condition

        enc = encounter_with_metabolic_data
        enc.conditions = [Condition(code="E66.0", title="Obesity")]
        motor = CharlsonMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["cci_score"] == 0

    def test_compute_with_high_comorbidity(self, encounter_with_metabolic_data):
        from src.engines.specialty.charlson import CharlsonMotor
        from src.domain.models import Condition

        enc = encounter_with_metabolic_data
        enc.conditions = [
            Condition(code="I21", title="MI"),
            Condition(code="I50", title="HF"),
            Condition(code="N18.4", title="CKD Stage 4"),
        ]
        motor = CharlsonMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["cci_score"] >= 5


class TestFreeTestosteroneMotor:
    def test_validate_returns_false_without_data(self, minimal_encounter):
        from src.engines.specialty.free_testosterone import FreeTestosteroneMotor

        motor = FreeTestosteroneMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_normal_free_t(self, encounter_with_metabolic_data):
        from src.engines.specialty.free_testosterone import FreeTestosteroneMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(
            Observation(code="TESTO-001", value=500.0, unit="ng/dL")
        )
        enc.metabolic_panel.shbg_nmol_l = 35.0
        motor = FreeTestosteroneMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_compute_with_low_free_t(self, encounter_with_metabolic_data):
        from src.engines.specialty.free_testosterone import FreeTestosteroneMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(
            Observation(code="TESTO-001", value=150.0, unit="ng/dL")
        )
        enc.metabolic_panel.shbg_nmol_l = 80.0
        motor = FreeTestosteroneMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["free_t_pg_ml"] < 50


class TestVitaminDMotor:
    def test_validate_returns_false_without_data(self, minimal_encounter):
        from src.engines.specialty.vitamin_d import VitaminDMotor

        motor = VitaminDMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_sufficient_vitd(self, encounter_with_metabolic_data):
        from src.engines.specialty.vitamin_d import VitaminDMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(Observation(code="VITD-001", value=45.0, unit="ng/mL"))
        motor = VitaminDMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.estado_ui == "INDETERMINATE_LOCKED"

    def test_compute_with_deficient_vitd(self, encounter_with_metabolic_data):
        from src.engines.specialty.vitamin_d import VitaminDMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(Observation(code="VITD-001", value=12.0, unit="ng/mL"))
        motor = VitaminDMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.estado_ui == "CONFIRMED_ACTIVE"


# ============================================================
# Sprint 5: Clinical utility
# ============================================================


class TestFriedFrailtyMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.fried_frailty import FriedFrailtyMotor

        motor = FriedFrailtyMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_robust(self, encounter_with_metabolic_data):
        from src.engines.specialty.fried_frailty import FriedFrailtyMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(Observation(code="GRIP-STR-R", value=35.0, unit="kg"))
        enc.observations.append(Observation(code="GAIT-SPEED", value=1.1, unit="m/s"))
        enc.observations.append(Observation(code="PA-MIN-WEEK", value=200))
        motor = FriedFrailtyMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["fried_score"] == 0

    def test_compute_frail(self, encounter_with_metabolic_data):
        from src.engines.specialty.fried_frailty import FriedFrailtyMotor

        enc = encounter_with_metabolic_data
        enc.observations.append(Observation(code="GRIP-STR-R", value=14.0, unit="kg"))
        enc.observations.append(Observation(code="GAIT-SPEED", value=0.6, unit="m/s"))
        enc.observations.append(Observation(code="PA-MIN-WEEK", value=30))
        enc.observations.append(Observation(code="PHQ9-SCORE", value=15))
        motor = FriedFrailtyMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["fried_score"] >= 3


class TestTyGBMIMotor:
    def test_validate_returns_false_without_data(self, empty_encounter):
        from src.engines.specialty.tyg_bmi import TyGBMIMotor

        motor = TyGBMIMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_with_low_ir(self, encounter_with_metabolic_data):
        from src.engines.specialty.tyg_bmi import TyGBMIMotor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.triglycerides_mg_dl = 70.0
        enc.metabolic_panel.glucose_mg_dl = 80.0
        enc.observations = [
            o for o in enc.observations if o.code not in ("29463-7", "8302-2")
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=60.0, unit="kg"),
                Observation(code="8302-2", value=175.0, unit="cm"),
            ]
        )
        motor = TyGBMIMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["tyg_bmi"] < 230

    def test_compute_with_severe_ir(self, encounter_with_metabolic_data):
        from src.engines.specialty.tyg_bmi import TyGBMIMotor

        motor = TyGBMIMotor()
        result = motor.compute(encounter_with_metabolic_data)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["category"] == "severe"


class TestCVDReclassifierMotor:
    def test_validate_returns_false_without_ldl(self, empty_encounter):
        from src.engines.specialty.cvd_reclassifier import CVDReclassifierMotor

        motor = CVDReclassifierMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_compute_no_statin_needed(self, encounter_with_metabolic_data):
        from src.engines.specialty.cvd_reclassifier import CVDReclassifierMotor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.ldl_mg_dl = 90.0
        enc.cardio_panel.triglycerides_mg_dl = 80.0
        enc.cardio_panel.hdl_mg_dl = 60.0
        enc.metabolic_panel.hs_crp_mg_l = 0.5
        enc.metabolic_panel.glucose_mg_dl = 85.0
        enc.observations = [
            o for o in enc.observations if o.code not in ("WAIST-001", "8480-6")
        ]
        enc.observations.extend(
            [
                Observation(code="WAIST-001", value=75.0, unit="cm"),
                Observation(code="8480-6", value=115.0, unit="mmHg"),
            ]
        )
        motor = CVDReclassifierMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["n_factors"] <= 1

    def test_compute_statin_indicated(self, encounter_with_metabolic_data):
        from src.engines.specialty.cvd_reclassifier import CVDReclassifierMotor

        enc = encounter_with_metabolic_data
        enc.cardio_panel.ldl_mg_dl = 170.0
        enc.cardio_panel.triglycerides_mg_dl = 200.0
        enc.metabolic_panel.hs_crp_mg_l = 3.0
        motor = CVDReclassifierMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["n_factors"] >= 1


# ============================================================
# Sprint 6: Sex-specific health assessments
# ============================================================


class TestWomensHealthMotor:
    def test_validate_returns_false_for_male(self, minimal_encounter):
        from src.engines.specialty.womens_health import WomensHealthMotor

        enc = minimal_encounter
        enc.metadata["sex"] = "male"
        motor = WomensHealthMotor()
        is_valid, reason = motor.validate(enc)
        assert not is_valid
        assert "female" in reason.lower()

    def test_compute_with_sop_confirmed(self, encounter_with_metabolic_data):
        from src.engines.specialty.womens_health import WomensHealthMotor

        enc = encounter_with_metabolic_data
        enc.demographics.gender = "female"
        enc.metadata["sex"] = "female"
        enc.metabolic_panel.testosterone_total_ng_dl = 80.0
        enc.metabolic_panel.shbg_nmol_l = 15.0
        enc.history = ClinicalHistory(cycle_regularity="irregular")
        motor = WomensHealthMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["sop_confirmed"] is True
        assert result.estado_ui == "CONFIRMED_ACTIVE"

    def test_compute_with_pregnancy_alert(self, encounter_with_metabolic_data):
        from src.engines.specialty.womens_health import WomensHealthMotor

        enc = encounter_with_metabolic_data
        enc.demographics.gender = "female"
        enc.metadata["sex"] = "female"
        enc.history = ClinicalHistory(pregnancy_status="pregnant")
        motor = WomensHealthMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["pregnancy_status"] == "pregnant"
        assert result.estado_ui == "CONFIRMED_ACTIVE"
        assert any(a.priority == "critical" for a in result.action_checklist)


class TestMensHealthMotor:
    def test_validate_returns_false_for_female(self, minimal_encounter):
        from src.engines.specialty.mens_health import MensHealthMotor

        enc = minimal_encounter
        enc.metadata["sex"] = "female"
        motor = MensHealthMotor()
        is_valid, reason = motor.validate(enc)
        assert not is_valid
        assert "male" in reason.lower()

    def test_compute_with_hypogonadism(self, encounter_with_metabolic_data):
        from src.engines.specialty.mens_health import MensHealthMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.testosterone_total_ng_dl = 200.0
        enc.history = ClinicalHistory(has_erectile_dysfunction=True)
        motor = MensHealthMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["hypogonadism_confirmed"] is True
        assert result.estado_ui == "CONFIRMED_ACTIVE"

    def test_compute_with_elevated_psa(self, encounter_with_metabolic_data):
        from src.engines.specialty.mens_health import MensHealthMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.psa_ng_ml = 12.0
        enc.history = ClinicalHistory()
        motor = MensHealthMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["psa"] == 12.0
        assert result.estado_ui == "CONFIRMED_ACTIVE"
        assert any(a.priority == "critical" for a in result.action_checklist)


# ============================================================
# Sprint 7: Therapy optimization
# ============================================================


class TestBodyCompositionTrendMotor:
    def test_validate_returns_false_without_data(self, minimal_encounter):
        from src.engines.specialty.body_comp_trend import BodyCompositionTrendMotor

        motor = BodyCompositionTrendMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_acceptable_lean_loss(self, encounter_with_metabolic_data):
        from src.engines.specialty.body_comp_trend import BodyCompositionTrendMotor

        enc = encounter_with_metabolic_data
        enc.metadata["prev_weight_kg"] = 100.0
        enc.metadata["prev_muscle_mass_kg"] = 65.0
        enc.observations = [
            o
            for o in enc.observations
            if o.code not in ("29463-7", "MMA-001", "MUSCLE-KG")
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=90.0, unit="kg"),
                Observation(code="MMA-001", value=64.0, unit="kg"),
            ]
        )
        motor = BodyCompositionTrendMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["lean_loss_pct"] < 15

    def test_compute_with_high_lean_loss(self, encounter_with_metabolic_data):
        from src.engines.specialty.body_comp_trend import BodyCompositionTrendMotor

        enc = encounter_with_metabolic_data
        enc.metadata["prev_weight_kg"] = 100.0
        enc.metadata["prev_muscle_mass_kg"] = 65.0
        enc.observations = [
            o
            for o in enc.observations
            if o.code not in ("29463-7", "MMA-001", "MUSCLE-KG")
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=80.0, unit="kg"),
                Observation(code="MMA-001", value=55.0, unit="kg"),
            ]
        )
        motor = BodyCompositionTrendMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["lean_loss_pct"] > 25


class TestObesityPharmaEligibilityMotor:
    def test_validate_returns_false_without_bmi(self, minimal_encounter):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = minimal_encounter
        enc.observations = [
            o for o in enc.observations if o.code not in ("29463-7", "8302-2")
        ]
        motor = ObesityPharmaEligibilityMotor()
        is_valid, reason = motor.validate(enc)
        assert not is_valid

    def test_compute_eligible_bmi30(self, encounter_with_metabolic_data):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory()
        motor = ObesityPharmaEligibilityMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["eligible"] is True

    def test_compute_not_eligible_low_bmi(self, encounter_with_metabolic_data):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = encounter_with_metabolic_data
        enc.observations = [
            o for o in enc.observations if o.code not in ("29463-7", "8302-2")
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=55.0, unit="kg"),
                Observation(code="8302-2", value=175.0, unit="cm"),
            ]
        )
        enc.history = ClinicalHistory()
        motor = ObesityPharmaEligibilityMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert result.metadata["eligible"] is False

    def test_glp1_contraindicated_mtc(self, encounter_with_metabolic_data):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(has_history_medullary_thyroid_carcinoma=True)
        motor = ObesityPharmaEligibilityMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert any(
            "carcinoma medular" in f.lower() for f in result.explanation.split("; ")
        )

    def test_glp1_contraindicated_men2(self, encounter_with_metabolic_data):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(has_history_men2=True)
        motor = ObesityPharmaEligibilityMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert any("men2" in f.lower() for f in result.explanation.split("; "))

    def test_bupropion_contraindicated_suicide_risk(
        self, encounter_with_metabolic_data
    ):
        from src.engines.specialty.aom_eligibility import ObesityPharmaEligibilityMotor

        enc = encounter_with_metabolic_data
        enc.history = ClinicalHistory(phq9_item_9_score=2)
        motor = ObesityPharmaEligibilityMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
        assert any(
            "riesgo suicida" in str(a.task).lower()
            or "contraindicado" in str(a.task).lower()
            for a in result.action_checklist
        )


class TestGLP1TitrationMotor:
    def test_validate_returns_false_without_glp1(self, minimal_encounter):
        from src.engines.specialty.glp1_titration import GLP1TitrationMotor

        motor = GLP1TitrationMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_good_response(self, encounter_with_glp1_therapy):
        from src.engines.specialty.glp1_titration import GLP1TitrationMotor

        enc = encounter_with_glp1_therapy
        enc.metadata["prev_weight_kg"] = 105.0
        enc.metadata["glp1_weeks"] = 16
        motor = GLP1TitrationMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_compute_with_suboptimal_response(self, encounter_with_glp1_therapy):
        from src.engines.specialty.glp1_titration import GLP1TitrationMotor

        enc = encounter_with_glp1_therapy
        enc.metadata["prev_weight_kg"] = 104.0
        enc.metadata["glp1_weeks"] = 16
        motor = GLP1TitrationMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)


class TestDrugInteractionMotor:
    def test_validate_returns_false_without_meds(self, minimal_encounter):
        from src.engines.specialty.drug_interaction import DrugInteractionMotor

        motor = DrugInteractionMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_no_interactions(self, encounter_with_metabolic_data):
        from src.engines.specialty.drug_interaction import DrugInteractionMotor
        from src.schemas.encounter import MedicationSchema

        enc = encounter_with_metabolic_data
        enc.medications = [
            MedicationSchema(name="lisinopril", dose_amount="10mg", frequency="daily"),
        ]
        motor = DrugInteractionMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_compute_with_critical_interaction(self, encounter_with_metabolic_data):
        from src.engines.specialty.drug_interaction import DrugInteractionMotor
        from src.schemas.encounter import MedicationSchema

        enc = encounter_with_metabolic_data
        enc.medications = [
            MedicationSchema(
                name="semaglutide", dose_amount="1.0mg", frequency="weekly"
            ),
            MedicationSchema(
                name="insulin_glargine", dose_amount="20U", frequency="daily"
            ),
        ]
        motor = DrugInteractionMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_bupropion_contraindicated_suicide_risk(
        self, encounter_with_metabolic_data
    ):
        from src.engines.specialty.drug_interaction import DrugInteractionMotor

        enc = encounter_with_metabolic_data
        enc.medications = [
            MedicationSchema(
                name="naltrexone_bupropion", dose_amount="8mg-90mg", frequency="daily"
            ),
        ]
        motor = DrugInteractionMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)


class TestProteinEngineMotor:
    def test_validate_returns_false_without_ffm(self, minimal_encounter):
        from src.engines.protein_engine import ProteinEngineMotor

        motor = ProteinEngineMotor()
        is_valid, reason = motor.validate(minimal_encounter)
        assert not is_valid

    def test_compute_with_normal_ffm(self, encounter_with_metabolic_data):
        from src.engines.protein_engine import ProteinEngineMotor

        enc = encounter_with_metabolic_data
        enc.observations = [
            o
            for o in enc.observations
            if o.code not in ("29463-7", "8302-2", "MMA-001", "MUSCLE-KG", "BIA-FFM-KG")
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=80.0, unit="kg"),
                Observation(code="8302-2", value=175.0, unit="cm"),
                Observation(code="MMA-001", value=30.0, unit="kg"),
            ]
        )
        motor = ProteinEngineMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)

    def test_compute_with_ckd_restriction(self, encounter_with_metabolic_data):
        from src.engines.protein_engine import ProteinEngineMotor

        enc = encounter_with_metabolic_data
        enc.metabolic_panel.creatinine_mg_dl = 3.0
        enc.observations = [
            o
            for o in enc.observations
            if o.code
            not in (
                "29463-7",
                "8302-2",
                "MMA-001",
                "MUSCLE-KG",
                "BIA-FFM-KG",
                "UACR-001",
            )
        ]
        enc.observations.extend(
            [
                Observation(code="29463-7", value=80.0, unit="kg"),
                Observation(code="8302-2", value=175.0, unit="cm"),
                Observation(code="MMA-001", value=30.0, unit="kg"),
                Observation(code="UACR-001", value=150.0, unit="mg/g"),
            ]
        )
        motor = ProteinEngineMotor()
        result = motor.compute(enc)
        assert isinstance(result, AdjudicationResult)
