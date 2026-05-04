import pytest
from src.engines.domain import (
    Encounter, Observation, DemographicsSchema,
    MetabolicPanelSchema, ActionItem
)
from src.schemas.encounter import MetabolicPanelSchema
from src.domain.models import ClinicalHistory
from src.engines.specialty.womens_health import WomensHealthMotor

def _female_enc(**overrides) -> Encounter:
    obs = overrides.pop("observations", [])
    history_kw = overrides.pop("history_kwargs", {"onset_trigger": "unknown", "pregnancy_status": "not_applicable"})
    if "pregnancy_status" not in history_kw:
        history_kw["pregnancy_status"] = "not_applicable"
    if "onset_trigger" not in history_kw:
        history_kw["onset_trigger"] = "unknown"
    history = ClinicalHistory(**history_kw)
    metabolic = overrides.pop("metabolic_panel", MetabolicPanelSchema())
    cardio = overrides.pop("cardio_panel", MetabolicPanelSchema())
    demo = DemographicsSchema(age_years=35, gender="female", weight_kg=70, height_cm=160)
    
    return Encounter(
        id="WOMEN-01",
        demographics=overrides.pop("demographics", demo),
        metabolic_panel=metabolic,
        cardio_panel=cardio,
        history=history,
        observations=obs,
        **overrides
    )

motor = WomensHealthMotor()

def test_validation():
    enc_m = _female_enc()
    enc_m.demographics.gender = "male"
    enc_m.metadata = {"sex": "male"}
    v, _ = motor.validate(enc_m)
    assert not v

    enc_f = _female_enc()
    enc_f.metadata = {"sex": "female"}
    v2, _ = motor.validate(enc_f)
    assert v2

def test_pcos_metabolic():
    enc = _female_enc(
        history_kwargs={"cycle_regularity": "irregular", "ferriman_gallwey_score": 10},
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=100, insulin_mu_u_ml=20)
    )
    res = motor.compute(enc)
    assert "SOP Confirmado" in res.calculated_value
    assert "Fenotipo Metabólico" in res.calculated_value
    assert any("Metformina" in a.rationale for a in res.action_checklist)

def test_pcos_adrenal():
    enc = _female_enc(
        observations=[Observation(code="DHEAS-001", value=350)],
        history_kwargs={"cycle_regularity": "irregular", "ferriman_gallwey_score": 10},
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=90, insulin_mu_u_ml=5)
    )
    res = motor.compute(enc)
    assert "SOP Fenotipo Adrenal" in res.calculated_value
    assert any("Espironolactona" in a.rationale for a in res.action_checklist)

def test_hrt_safety_gate_breast_cancer():
    enc = _female_enc(
        observations=[Observation(code="Hx-BRCA", value="yes")],
        history_kwargs={"menopausal_status": "post"}
    )
    res = motor.compute(enc)
    assert any("CONTRAINDICADA" in a.task and "Cáncer" in a.rationale for a in res.action_checklist)

def test_hrt_safety_gate_vte():
    enc = _female_enc(
        observations=[Observation(code="Hx-VTE", value="yes")],
        history_kwargs={"menopausal_status": "post"}
    )
    res = motor.compute(enc)
    assert any("Transdérmica" in a.task for a in res.action_checklist)

def test_hrt_window_closed():
    demo = DemographicsSchema(age_years=65, gender="female", weight_kg=70, height_cm=160)
    enc = _female_enc(
        demographics=demo,
        history_kwargs={"menopausal_status": "post"}
    )
    res = motor.compute(enc)
    assert any("No iniciar HRT" in a.task and "Edad" in a.rationale for a in res.action_checklist)

def test_premature_menopause():
    enc = _female_enc(
        observations=[Observation(code="MENOPAUSE-AGE", value="38")],
        history_kwargs={"menopausal_status": "post"}
    )
    res = motor.compute(enc)
    assert "POI" in res.calculated_value
    assert any("HRT mandatoria" in a.task for a in res.action_checklist)
