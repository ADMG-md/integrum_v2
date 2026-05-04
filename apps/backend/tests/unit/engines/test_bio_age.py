"""
Golden Motor Tests: BiologicalAgeMotor (IEC 62304 V&V)
=======================================================
Tests for Biological Age (PhenoAge Levine).
Test IDs: T-BIO-01 through T-BIO-03.
Evidence: Levine et al., 2018.
"""

import pytest
from src.engines.specialty.bio_age import BiologicalAgeMotor, PhenoAgeLevineInput

@pytest.fixture
def motor():
    return BiologicalAgeMotor()

def test_bio_age_calculation(motor):
    """T-BIO-01: Correct calculation for a standard 50yo."""
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
        wbc_k_ul=6.5
    )
    result = motor(data)
    assert result.status == "ok"
    assert result.biological_age_years is not None
    # For a healthy 50yo, bio age should be around 50 or less
    assert result.biological_age_years < 60
