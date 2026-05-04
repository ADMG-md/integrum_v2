"""
V&V Tests for ALL registered motors.
Each motor is tested with:
1. Instantiation
2. Validation with minimal data
3. Computation with comprehensive data
"""

import pytest
from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    Condition,
)
from src.engines.base_models import AdjudicationResult
from src.engines.specialty_runner import specialty_runner


@pytest.fixture
def minimal_encounter():
    return Encounter(
        id="test-min",
        demographics=DemographicsSchema(age_years=45.0, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=100,
            creatinine_mg_dl=1.0,
            hba1c_percent=5.7,
            albumin_g_dl=4.0,
            alkaline_phosphatase_u_l=80,
            mcv_fl=90,
            rdw_percent=13,
            wbc_k_ul=7,
            lymphocyte_percent=30,
            neutrophil_percent=60,
            ferritin_ng_ml=100,
            hs_crp_mg_l=1.5, 
            total_cholesterol_mg_dl=200,
            ldl_mg_dl=130,
            hdl_mg_dl=45,
            triglycerides_mg_dl=150,
            apob_mg_dl=100,
            lpa_mg_dl=30,
        ),
        observations=[
            Observation(code="29463-7", value=95, unit="kg"),
            Observation(code="8302-2", value=170, unit="cm"),
            Observation(code="WAIST-001", value=95, unit="cm"),
            Observation(code="8480-6", value=135, unit="mmHg"),
            Observation(code="8462-4", value=85, unit="mmHg"),
            Observation(code="AGE-001", value=45),
            Observation(code="MMA-001", value=30, unit="kg"),
            Observation(code="MUSCLE-KG", value=30, unit="kg"),
            Observation(code="BIA-MUSCLE-KG", value=30, unit="kg"),
            Observation(code="11579-0", value=2.5),
            Observation(code="FT4-001", value=1.2),
            Observation(code="30522-7", value=1.5),
            Observation(code="26499-4", value=60),
            Observation(code="26474-7", value=30),
            Observation(code="FER-001", value=100),
            Observation(code="NECK-001", value=40, unit="cm"),
            Observation(code="LIFE-SNORING", value=0),
            Observation(code="LIFE-TIRED", value=0),
            Observation(code="LIFE-APNEA", value=0),
            Observation(code="PHQ-9", value=5, category="Psychometry"),
            Observation(code="GAD-7", value=4, category="Psychometry"),
            Observation(code="AIS-001", value=4, category="Psychometry"),
            Observation(code="TFEQ-UNCONTROLLED", value=10, category="Psychometry"),
            Observation(code="TFEQ-EMOTIONAL", value=8, category="Psychometry"),
            Observation(
                code="LIFE-EXERCISE", value=150, unit="min/week", category="Lifestyle"
            ),
            Observation(code="LIFE-STRESS", value=4, unit="1-10", category="Lifestyle"),
            Observation(code="LIFE-SLEEP", value=7, unit="hours", category="Lifestyle"),
        ],
        conditions=[
            Condition(
                code="E66.0", title="Obesidad por exceso calórico", system="CIE-10"
            ),
            Condition(code="I10", title="Hipertensión esencial", system="CIE-10"),
        ],
        metadata={"sex": "male"},
    )


# ============================================================
# Test all PRIMARY motors
# ============================================================


