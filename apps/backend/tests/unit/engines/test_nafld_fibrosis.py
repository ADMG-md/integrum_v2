"""
Golden Motor Tests: NFSMotor (IEC 62304 V&V)
==============================================
Tests for NAFLD Fibrosis Score.
Test IDs: T-NFS-01 through T-NFS-04.
Evidence: Angulo et al., 2007.
"""

import pytest
from src.engines.specialty.nafld_fibrosis import NFSMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

@pytest.fixture
def motor():
    return NFSMotor()

def test_nfs_high_risk(motor):
    """T-NFS-01: High fibrosis risk."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=65, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            ast_u_l=80, alt_u_l=40, platelets_k_u_l=100, albumin_g_dl=3.0, glucose_mg_dl=150
        ),
        observations=[
            Observation(code="29463-7", value=110),
            Observation(code="8302-2", value=170),
        ]
    )
    result = motor.compute(enc)
    assert result.metadata["category"] == "high"
    assert result.estado_ui == "CONFIRMED_ACTIVE"
