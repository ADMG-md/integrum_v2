import pytest
from src.engines.specialty.pediatric_nutrition import PediatricNutritionMotor
from src.engines.domain import Encounter, Condition
from src.schemas.encounter import (
    DemographicsSchema,
    MetabolicPanelSchema,
)


@pytest.fixture
def motor():
    return PediatricNutritionMotor()


def _make_encounter(id="ped-test", age=10, gender="male", conditions=None):
    """Helper: creates a valid Encounter for Pediatric Nutrition testing."""
    return Encounter(
        id=id,
        demographics=DemographicsSchema(age_years=age, gender=gender),
        metabolic_panel=MetabolicPanelSchema(),
        conditions=conditions or [],
        observations=[],
        metadata={},
    )


def test_ped_nutrition_validate_pediatric_age(motor):
    """T-PED-01: Valid pediatric age 2-18 passes validation."""
    enc = _make_encounter(id="1", age=10)
    valid, msg = motor.validate(enc)
    assert valid is True


def test_ped_nutrition_validate_adult_age_fails(motor):
    """T-PED-02: Adult age 18+ fails validation."""
    enc = _make_encounter(id="2", age=25)
    valid, msg = motor.validate(enc)
    assert valid is False
    assert "18" in msg


def test_ped_nutrition_validate_infant_fails(motor):
    """T-PED-03: Infant age <2 fails validation."""
    enc = _make_encounter(id="3", age=1)
    valid, msg = motor.validate(enc)
    assert valid is False
    assert "2" in msg


def test_ped_nutrition_obesity_condition(motor):
    """T-PED-OB-01: Obesity condition = obesity category."""
    enc = _make_encounter(
        id="ob1",
        age=12,
        conditions=[Condition(code="E66.9", title="Obesity")],
    )
    result = motor.compute(enc)
    assert result.metadata["patient_category"] == "obesity"
    assert result.estado_ui == "PROBABLE_RECOMMENDATION"


