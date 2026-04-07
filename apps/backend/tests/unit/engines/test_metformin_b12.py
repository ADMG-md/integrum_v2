"""
Golden Motor Tests: MetforminB12Motor (IEC 62304 V&V)
=======================================================
Tests for Metformin-induced B12 Deficiency Monitoring.
Test IDs: T-MET-01 through T-MET-06.
Evidence: ADA Standards of Care 2024.
"""

import pytest
from src.engines.specialty.metformin_b12 import MetforminB12Motor
from src.engines.domain import Encounter, Observation, MedicationStatement
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return MetforminB12Motor()


def _make_encounter(id="met-test", medications=None, observations=None, b12_value=None):
    """Helper: creates a valid Encounter for Metformin B12 testing."""
    mp = MetabolicPanelSchema()
    if b12_value is not None:
        mp.vitamin_b12_pg_ml = b12_value
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=mp,
        cardio_panel=CardioPanelSchema(),
        observations=observations or [],
        medications=medications or [],
        metadata={},
    )


def test_metformin_validate_no_metformin(motor):
    """T-MET-01: No metformin = validation failure."""
    enc = _make_encounter(id="1", medications=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "No metformin" in msg


def test_metformin_validate_with_metformin(motor):
    """T-MET-01: With metformin = validation passes."""
    enc = _make_encounter(
        id="2",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_metformin_b12_deficiency(motor):
    """T-MET-02: B12 < 200 pg/mL = deficiency confirmed."""
    enc = _make_encounter(
        id="3",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=150,
    )
    result = motor.compute(enc)
    assert "Deficiencia" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert result.metadata["b12_value"] == 150
    critical_actions = [a for a in result.action_checklist if a.priority == "critical"]
    assert len(critical_actions) > 0


def test_metformin_b12_borderline(motor):
    """T-MET-03: B12 200-300 pg/mL = borderline, needs functional testing."""
    enc = _make_encounter(
        id="4",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=250,
    )
    result = motor.compute(enc)
    assert "limtrofe" in result.calculated_value
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.metadata["b12_value"] == 250


def test_metformin_b12_adequate(motor):
    """T-MET-04: B12 > 300 pg/mL = adequate."""
    enc = _make_encounter(
        id="5",
        medications=[
            MedicationStatement(code="MET", name="GLUCOPHAGE", is_active=True)
        ],
        b12_value=400,
    )
    result = motor.compute(enc)
    assert "adecuado" in result.calculated_value
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_metformin_b12_not_available(motor):
    """T-MET-05: No B12 available = prompt screening."""
    enc = _make_encounter(
        id="6",
        medications=[
            MedicationStatement(code="MET", name="METFORMINA", is_active=True)
        ],
        b12_value=None,
    )
    result = motor.compute(enc)
    assert "no disponible" in result.calculated_value
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.confidence == 0.95
    actions = [
        a
        for a in result.action_checklist
        if "B12" in a.task or "screening" in a.task.lower()
    ]
    assert len(actions) > 0


def test_metformin_b12_boundary_200(motor):
    """T-MET-06: B12 = 200 exactly should be borderline, not deficiency."""
    enc = _make_encounter(
        id="7",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=200,
    )
    result = motor.compute(enc)
    assert "limtrofe" in result.calculated_value


def test_metformin_b12_boundary_300(motor):
    """T-MET-06: B12 = 300 exactly should be adequate."""
    enc = _make_encounter(
        id="8",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=300,
    )
    result = motor.compute(enc)
    assert "adecuado" in result.calculated_value
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_metformin_b12_not_available(motor):
    """T-MET-05: No B12 available = prompt screening."""
    enc = _make_encounter(
        id="6",
        medications=[
            MedicationStatement(code="MET", name="METFORMINA", is_active=True)
        ],
        b12_value=None,
    )
    result = motor.compute(enc)
    assert "no disponible" in result.calculated_value
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.confidence == 0.95
    # Should have action item for screening
    actions = [
        a
        for a in result.action_checklist
        if "B12" in a.task or "screening" in a.task.lower()
    ]
    assert len(actions) > 0


def test_metformin_b12_boundary_200(motor):
    """T-MET-06: B12 = 200 exactly should be borderline, not deficiency."""
    enc = _make_encounter(
        id="7",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=200,
    )
    result = motor.compute(enc)
    # 200 is not < 200, so it goes to borderline (200-300)
    assert "limtrofe" in result.calculated_value


def test_metformin_b12_boundary_300(motor):
    """T-MET-06: B12 = 300 exactly should be adequate."""
    enc = _make_encounter(
        id="8",
        medications=[MedicationStatement(code="MET", name="Metformin", is_active=True)],
        b12_value=300,
    )
    result = motor.compute(enc)
    # 300 is not < 300, so it's adequate
    assert "adecuado" in result.calculated_value
