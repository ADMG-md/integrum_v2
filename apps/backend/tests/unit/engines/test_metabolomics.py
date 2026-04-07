import pytest
from src.engines.specialty.metabolomics import DeepMetabolicProxyMotor
from src.engines.domain import Encounter, Observation
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return DeepMetabolicProxyMotor()


def test_metabolomics_validate_missing(motor):
    """T-META-01: Validation fails without any shadow markers."""
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


def test_metabolomics_validate_success(motor):
    """T-META-02: Validation passes with any shadow marker."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="GGT-001", value=30)],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_metabolomics_ggt_elevated(motor):
    """T-META-03: GGT > 40 (male) = oxidative stress."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="GGT-001", value=50)],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Estrés Oxidativo" in result.calculated_value


def test_metabolomics_ferritin_elevated(motor):
    """T-META-04: Ferritin > 300 (male) = metainflammation."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="FER-001", value=350)],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Metainflamación" in result.calculated_value


def test_metabolomics_uric_acid(motor):
    """T-META-05: Uric acid > 6.5 = mitochondrial dysfunction."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="UA-001", value=7.0)],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Mitocondrial" in result.calculated_value


def test_metabolomics_tg_hdl_ratio(motor):
    """T-META-06: TG/HDL > 3.0 (male) = atherogenic dyslipidemia."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[
            Observation(code="2571-8", value=150),
            Observation(code="2085-9", value=40),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert (
        "Aterogénica" in result.calculated_value
        or "Fenotipo B" in result.calculated_value
    )


def test_metabolomics_bcaa(motor):
    """T-META-07: BCAA detected = insulin resistance signature."""
    enc = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="BCAA-ISO-001", value=0.8)],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Resistencia a la Insulina" in result.calculated_value


def test_metabolomics_glyca(motor):
    """T-META-08: GlycA = epigenetic aging proxy."""
    enc = Encounter(
        id="8",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[Observation(code="GLYCA-001", value=400)],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Epigenético" in result.calculated_value


def test_metabolomics_female_thresholds(motor):
    """T-META-09: Female has different GGT/ferritin thresholds."""
    enc = Encounter(
        id="9",
        demographics=DemographicsSchema(age_years=50, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[
            Observation(code="GGT-001", value=30),
            Observation(code="FER-001", value=150),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.calculated_value is not None


def test_metabolomics_no_findings(motor):
    """T-META-10: No findings = no deep risk."""
    enc = Encounter(
        id="10",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[
            Observation(code="GGT-001", value=20),
            Observation(code="FER-001", value=100),
        ],
        metadata={},
    )
    result = motor.compute(enc)
    assert "Sin firmas" in result.calculated_value
