import pytest
from src.engines.specialty.cardiometabolic import CMIMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return CMIMotor()


def test_cmi_validate_missing(motor):
    """T-CMI-01: Validation fails without required data."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is False


def test_cmi_validate_success(motor):
    """T-CMI-02: Validation passes with all data."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=150, hdl_mg_dl=40),
        observations=[
            Observation(code="WAIST-001", value=90),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "M"},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_cmi_male_high(motor):
    """T-CMI-03: Male with CMI > 0.7 = high risk."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=200, hdl_mg_dl=35),
        observations=[
            Observation(code="WAIST-001", value=100),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "male"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "ELEVADO" in result.calculated_value


def test_cmi_male_low(motor):
    """T-CMI-04: Male with CMI < 0.7 = low risk."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=80, hdl_mg_dl=60),
        observations=[
            Observation(code="WAIST-001", value=70),
            Observation(code="8302-2", value=175),
        ],
        metadata={"sex": "M"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "dentro de rango" in result.calculated_value


def test_cmi_female_high(motor):
    """T-CMI-05: Female with CMI > 0.5 = high risk."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=180, hdl_mg_dl=40),
        observations=[
            Observation(code="WAIST-001", value=85),
            Observation(code="8302-2", value=160),
        ],
        metadata={"sex": "F"},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "CONFIRMED_ACTIVE"
    assert "ELEVADO" in result.calculated_value


def test_cmi_sex_difference(motor):
    """T-CMI-06: Same CMI value shows sex-based threshold difference."""
    enc_male = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=150, hdl_mg_dl=40),
        observations=[
            Observation(code="WAIST-001", value=90),
            Observation(code="8302-2", value=170),
        ],
        metadata={"sex": "male"},
    )
    enc_female = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=50, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(triglycerides_mg_dl=150, hdl_mg_dl=40),
        observations=[
            Observation(code="WAIST-001", value=90),
            Observation(code="8302-2", value=160),
        ],
        metadata={"sex": "female"},
    )
    result_male = motor.compute(enc_male)
    result_female = motor.compute(enc_female)
    assert result_male.metadata["threshold"] == 0.7
    assert result_female.metadata["threshold"] == 0.5
