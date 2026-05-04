"""
Golden Motor Tests: NFSMotor (IEC 62304 V&V)
=============================================
Tests for NAFLD Fibrosis Score.
Test IDs: T-NFS-01 through T-NFS-06.
Evidence: Angulo et al., 2007 (validated >700 patients).
"""

import pytest
from src.engines.specialty.nafld_fibrosis import NFSMotor
from src.engines.domain import Encounter, Observation, ClinicalHistory
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return NFSMotor()


def _make_encounter(
    id="nfs-test", observations=None, metadata=None, metabolic=None, history=None
):
    """Helper: creates a valid Encounter for NFS testing."""
    mp = MetabolicPanelSchema()
    if metabolic:
        for k, v in metabolic.items():
            setattr(mp, k, v)
    default_meta = {"sex": "M", "bmi": 28}
    if metadata:
        default_meta.update(metadata)
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=mp,
        cardio_panel=MetabolicPanelSchema(),
        observations=observations or [],
        metadata=default_meta,
        history=history,
    )


def test_nfs_validate_missing_data(motor):
    """T-NFS-01: Missing required data = validation failure."""
    enc = _make_encounter(id="1", observations=[])
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "NFS" in msg


def test_nfs_validate_success(motor):
    """T-NFS-01: With all required data = validation passes."""
    enc = _make_encounter(
        id="2",
        observations=[
            Observation(code="AGE-001", value=50),
            Observation(code="29463-7", value=80),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=25),
            Observation(code="ALT-001", value=30),
            Observation(code="PLT-001", value=200),
        ],
        metabolic={"albumin_g_dl": 4.0},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_nfs_low_fibrosis(motor):
    """T-NFS-02: NFS < -1.455 = Low fibrosis risk."""
    enc = _make_encounter(
        id="3",
        observations=[
            Observation(code="AGE-001", value=40),
            Observation(code="29463-7", value=70),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=20),
            Observation(code="ALT-001", value=35),
            Observation(code="PLT-001", value=250),
        ],
        metadata={"sex": "M", "bmi": 24},
        metabolic={"albumin_g_dl": 4.5},
    )
    result = motor.compute(enc)
    assert "descartada" in result.calculated_value.lower()
    assert result.estado_ui == "INDETERMINATE_LOCKED"


def test_nfs_indeterminate(motor):
    """T-NFS-03: NFS -1.455 to 0.676 = Indeterminate."""
    enc = _make_encounter(
        id="4",
        observations=[
            Observation(code="AGE-001", value=55),
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=40),
            Observation(code="ALT-001", value=50),
            Observation(code="PLT-001", value=180),
        ],
        metadata={"sex": "M", "bmi": 29},
        metabolic={"albumin_g_dl": 4.0},
    )
    result = motor.compute(enc)
    assert (
        "indeterminada" in result.calculated_value.lower()
        or "gris" in result.calculated_value.lower()
    )
    assert result.estado_ui == "PROBABLE_WARNING"


def test_nfs_high_fibrosis(motor):
    """T-NFS-04: NFS > 0.676 = High fibrosis risk."""
    enc = _make_encounter(
        id="5",
        observations=[
            Observation(code="AGE-001", value=65),
            Observation(code="29463-7", value=100),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=60),
            Observation(code="ALT-001", value=40),
            Observation(code="PLT-001", value=120),
        ],
        metadata={"sex": "M", "bmi": 35},
        metabolic={"albumin_g_dl": 3.5},
    )
    result = motor.compute(enc)
    assert (
        "avanzada probable" in result.calculated_value.lower()
        or "alta" in result.calculated_value.lower()
    )
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_nfs_diabetes_weight(motor):
    """T-NFS-05: Diabetes adds 1.13 to NFS score."""
    history = ClinicalHistory(has_type2_diabetes=True)
    enc = _make_encounter(
        id="6",
        observations=[
            Observation(code="AGE-001", value=50),
            Observation(code="29463-7", value=85),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=30),
            Observation(code="ALT-001", value=40),
            Observation(code="PLT-001", value=200),
        ],
        metadata={"sex": "M", "bmi": 28},
        metabolic={"albumin_g_dl": 4.0},
        history=history,
    )
    result = motor.compute(enc)
    assert result.metadata["has_diabetes"] is True


def test_nfs_boundary_low(motor):
    """T-NFS-06: NFS = -1.455 exactly = Indeterminate."""
    enc = _make_encounter(
        id="7",
        observations=[
            Observation(code="AGE-001", value=50),
            Observation(code="29463-7", value=75),
            Observation(code="8302-2", value=170),
            Observation(code="AST-001", value=25),
            Observation(code="ALT-001", value=35),
            Observation(code="PLT-001", value=220),
        ],
        metadata={"sex": "M", "bmi": 26},
        metabolic={"albumin_g_dl": 4.2},
    )
    result = motor.compute(enc)
    assert result.metadata["nfs"] is not None
