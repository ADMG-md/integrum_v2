"""
Golden Motor Tests: CVDReclassifierMotor (IEC 62304 V&V)
=======================================================
Tests for CVD Risk Reclassification (Statin Eligibility).
Test IDs: T-CVD-01 through T-CVD-06.
Evidence: ACC/AHA 2018 Cholesterol Guidelines.
"""

import pytest
from src.engines.specialty.cvd_reclassifier import CVDReclassifierMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return CVDReclassifierMotor()


def test_cvd_validate_missing_ldl(motor):
    """T-CVD-01: No LDL = validation failure."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[],
        metadata={"sex": "M"},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is False
    assert "LDL" in msg


def test_cvd_validate_success(motor):
    """T-CVD-01: With LDL = validation passes."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ldl_mg_dl=130),
        observations=[],
        metadata={"sex": "M"},
    )
    is_valid, msg = motor.validate(enc)
    assert is_valid is True


def test_cvd_ldl_190_plus(motor):
    """T-CVD-02: LDL >= 190 = High intensity statin indicated."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ldl_mg_dl=210),
        observations=[],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert "ALTA intensidad" in result.calculated_value
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_cvd_multiple_risk_factors(motor):
    """T-CVD-03: 2+ risk factors = Statin indicated."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(hs_crp_mg_l=2.5, ldl_mg_dl=160, triglycerides_mg_dl=180),
        observations=[],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["n_factors"] >= 2
    assert result.estado_ui == "CONFIRMED_ACTIVE"


def test_cvd_single_risk_factor(motor):
    """T-CVD-04: 1 risk factor = Consider statin."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ldl_mg_dl=140, triglycerides_mg_dl=180),
        observations=[],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["n_factors"] == 1
    assert result.estado_ui == "PROBABLE_WARNING"


def test_cvd_no_risk_factors(motor):
    """T-CVD-05: No risk factors = No statin indicated."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ldl_mg_dl=100),
        observations=[],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "no indicada" in result.calculated_value.lower()


def test_cvd_ckd_risk_factor(motor):
    """T-CVD-06: CKD is a risk-enhancing factor."""
    enc = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(ldl_mg_dl=140, triglycerides_mg_dl=180),
        observations=[Observation(code="EGFR-001", value=45)],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["n_factors"] >= 1


def test_cvd_metabolic_syndrome(motor):
    """T-CVD-06: Metabolic syndrome = risk factor."""
    enc = Encounter(
        id="8",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=105, 
            ldl_mg_dl=130, triglycerides_mg_dl=160, hdl_mg_dl=35
        ),
        observations=[
            Observation(code="WAIST-001", value=110),
            Observation(code="8480-6", value=135),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.metadata["n_factors"] >= 1
