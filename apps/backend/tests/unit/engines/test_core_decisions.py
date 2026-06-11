import pytest
from src.engines.domain import Encounter, Observation, DemographicsSchema, MetabolicPanelSchema, DecisionContext
from src.engines.core_decisions import CoreClinicalDecisionEngine


@pytest.fixture
def empty_encounter():
    return Encounter(
        id="test",
        demographics=DemographicsSchema(age_years=45.0, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[]
    )

@pytest.fixture
def core_engine():
    return CoreClinicalDecisionEngine()

def test_cd_cal_01_and_cd_pro_01_slow_burn(core_engine, empty_encounter):
    # Test triggering of Moderado deficit and Alta protein on Slow Burn / Sarcopenia
    ctx = DecisionContext(
        axis_a_code="A3",
        is_slow_burn=True,
        has_sarcopenic_risk=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    codes = [r["recommendation_code"] for r in recommendations]
    assert "DEFICIT_MODERADO" in codes
    assert "PROTEINA_ALTA" in codes
    
    # Assert proper Pydantic schema usage
    def_rec = next(r for r in recommendations if r["recommendation_code"] == "DEFICIT_MODERADO")
    assert def_rec["domain"] == "nutrition"
    assert def_rec["recommendation_type"] == "treatment"
    assert def_rec["status"] == "active"
    assert "300-500" in def_rec["audit_payload"]["caloric_deficit_target_kcal"]

def test_cd_cal_01_fallback_aggressive(core_engine, empty_encounter):
    # Test fallback to Aggressive deficit on normal metabolic phenotype
    ctx = DecisionContext(
        axis_a_code="A0",
        is_slow_burn=False
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    codes = [r["recommendation_code"] for r in recommendations]
    assert "DEFICIT_AGRESIVO" in codes
    assert "PROTEINA_ESTANDAR" in codes

def test_cd_pro_01_ckd_override(core_engine, empty_encounter):
    # Test protein requirement override due to CKD
    ctx = DecisionContext(
        axis_a_code="A3",
        has_advanced_ckd=True,
        is_slow_burn=True # Even with slow burn, CKD should inhibit high protein
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    pro_rec = next(r for r in recommendations if r["requirement_id"] == "CD-PRO-01")
    assert pro_rec["recommendation_code"] == "PROTEINA_MODERADA_CKD"
    assert pro_rec["status"] == "modified"
    assert pro_rec["suppression_reason"] is not None

def test_cd_beh_01_cbt_referral(core_engine, empty_encounter):
    # Test behavioral focus derivation for uncontrolled eating
    ctx = DecisionContext(
        axis_b_code="B1",
        has_uncontrolled_eating=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    codes = [r["recommendation_code"] for r in recommendations]
    assert "DERIVACION_CBT" in codes

def test_cd_phm_01_pharmacology_glp1(core_engine, empty_encounter):
    # Uncontrolled eating triggers GLP-1 priority
    ctx = DecisionContext(
        axis_b_code="B1",
        has_uncontrolled_eating=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    pharm = next(r for r in recommendations if r["requirement_id"] == "CD-PHM-01")
    assert pharm["recommendation_code"] == "PHARM_CLASS_GLP1"

def test_cd_phm_01_pharmacology_bupropion(core_engine, empty_encounter):
    # Emotional eating without uncontrolled eating triggers Bupropion/Naltrexone
    ctx = DecisionContext(
        axis_b_code="B1",
        has_emotional_eating=True,
        has_affective_traits=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    pharm = next(r for r in recommendations if r["requirement_id"] == "CD-PHM-01")
    assert pharm["recommendation_code"] == "PHARM_CLASS_BUPROPION_NALTREXONE"

def test_cd_slp_01_sleep_hygiene(core_engine, empty_encounter):
    # Severe insomnia prioritizes sleep treatment
    ctx = DecisionContext(
        axis_b_code="B1",
        has_clinical_insomnia=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    codes = [r["recommendation_code"] for r in recommendations]
    assert "PRIORIZAR_SUEÑO" in codes

def test_cd_rsk_01_early_failure_risk(core_engine, empty_encounter):
    # Slow burn + Uncontrolled eating + Suboptimal C trajectory
    ctx = DecisionContext(
        axis_a_code="A3",
        axis_b_code="B1",
        axis_c_code="C2",
        is_slow_burn=True,
        has_uncontrolled_eating=True,
        has_suboptimal_c=True
    )
    result = core_engine.compute_from_context(empty_encounter, ctx)
    recommendations = result.metadata["recommendations"]
    
    rsk = next(r for r in recommendations if r["requirement_id"] == "CD-RSK-01")
    assert rsk["recommendation_code"] == "ALERTA_FRACASO_TEMPRANO_ALTO"
