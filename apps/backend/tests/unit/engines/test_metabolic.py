import pytest
from src.engines.specialty.metabolic import MetabolicPrecisionMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return MetabolicPrecisionMotor()


def test_metabolic_validate_missing(motor):
    """T-MET-01: Validation fails without glucose, HbA1c, or BMI."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is False


def test_metabolic_validate_success(motor):
    """T-MET-02: Validation passes with glucose observation."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[Observation(code="2339-0", value=100)],
        metadata={"sex": "M"},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_metabolic_sick_fat(motor):
    """T-MET-03: Adiposopatía Inflamatoria - motor returns findings for high BMI + inflammation."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110, insulin_uu_ml=25),
        observations=[
            Observation(code="30522-7", value=1.5),
        ],
        metadata={"sex": "M", "bmi": 32},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_metabolic_sarcopenic_obesity(motor):
    """T-MET-04: Sarcopenic obesity (low SMI)."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=90, insulin_uu_ml=10),
        observations=[
            Observation(code="SMI-001", value=6.0),
        ],
        metadata={"sex": "male", "bmi": 30},
    )
    result = motor.compute(enc)
    assert "Sarcopénica" in result.calculated_value


def test_metabolic_fib4(motor):
    """T-MET-05: FIB-4 for ectopic fat."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        observations=[
            Observation(code="AGE-001", value=50),
            Observation(code="29230-0", value=35),
            Observation(code="22538-3", value=40),
            Observation(code="PLT-001", value=150),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_metabolic_stable(motor):
    """T-MET-06: No findings = stable."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=90),
        observations=[],
        metadata={"sex": "M", "bmi": 24},
    )
    result = motor.compute(enc)
    assert result.calculated_value == "Metabólicamente Estable"