def test_ped_nutrition_obesity_recommendations(motor):
    """T-PED-OB-02: Obesity = multimodal intervention."""
    enc = _make_encounter(
        id="ob2",
        age=10,
        conditions=[Condition(code="E66.0", title="Obesity")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    assert any("multimodal" in t.lower() for t in tasks)
    assert any("60 min" in t for t in tasks)
    assert any("familia" in t.lower() for t in tasks)


def test_ped_nutrition_tea_category(motor):
    """T-PED-TEA-01: TEA diagnosis = tea category."""
    enc = _make_encounter(
        id="tea1",
        age=8,
        conditions=[Condition(code="F84.0", title="Autistic disorder")],
    )
    result = motor.compute(enc)
    assert result.metadata["patient_category"] == "tea"


def test_ped_nutrition_tea_deficiency_evaluation(motor):
    """T-PED-TEA-02: TEA = evaluate deficiencies."""
    enc = _make_encounter(
        id="tea2",
        age=6,
        conditions=[Condition(code="F84.5", title="Asperger syndrome")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    assert any("deficiencias" in t.lower() for t in tasks)


def test_ped_nutrition_tea_diet_warning(motor):
    """T-PED-TEA-03: TEA = warn about restrictive diets."""
    enc = _make_encounter(
        id="tea3",
        age=10,
        conditions=[Condition(code="F84.9", title="ASD")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    assert any("evitar" in t.lower() and "restric" in t.lower() for t in tasks)


def test_ped_nutrition_tdah_category(motor):
    """T-PED-TDAH-01: TDAH = tdah category."""
    enc = _make_encounter(
        id="adhd1",
        age=9,
        conditions=[Condition(code="F90.0", title="ADHD")],
    )
    result = motor.compute(enc)
    assert result.metadata["patient_category"] == "tdah"


def test_ped_nutrition_tdah_micronutrients(motor):
    """T-PED-TDAH-02: TDAH = suggest micronutrients."""
    enc = _make_encounter(
        id="adhd2",
        age=7,
        conditions=[Condition(code="F90.9", title="ADHD")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    # Micronutrients could be mentioned in evaluation or supplements
    assert any(
        "hierro" in t.lower() or "zinc" in t.lower() or "nutrient" in t.lower()
        for t in tasks
    )


def test_ped_nutrition_tdah_regular_meals(motor):
    """T-PED-TDAH-03: TDAH = regular meals pattern."""
    enc = _make_encounter(
        id="adhd3",
        age=11,
        conditions=[Condition(code="F90.1", title="Hyperactive ADHD")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    assert any("horarios" in t.lower() and "comidas" in t.lower() for t in tasks)


def test_ped_nutrition_typical_category(motor):
    """T-PED-TYP-01: No conditions = typical category."""
    enc = _make_encounter(id="typ1", age=15)
    result = motor.compute(enc)
    assert result.metadata["patient_category"] == "typical"
    assert result.estado_ui == "NORMAL"


def test_ped_nutrition_referral_pediatric_nutrition(motor):
    """T-PED-REF-01: Non-typical = refer to pediatric nutrition."""
    enc = _make_encounter(
        id="ref1",
        age=8,
        conditions=[Condition(code="E66.9", title="Obesity")],
    )
    result = motor.compute(enc)
    tasks = [a.task for a in result.action_checklist]
    assert any("nutrición pediátrica" in t.lower() for t in tasks)


def test_ped_nutrition_age_groups(motor):
    """T-PED-AGE-01: Different ages = correct age groups."""
    test_cases = [
        (2, "child"),  # age 2-9 = child
        (5, "child"),
        (9, "child"),
        (10, "adolescent"),  # age 10-17 = adolescent
        (14, "adolescent"),
    ]
    for age, expected_group in test_cases:
        enc = _make_encounter(id=f"age_{age}", age=age)
        result = motor.compute(enc)
        assert result.metadata["age_group"] == expected_group, (
            f"age {age} should be {expected_group}, got {result.metadata['age_group']}"
        )


def test_ped_nutrition_metadata_complete(motor):
    """T-PED-META-01: Returns complete metadata."""
    enc = _make_encounter(
        id="meta1",
        age=12,
        conditions=[Condition(code="F90.0", title="ADHD")],
    )
    result = motor.compute(enc)
    assert result.metadata is not None
    assert "patient_category" in result.metadata
    assert "age_group" in result.metadata
    assert "has_adhd" in result.metadata
    assert "recommendations_count" in result.metadata
    assert "supplements" in result.metadata


def test_ped_nutrition_supplements_list(motor):
    """T-PED-SUP-01: TEA = vitamin D supplement."""
    enc = _make_encounter(
        id="sup1",
        age=10,
        conditions=[Condition(code="F84.0", title="Autism")],
    )
    result = motor.compute(enc)
    supplements = result.metadata.get("supplements", [])
    assert any("Vitamina D" in s.get("name", "") for s in supplements)


def test_ped_nutrition_monitoring_frequency(motor):
    """T-PED-MON-01: TEA = monthly monitoring."""
    enc = _make_encounter(
        id="mon1",
        age=7,
        conditions=[Condition(code="F84.5", title="Asperger")],
    )
    result = motor.compute(enc)
    assert result.metadata["monitoring_frequency"] == "mensual"


def test_ped_nutrition_tdah_labs(motor):
    """T-PED-TDAH-LAB-01: TDAH = suggest lab checks."""
    enc = _make_encounter(
        id="lab1",
        age=8,
        conditions=[Condition(code="F90.0", title="ADHD")],
    )
    result = motor.compute(enc)
    next_labs = result.metadata.get("next_lab_check", [])
    assert "Ferritina" in next_labs
    assert any("Zinc" in lab for lab in next_labs)


def test_ped_nutrition_confidence_typical_vs_tdah(motor):
    """T-PED-CONF-01: Typical has higher confidence than TDAH."""
    typical_enc = _make_encounter(id="c1", age=15)
    typical_result = motor.compute(typical_enc)

    tdah_enc = _make_encounter(
        id="c2",
        age=9,
        conditions=[Condition(code="F90.0", title="ADHD")],
    )
    tdah_result = motor.compute(tdah_enc)
    assert typical_result.confidence > tdah_result.confidence
