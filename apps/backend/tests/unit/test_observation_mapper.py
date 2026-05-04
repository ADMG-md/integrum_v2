"""
Tests for observation_mapper.py and narrative_service.py — DT-07.

observation_mapper is the bridge between the HTTP payload and the clinical engine domain.
It maps 40+ clinical fields to LOINC-coded Observation objects.
A silent bug here means engines receive no data and return INDETERMINATE silently.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.services.observation_mapper import (
    map_biometrics_to_observations,
    map_metabolic_to_observations,
    map_psychometrics_to_observations,
    map_lifestyle_to_observations,
    build_flat_observations,
)
from src.services.narrative_service import NarrativeService
from src.engines.domain import AdjudicationResult, ClinicalEvidence


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _bio(weight_kg=80.0, height_cm=170.0, **kwargs):
    m = MagicMock()
    m.weight_kg = weight_kg
    m.height_cm = height_cm
    m.waist_cm = kwargs.get("waist_cm", None)
    m.hip_cm = kwargs.get("hip_cm", None)
    m.neck_cm = kwargs.get("neck_cm", None)
    m.systolic_bp = kwargs.get("systolic_bp", None)
    m.diastolic_bp = kwargs.get("diastolic_bp", None)
    m.arm_circumference_cm = kwargs.get("arm_circumference_cm", None)
    m.calf_circumference_cm = kwargs.get("calf_circumference_cm", None)
    m.muscle_mass_kg = kwargs.get("muscle_mass_kg", None)
    m.skeletal_muscle_index = kwargs.get("skeletal_muscle_index", None)
    m.body_fat_percent = kwargs.get("body_fat_percent", None)
    m.fat_mass_kg = kwargs.get("fat_mass_kg", None)
    m.lean_mass_kg = kwargs.get("lean_mass_kg", None)
    m.visceral_fat_area_cm2 = kwargs.get("visceral_fat_area_cm2", None)
    m.visceral_fat_level = kwargs.get("visceral_fat_level", None)
    m.basal_metabolic_rate = kwargs.get("basal_metabolic_rate", None)
    m.total_body_water_percent = kwargs.get("total_body_water_percent", None)
    m.bone_mass_kg = kwargs.get("bone_mass_kg", None)
    return m


def _metabolic(**kwargs):
    m = MagicMock()
    defaults = {
        "glucose_mg_dl": None, "hba1c_percent": None, "insulin_mu_u_ml": None,
        "c_peptide_ng_ml": None, "gada_antibodies": None, "creatinine_mg_dl": None,
        "uric_acid_mg_dl": None, "ast_u_l": None, "alt_u_l": None, "ggt_u_l": None,
        "alkaline_phosphatase_u_l": None, "wbc_k_ul": None, "lymphocyte_percent": None,
        "neutrophil_percent": None, "mcv_fl": None, "rdw_percent": None,
        "platelets_k_u_l": None, "hs_crp_mg_l": None, "ferritin_ng_ml": None,
        "albumin_g_dl": None, "tsh_u_iu_ml": None, "ft4_ng_dl": None,
        "ft3_pg_ml": None, "rt3_ng_dl": None, "shbg_nmol_l": None,
        "cortisol_am_mcg_dl": None, "aldosterone_ng_dl": None, "renin_ng_ml_h": None,
        "total_cholesterol_mg_dl": None, "ldl_mg_dl": None, "hdl_mg_dl": None,
        "triglycerides_mg_dl": None, "vldl_mg_dl": None, "apob_mg_dl": None,
        "lpa_mg_dl": None, "apoa1_mg_dl": None,
    }
    for k, v in {**defaults, **kwargs}.items():
        setattr(m, k, v)
    return m


def _psycho(**kwargs):
    m = MagicMock()
    m.phq9_score = kwargs.get("phq9_score", None)
    m.gad7_score = kwargs.get("gad7_score", None)
    m.atenas_insomnia_score = kwargs.get("atenas_insomnia_score", None)
    m.tfeq_emotional_eating = kwargs.get("tfeq_emotional_eating", None)
    m.tfeq_uncontrolled_eating = kwargs.get("tfeq_uncontrolled_eating", None)
    m.tfeq_cognitive_restraint = kwargs.get("tfeq_cognitive_restraint", None)
    return m


def _lifestyle(**kwargs):
    m = MagicMock()
    m.sleep_hours = kwargs.get("sleep_hours", None)
    m.physical_activity_min_week = kwargs.get("physical_activity_min_week", None)
    m.stress_level_vas = kwargs.get("stress_level_vas", None)
    return m


def _obs_codes(obs_list):
    return [o.code for o in obs_list]


# ─── map_biometrics_to_observations ──────────────────────────────────────────

class TestMapBiometrics:

    def test_mandatory_fields_always_present(self):
        """Weight and height must always map — engines depend on them."""
        obs = map_biometrics_to_observations(_bio(80, 170))
        codes = _obs_codes(obs)
        assert "29463-7" in codes, "Weight LOINC missing"
        assert "8302-2" in codes, "Height LOINC missing"

    def test_weight_value_correct(self):
        obs = map_biometrics_to_observations(_bio(75.5, 160))
        weight_obs = next(o for o in obs if o.code == "29463-7")
        assert weight_obs.value == 75.5
        assert weight_obs.unit == "kg"

    def test_optional_fields_absent_when_none(self):
        """No optional observations should be injected when data is None."""
        obs = map_biometrics_to_observations(_bio(80, 170))
        codes = _obs_codes(obs)
        assert "WAIST-001" not in codes
        assert "8480-6" not in codes  # SBP
        assert "MMA-001" not in codes

    def test_waist_injected_when_present(self):
        obs = map_biometrics_to_observations(_bio(80, 170, waist_cm=90.0))
        assert "WAIST-001" in _obs_codes(obs)
        waist = next(o for o in obs if o.code == "WAIST-001")
        assert waist.value == 90.0

    def test_bp_both_injected(self):
        obs = map_biometrics_to_observations(_bio(80, 170, systolic_bp=130, diastolic_bp=85))
        codes = _obs_codes(obs)
        assert "8480-6" in codes  # SBP
        assert "8462-4" in codes  # DBP

    def test_muscle_mass_triplicated_for_engines(self):
        """muscle_mass_kg must emit 3 codes (MMA-001, MUSCLE-KG, BIA-MUSCLE-KG) for engine compatibility."""
        obs = map_biometrics_to_observations(_bio(80, 170, muscle_mass_kg=32.0))
        codes = _obs_codes(obs)
        assert "MMA-001" in codes
        assert "MUSCLE-KG" in codes
        assert "BIA-MUSCLE-KG" in codes

    def test_lbm_boer_male(self):
        """Boer LBM formula: male = 0.407*W + 0.267*H - 19.2"""
        obs = map_biometrics_to_observations(_bio(80, 170), gender="male")
        lbm = next((o for o in obs if o.code == "LBM-BOER"), None)
        assert lbm is not None, "LBM-BOER observation missing for male"
        expected = round(0.407 * 80 + 0.267 * 170 - 19.2, 1)
        assert lbm.value == expected

    def test_lbm_boer_female(self):
        """Boer LBM formula: female = 0.252*W + 0.473*H - 48.3"""
        obs = map_biometrics_to_observations(_bio(65, 160), gender="female")
        lbm = next((o for o in obs if o.code == "LBM-BOER"), None)
        assert lbm is not None, "LBM-BOER observation missing for female"
        expected = round(0.252 * 65 + 0.473 * 160 - 48.3, 1)
        assert lbm.value == expected

    def test_lbm_boer_absent_without_gender(self):
        """LBM cannot be calculated without gender — should not be injected."""
        obs = map_biometrics_to_observations(_bio(80, 170), gender=None)
        assert "LBM-BOER" not in _obs_codes(obs)

    def test_bia_fields_all_mapped(self):
        obs = map_biometrics_to_observations(_bio(
            80, 170,
            body_fat_percent=28.0,
            fat_mass_kg=22.0,
            lean_mass_kg=58.0,
            visceral_fat_area_cm2=120.0,
            visceral_fat_level=10,
            basal_metabolic_rate=1800,
            total_body_water_percent=55.0,
            bone_mass_kg=3.2,
        ))
        codes = _obs_codes(obs)
        assert "BIA-FAT-PCT" in codes
        assert "BIA-FAT-KG" in codes
        assert "BIA-LEAN-KG" in codes
        assert "BIA-VISCERAL" in codes
        assert "BIA-VISCERAL-LVL" in codes
        assert "BIA-BMR" in codes
        assert "BIA-TBW" in codes
        assert "BIA-BONE" in codes


# ─── map_metabolic_to_observations ───────────────────────────────────────────

class TestMapMetabolic:

    def test_empty_panel_returns_empty_list(self):
        obs = map_metabolic_to_observations(_metabolic())
        assert obs == [], "Empty metabolic panel should produce no observations"

    def test_glucose_mapping(self):
        obs = map_metabolic_to_observations(_metabolic(glucose_mg_dl=95.0))
        codes = _obs_codes(obs)
        assert "2339-0" in codes
        glu = next(o for o in obs if o.code == "2339-0")
        assert glu.value == 95.0
        assert glu.unit == "mg/dL"

    def test_lipid_panel_all_mapped(self):
        obs = map_metabolic_to_observations(_metabolic(
            total_cholesterol_mg_dl=200,
            ldl_mg_dl=120,
            hdl_mg_dl=50,
            triglycerides_mg_dl=150,
        ))
        codes = _obs_codes(obs)
        assert "2093-3" in codes   # Total cholesterol
        assert "13457-7" in codes  # LDL
        assert "2085-9" in codes   # HDL
        assert "2571-8" in codes   # TG

    def test_liver_enzymes_mapped(self):
        obs = map_metabolic_to_observations(_metabolic(ast_u_l=35, alt_u_l=42, ggt_u_l=60))
        codes = _obs_codes(obs)
        assert "29230-0" in codes  # AST
        assert "22538-3" in codes  # ALT
        assert "GGT-001" in codes

    def test_inflammation_markers(self):
        obs = map_metabolic_to_observations(_metabolic(hs_crp_mg_l=4.5, ferritin_ng_ml=220))
        codes = _obs_codes(obs)
        assert "30522-7" in codes  # hs-CRP
        assert "FER-001" in codes

    def test_hba1c_mapped(self):
        obs = map_metabolic_to_observations(_metabolic(hba1c_percent=6.2))
        assert "4548-4" in _obs_codes(obs)

    def test_thyroid_panel(self):
        obs = map_metabolic_to_observations(_metabolic(tsh_u_iu_ml=2.1, ft4_ng_dl=1.1))
        codes = _obs_codes(obs)
        assert "11579-0" in codes  # TSH
        assert "FT4-001" in codes


# ─── map_psychometrics_to_observations ───────────────────────────────────────

class TestMapPsychometrics:

    def test_all_none_returns_empty(self):
        obs = map_psychometrics_to_observations(_psycho())
        assert obs == []

    def test_phq9_mapped(self):
        obs = map_psychometrics_to_observations(_psycho(phq9_score=12))
        phq = next(o for o in obs if o.code == "PHQ-9")
        assert phq.value == 12
        assert phq.category == "Psychometry"

    def test_gad7_mapped(self):
        obs = map_psychometrics_to_observations(_psycho(gad7_score=8))
        assert "GAD-7" in _obs_codes(obs)

    def test_tfeq_all_three_scales(self):
        obs = map_psychometrics_to_observations(_psycho(
            tfeq_emotional_eating=3,
            tfeq_uncontrolled_eating=5,
            tfeq_cognitive_restraint=2,
        ))
        codes = _obs_codes(obs)
        assert "TFEQ-EMOTIONAL" in codes
        assert "TFEQ-UNCONTROLLED" in codes
        assert "TFEQ-COGNITIVE" in codes

    def test_phq9_zero_is_valid(self):
        """PHQ-9 score of 0 is clinically meaningful (no depression) — must not be skipped."""
        obs = map_psychometrics_to_observations(_psycho(phq9_score=0))
        assert "PHQ-9" in _obs_codes(obs)


# ─── map_lifestyle_to_observations ───────────────────────────────────────────

class TestMapLifestyle:

    def test_empty_returns_empty(self):
        obs = map_lifestyle_to_observations(_lifestyle())
        assert obs == []

    def test_sleep_hours_mapped(self):
        obs = map_lifestyle_to_observations(_lifestyle(sleep_hours=6.0))
        sleep = next(o for o in obs if o.code == "LIFE-SLEEP")
        assert sleep.value == 6.0
        assert sleep.unit == "hours"

    def test_exercise_mapped(self):
        obs = map_lifestyle_to_observations(_lifestyle(physical_activity_min_week=150))
        assert "LIFE-EXERCISE" in _obs_codes(obs)

    def test_stress_vas_mapped(self):
        obs = map_lifestyle_to_observations(_lifestyle(stress_level_vas=7))
        stress = next(o for o in obs if o.code == "LIFE-STRESS")
        assert stress.value == 7


# ─── build_flat_observations ─────────────────────────────────────────────────

class TestBuildFlatObservations:

    def _make_payload(self, **kwargs):
        p = MagicMock()
        p.observations = kwargs.get("observations", [])
        p.biometrics = kwargs.get("biometrics", None)
        p.metabolic = kwargs.get("metabolic", None)
        p.psychometrics = kwargs.get("psychometrics", None)
        p.lifestyle = kwargs.get("lifestyle", None)
        return p

    def test_empty_payload_returns_raw_observations_only(self):
        payload = self._make_payload(observations=[MagicMock(code="CUSTOM-001")])
        result = build_flat_observations(payload)
        assert len(result) == 1

    def test_all_sections_aggregated(self):
        payload = self._make_payload(
            biometrics=_bio(80, 170, waist_cm=90),
            metabolic=_metabolic(glucose_mg_dl=100),
            psychometrics=_psycho(phq9_score=5),
            lifestyle=_lifestyle(sleep_hours=7),
        )
        result = build_flat_observations(payload, gender="male")
        codes = _obs_codes(result)
        assert "29463-7" in codes   # weight
        assert "2339-0" in codes    # glucose
        assert "PHQ-9" in codes     # PHQ-9
        assert "LIFE-SLEEP" in codes

    def test_gender_flows_to_lbm_calculation(self):
        """Gender must reach map_biometrics for LBM-BOER to be calculated."""
        payload = self._make_payload(biometrics=_bio(80, 170))
        result = build_flat_observations(payload, gender="female")
        assert "LBM-BOER" in _obs_codes(result)

    def test_no_section_no_extra_obs(self):
        """If all optional sections are None, only raw observations are returned."""
        payload = self._make_payload(observations=[])
        result = build_flat_observations(payload)
        assert result == []


# ─── NarrativeService ────────────────────────────────────────────────────────

class TestNarrativeService:

    def _make_result(self, value: str) -> AdjudicationResult:
        return AdjudicationResult(
            calculated_value=value,
            confidence=0.9,
            explanation="test",
            estado_ui="CONFIRMED_ACTIVE",
            evidence=[],
        )

    def _make_encounter(self):
        enc = MagicMock()
        enc.model_dump.return_value = {}
        return enc

    def test_empty_results_returns_fallback(self):
        svc = NarrativeService()
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            result = svc.generate_technical_summary({}, self._make_encounter())
        assert "No se han detectado" in result

    def test_acosta_phenotype_included(self):
        svc = NarrativeService()
        results = {"acosta": self._make_result("Fenotipo Hiperfágico")}
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            narrative = svc.generate_technical_summary(results, self._make_encounter())
        assert "Fenotipo Hiperfágico" in narrative

    def test_eoss_staging_included(self):
        svc = NarrativeService()
        results = {
            "acosta": self._make_result("Fenotipo Sedentario"),
            "eoss": self._make_result("EOSS Etapa 2"),
        }
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            narrative = svc.generate_technical_summary(results, self._make_encounter())
        assert "EOSS Etapa 2" in narrative

    def test_metabolic_circadian_correlation(self):
        """Metabolic + sleep correlation should produce a specific insight."""
        svc = NarrativeService()
        results = {
            "MetabolicPrecisionMotor": self._make_result("Insulin Resistance detected"),
            "Lifestyle360Motor": self._make_result("Sleep Debt of 2h detected"),
        }
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            narrative = svc.generate_technical_summary(results, self._make_encounter())
        assert "circadian" in narrative.lower() or "sueño" in narrative.lower()

    def test_inflammation_finding_included(self):
        svc = NarrativeService()
        ev = ClinicalEvidence(type="Observation", code="HS-CRP", value=5.2, display="hs-CRP")
        inf_result = AdjudicationResult(
            calculated_value="Meta-inflammation systemic",
            confidence=0.85,
            explanation="",
            estado_ui="CONFIRMED_ACTIVE",
            evidence=[ev],
        )
        results = {"InflammationMotor": inf_result}
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            narrative = svc.generate_technical_summary(results, self._make_encounter())
        assert "inflamación" in narrative.lower() or "inflammation" in narrative.lower()

    def test_narrative_is_string(self):
        """Return type must always be str — never None."""
        svc = NarrativeService()
        with patch("src.services.narrative_service.sanitization_service") as mock_san:
            mock_san.sanitize_encounter.return_value = {}
            result = svc.generate_technical_summary({}, self._make_encounter())
        assert isinstance(result, str)