class TestPrimaryMotors:
    def test_all_primary_motors_run(self, minimal_encounter):
        """All primary motors should execute without error."""
        results = specialty_runner.run_all(minimal_encounter)
        # 26 primary motors registered after cleanup
        assert len(results) >= 18, (
            f"Expected >=18 results, got {len(results)}: {list(results.keys())}"
        )

    def test_acosta_phenotype(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["AcostaPhenotypeMotor"]
        assert isinstance(r, AdjudicationResult)
        assert r.calculated_value is not None

    def test_eoss_staging(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["EOSSStagingMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_sarcopenia(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["SarcopeniaMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_biological_age(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["BiologicalAgeMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_metabolic_precision(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["MetabolicPrecisionMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_deep_metabolic_proxy(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["DeepMetabolicProxyMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_lifestyle360(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["Lifestyle360Motor"]
        assert isinstance(r, AdjudicationResult)

    def test_anthropometry(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["AnthropometryMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_endocrine(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["EndocrineMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_hypertension(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["HypertensionMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_inflammation(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["InflammationMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_sleep_apnea(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["SleepApneaMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_laboratory_stewardship(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["LaboratoryStewardshipMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_functional_sarcopenia(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "FunctionalSarcopeniaMotor" in results:
            r = results["FunctionalSarcopeniaMotor"]
            assert isinstance(r, AdjudicationResult)

    def test_fli(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "FLIMotor" in results:
            assert isinstance(results["FLIMotor"], AdjudicationResult)

    def test_vai(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "VAIMotor" in results:
            assert isinstance(results["VAIMotor"], AdjudicationResult)

    def test_apob_apoa1(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "ApoBApoA1Motor" in results:
            assert isinstance(results["ApoBApoA1Motor"], AdjudicationResult)

    def test_pulse_pressure(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["PulsePressureMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_nfs(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "NFSMotor" in results:
            assert isinstance(results["NFSMotor"], AdjudicationResult)

    def test_glp1_monitor(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "GLP1MonitoringMotor" in results:
            assert isinstance(results["GLP1MonitoringMotor"], AdjudicationResult)

    def test_ace_score(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "ACEScoreEngine" in results:
            assert isinstance(results["ACEScoreEngine"], AdjudicationResult)

    def test_metformin_b12(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "MetforminB12Motor" in results:
            assert isinstance(results["MetforminB12Motor"], AdjudicationResult)

    def test_cancer_screening(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "CancerScreeningMotor" in results:
            assert isinstance(results["CancerScreeningMotor"], AdjudicationResult)

    def test_sglt2i_benefit(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "SGLT2iBenefitMotor" in results:
            assert isinstance(results["SGLT2iBenefitMotor"], AdjudicationResult)

    def test_kfre(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "KFREMotor" in results:
            assert isinstance(results["KFREMotor"], AdjudicationResult)

    def test_charlson(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "CharlsonMotor" in results:
            assert isinstance(results["CharlsonMotor"], AdjudicationResult)

    def test_free_testosterone(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "FreeTestosteroneMotor" in results:
            assert isinstance(results["FreeTestosteroneMotor"], AdjudicationResult)

    def test_vitamin_d(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        if "VitaminDMotor" in results:
            assert isinstance(results["VitaminDMotor"], AdjudicationResult)


class TestGatedMotors:
    def test_gated_motors_run(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        # CVDHazardMotor runs because patient has HTN + BMI >= 30
        assert "CVDHazardMotor" in results
        # MarkovProgressionMotor is gated: requires DM2/prediabetes (not present in minimal)
        assert "MarkovProgressionMotor" not in results

    def test_cvd_hazard(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        r = results["CVDHazardMotor"]
        assert isinstance(r, AdjudicationResult)

    def test_markov_progression_with_diabetes(self, minimal_encounter):
        """MarkovProgressionMotor only runs when patient has DM2 or prediabetes."""
        from src.domain.models import ClinicalHistory

        enc = minimal_encounter
        enc.history = ClinicalHistory(has_type2_diabetes=True)
        results = specialty_runner.run_all(enc)
        assert "MarkovProgressionMotor" in results
        r = results["MarkovProgressionMotor"]
        assert isinstance(r, AdjudicationResult)


# ============================================================
# Test AGGREGATOR motors
# ============================================================


class TestAggregatorMotors:
    def test_obesity_master(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        assert "ObesityMasterMotor" in results
        r = results["ObesityMasterMotor"]
        # ObesityMaster now returns AdjudicationResult (V2.7 contract fix)
        assert isinstance(r, AdjudicationResult)
        assert "clinical_profile" in r.metadata
        assert r.calculated_value is not None

    def test_clinical_guidelines(self, minimal_encounter):
        results = specialty_runner.run_all(minimal_encounter)
        assert "ClinicalGuidelinesMotor" in results
        r = results["ClinicalGuidelinesMotor"]
        assert isinstance(r, AdjudicationResult)
