import pytest
from src.engines.obesity_master import ObesityMasterMotor, ObesityClinicalStoryInput

def test_obesity_master_classic_obesity():
    data = ObesityClinicalStoryInput(
        acosta_phenotype="Hungry_Brain",
        eoss_stage=3,
        sarcopenia_risk="low",
        bmi_kg_m2=34.5,
        waist_cm=110,
        cvd_risk_category="intermediate"
    )
    motor = ObesityMasterMotor()
    out = motor(data)
    
    assert out.discordant_profile is False
    assert "Hungry_Brain" in out.clinical_profile
    assert "EOSS 3" in out.clinical_profile
    assert "daño establecido" in out.headline_verdict.lower()

def test_obesity_master_discordant_mho_high_cvd():
    # R-06 Audit: MHO with High CVD Risk MUST NOT trigger automated discordance (FDA 2026 CDS rule)
    data = ObesityClinicalStoryInput(
        acosta_phenotype="Hungry_Brain",
        eoss_stage=1,
        sarcopenia_risk="low",
        bmi_kg_m2=32,
        waist_cm=105,
        cvd_risk_category="high"
    )
    motor = ObesityMasterMotor()
    out = motor(data)
    
    assert out.discordant_profile is False
    assert "Hungry_Brain" in out.clinical_profile
    assert "high" in out.explanation

def test_obesity_master_sarcopenic_obesity():
    # Sarcopenic Obesity: High Sarcopenia + BMI >= 27
    data = ObesityClinicalStoryInput(
        acosta_phenotype="Hungry_Gut",
        eoss_stage=1,
        sarcopenia_risk="high",
        bmi_kg_m2=29,
        waist_cm=102,
        cvd_risk_category="intermediate"
    )
    motor = ObesityMasterMotor()
    out = motor(data)
    
    assert out.discordant_profile is True
    assert "Obesidad sarcopénica" in (out.discordance_reason or "")
