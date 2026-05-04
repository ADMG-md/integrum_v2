"""
Golden Motor Tests: DrugInteractionMotor (IEC 62304 V&V)
========================================================
Tests for drug-drug interactions, contraindications, and renal dosing.
"""

import pytest
from src.engines.specialty.drug_interaction import DrugInteractionMotor
from src.engines.domain import Encounter, Observation, MedicationStatement, Condition
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema


@pytest.fixture
def motor():
    return DrugInteractionMotor()


def _make_encounter(meds, conditions=None, e_gfr=None, pregnancy=None):
    obs = []
    if e_gfr is not None:
        obs.append(Observation(code="EGFR-001", value=e_gfr))
    metadata = {}
    if pregnancy:
        metadata["pregnancy_status"] = pregnancy

    return Encounter(
        id="test-drug",
        demographics=DemographicsSchema(age_years=50, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        medications=meds,
        conditions=conditions or [],
        observations=obs,
        metadata=metadata,
    )


def test_drug_validate_missing(motor):
    """Validation fails without medications."""
    enc = _make_encounter(meds=[])
    valid, msg = motor.validate(enc)
    assert valid is False


def test_drug_drug_interaction(motor):
    """Test major interaction between GLP-1 and Insulin."""
    meds = [
        MedicationStatement(code="dummy1", name="semaglutide"),
        MedicationStatement(code="dummy2", name="insulin_glargine"),
    ]
    enc = _make_encounter(meds=meds)
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "major_alerts" in result.metadata
    assert len(result.metadata["major_alerts"]) >= 1
    assert any("Hypoglycemia risk" in alert for alert in result.metadata["major_alerts"])


def test_drug_contraindication(motor):
    """Test absolute contraindication based on condition (C73 Thyroid cancer + GLP-1)."""
    meds = [MedicationStatement(code="dummy1", name="semaglutide")]
    conditions = [Condition(code="C73", title="Malignant neoplasm of thyroid gland")]
    enc = _make_encounter(meds=meds, conditions=conditions)
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert len(result.metadata["critical_alerts"]) >= 1
    assert any("CONTRAINDICACIÓN" in alert for alert in result.metadata["critical_alerts"])


def test_drug_renal_dosing_contraindicated(motor):
    """Test renal dosing adjustment: Metformin with eGFR < 30."""
    meds = [MedicationStatement(code="dummy1", name="metformin")]
    enc = _make_encounter(meds=meds, e_gfr=20.0)
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert len(result.metadata["critical_alerts"]) >= 1
    assert any("Ajuste renal" in alert and "Contraindicated" in alert for alert in result.metadata["critical_alerts"])


def test_drug_pregnancy_safety(motor):
    """Test teratogenic drug (Atorvastatin, Cat X) with positive pregnancy."""
    meds = [MedicationStatement(code="dummy1", name="atorvastatin")]
    enc = _make_encounter(meds=meds, pregnancy="positive")
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert len(result.metadata["critical_alerts"]) >= 1
    assert any("RIESGO TERATOGÉNICO" in alert for alert in result.metadata["critical_alerts"])


def test_drug_no_interactions(motor):
    """Test normal medication with no interactions."""
    meds = [MedicationStatement(code="dummy1", name="metformin")]
    enc = _make_encounter(meds=meds, e_gfr=90.0)
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert len(result.metadata["critical_alerts"]) == 0
    assert len(result.metadata["major_alerts"]) == 0
