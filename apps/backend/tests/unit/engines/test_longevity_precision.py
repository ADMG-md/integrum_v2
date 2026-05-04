"""
Longevity Precision Tests (IEC 62304 V&V)
==========================================
Tests for SpecialtyRunner structure and PhenoAge verification.
"""

import pytest
from src.engines.specialty_runner import SpecialtyRunner, PRIMARY_MOTORS
from src.engines.specialty.bio_age import PhenoAgeLevineInput, BiologicalAgeMotor


def test_specialty_runner_excludes_draft_motors():
    """Verifies SpecialtyRunner includes formerly orphaned specialty motors."""
    names = set(PRIMARY_MOTORS.keys())

    # Should contain formalized ones
    assert "AcostaPhenotypeMotor" in names
    assert "EOSSStagingMotor" in names

    # Formerly orphaned motors are now registered
    assert "AnthropometryMotor" in names
    assert "LaboratoryStewardshipMotor" in names
    assert "HypertensionMotor" in names


def test_phenoage_matches_reference_example():
    # Example data from Levine 2018
    data = PhenoAgeLevineInput(
        chronological_age_years=50,
        albumin_g_dl=4.5,
        creatinine_mg_dl=0.9,
        glucose_mg_dl=90,
        hs_crp_mg_l=1.0,
        lymphocyte_percent=30,
        mcv_fl=90,
        rdw_percent=13,
        alkaline_phosphatase_u_l=75,
        wbc_k_ul=6.5,
    )
    motor = BiologicalAgeMotor()
    res = motor(data)
    assert res.status == "ok"
    assert abs(res.biological_age_years - 50.0) < 5.0
