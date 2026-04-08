import pytest
from src.engines.specialty.lab_suggestion import LaboratorySuggestionMotor
from src.engines.domain import Encounter, Observation, Condition, MedicationStatement
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)


@pytest.fixture
def motor():
    return LaboratorySuggestionMotor()


def test_lab_suggest_validate_always_passes(motor):
    """T-LAB-01: Validation always passes."""
    enc = Encounter(
        id="1",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    valid, msg = motor.validate(enc)
    assert valid is True


def test_lab_suggest_full_panel(motor):
    """T-LAB-02: Full metabolic/lipid panel = minimal suggestions."""
    enc = Encounter(
        id="2",
        demographics=DemographicsSchema(age_years=35, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=100,
            hba1c_percent=5.5,
            creatinine_mg_dl=1.0,
            uric_acid_mg_dl=5.0,
            alt_u_l=25,
            ast_u_l=20,
            ggt_u_l=25,
            ferritin_ng_ml=100,
            vitamin_d_ng_ml=30,
            tsh_uIU_ml=2.0,
            hs_crp_mg_l=1.0,
        ),
        cardio_panel=CardioPanelSchema(
            hdl_mg_dl=50,
            triglycerides_mg_dl=120,
            ldl_mg_dl=100,
        ),
        conditions=[],
        medications=[],
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "INDETERMINATE_LOCKED"
    assert "completo" in result.explanation.lower()


def test_lab_suggest_missing_base(motor):
    """T-LAB-03: Missing base panel = high priority suggestion."""
    enc = Encounter(
        id="3",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"
    assert result.action_checklist is not None
    assert len(result.action_checklist) > 0
    assert any("básico" in a.task.lower() for a in result.action_checklist)


def test_lab_suggest_diabetes_condition(motor):
    """T-LAB-04: Patient with diabetes = suggest HbA1c."""
    enc = Encounter(
        id="4",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=130),
        cardio_panel=CardioPanelSchema(),
        conditions=[Condition(code="E11.9", title="Type 2 Diabetes Mellitus")],
        medications=[],
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert any("HbA1c" in a.task for a in result.action_checklist)


def test_lab_suggest_hypertension_condition(motor):
    """T-LAB-05: Patient with hypertension = suggest lipid panel."""
    enc = Encounter(
        id="5",
        demographics=DemographicsSchema(age_years=60, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        conditions=[Condition(code="I10", title="Essential hypertension")],
        medications=[],
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert any("lipídico" in a.task.lower() for a in result.action_checklist)


def test_lab_suggest_metformin_monitoring(motor):
    """T-LAB-06: Patient on metformin = suggest renal function."""
    enc = Encounter(
        id="6",
        demographics=DemographicsSchema(age_years=50, gender="female"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110),
        cardio_panel=CardioPanelSchema(),
        conditions=[],
        medications=[MedicationStatement(code="A10BA02", name="Metformin 500mg")],
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert any("renal" in a.task.lower() for a in result.action_checklist)


def test_lab_suggest_age_based_screening(motor):
    """T-LAB-07: Age 45 = suggest lipid screening."""
    enc = Encounter(
        id="7",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert any("lipídico" in a.task.lower() for a in result.action_checklist)


def test_lab_suggest_multiple_gaps(motor):
    """T-LAB-08: Multiple gaps = multiple suggestions."""
    enc = Encounter(
        id="8",
        demographics=DemographicsSchema(age_years=45, gender="female"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.estado_ui == "PROBABLE_WARNING"
    assert len(result.action_checklist) >= 4


def test_lab_suggest_returns_metadata(motor):
    """T-LAB-09: Returns metadata with suggestions."""
    enc = Encounter(
        id="9",
        demographics=DemographicsSchema(age_years=50, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=90),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    assert result.metadata is not None
    assert "suggestions" in result.metadata
    assert result.metadata["age"] == 50


def test_lab_suggest_priority_order(motor):
    """T-LAB-10: High priority suggestions come first."""
    enc = Encounter(
        id="10",
        demographics=DemographicsSchema(age_years=35, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
        metadata={},
    )
    result = motor.compute(enc)
    high_priority = [a for a in result.action_checklist if a.priority == "high"]
    if high_priority:
        assert result.action_checklist[0].priority == "high"
