import pytest
from src.engines.domain import (
    Encounter, Observation, DemographicsSchema,
    MetabolicPanelSchema, ActionItem
)
from src.domain.models import ClinicalHistory
from src.schemas.encounter import MetabolicPanelSchema
from src.engines.specialty.mens_health import MensHealthMotor

def _male_enc(**overrides) -> Encounter:
    obs = overrides.pop("observations", [])
    history_kw = overrides.pop("history_kwargs", {"onset_trigger": "unknown", "pregnancy_status": "not_applicable"})
    history = ClinicalHistory(**history_kw)
    metabolic = overrides.pop("metabolic_panel", MetabolicPanelSchema())
    cardio = overrides.pop("cardio_panel", MetabolicPanelSchema())
    demo = DemographicsSchema(age_years=50, gender="male", weight_kg=90, height_cm=175)
    
    return Encounter(
        id="MEN-01",
        demographics=overrides.pop("demographics", demo),
        metabolic_panel=metabolic,
        cardio_panel=cardio,
        history=history,
        observations=obs,
        metadata={"sex": "male"},
        **overrides
    )

motor = MensHealthMotor()

def test_validation():
    enc_f = _male_enc()
    enc_f.metadata = {"sex": "female"}
    v, _ = motor.validate(enc_f)
    assert not v

def test_hypogonadism_primary():
    enc = _male_enc(
        history_kwargs={"has_erectile_dysfunction": True},
        metabolic_panel=MetabolicPanelSchema(testosterone_total_ng_dl=250, lh_u_l=10)
    )
    res = motor.compute(enc)
    assert "Hipogonadismo" in res.calculated_value
    assert "Primario" in res.calculated_value
    assert any("falla testicular" in a.rationale for a in res.action_checklist)

def test_hypogonadism_secondary():
    enc = _male_enc(
        history_kwargs={"has_erectile_dysfunction": True},
        metabolic_panel=MetabolicPanelSchema(testosterone_total_ng_dl=250, lh_u_l=2.5)
    )
    res = motor.compute(enc)
    assert "Secundario" in res.calculated_value
    assert any("LH inapropiadamente baja" in a.rationale for a in res.action_checklist)

def test_trt_safety_hematocrit_veto():
    enc = _male_enc(
        observations=[Observation(code="HCT-001", value=55)],
        history_kwargs={"has_erectile_dysfunction": True},
        metabolic_panel=MetabolicPanelSchema(testosterone_total_ng_dl=200)
    )
    res = motor.compute(enc)
    assert any("HARD STOP" in a.task and "Hematocrito > 54" in a.task for a in res.action_checklist)

def test_trt_safety_psa_veto():
    enc = _male_enc(
        history_kwargs={"has_erectile_dysfunction": True},
        metabolic_panel=MetabolicPanelSchema(testosterone_total_ng_dl=200, psa_ng_ml=5.0)
    )
    res = motor.compute(enc)
    assert any("HARD STOP" in a.task and "PSA" in a.rationale for a in res.action_checklist)

def test_trt_safety_osa_warning():
    enc = _male_enc(
        history_kwargs={"has_erectile_dysfunction": True, "has_osa": True},
        metabolic_panel=MetabolicPanelSchema(testosterone_total_ng_dl=200)
    )
    res = motor.compute(enc)
    assert any("Verificar CPAP" in a.task for a in res.action_checklist)
