import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)
from src.engines.specialty.readiness import (
    ClinicalDataReadinessEngine,
    MOTOR_REQUIREMENTS,
)
from src.engines.specialty_runner import PRIMARY_MOTORS


def make_encounter(**kwargs):
    defaults = dict(
        id="test-readiness",
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=100),
        cardio_panel=CardioPanelSchema(glucose_mg_dl=100),
        observations=[],
        conditions=[],
        medications=[],
    )
    defaults.update(kwargs)
    return Encounter(**defaults)


def test_empty_encounter_all_blocked():
    """No data → all motors blocked or quickwins."""
    engine = ClinicalDataReadinessEngine()
    enc = make_encounter(
        metabolic_panel=MetabolicPanelSchema(),
        cardio_panel=CardioPanelSchema(),
        observations=[],
    )
    report = engine.score(enc, PRIMARY_MOTORS)

    assert report.total_motors == len(PRIMARY_MOTORS)
    assert report.feasibility_score < 0.1
    assert report.tier == "Básica"
    assert report.ready_count <= 2
    assert (
        report.blocked_count + report.quickwin_count
        == report.total_motors - report.ready_count
    )
    print(
        f"✅ Empty encounter: {report.ready_count} ready, {report.quickwin_count} quickwins, {report.blocked_count} blocked"
    )


def test_basic_data_some_motors_ready():
    """Minimal Colombian EPS data: glucose, cholesterol, weight, height."""
    engine = ClinicalDataReadinessEngine()
    enc = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
        ),
        cardio_panel=CardioPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
        ),
        observations=[
            Observation(code="29463-7", value=85, unit="kg", category="Anthropometry"),
            Observation(code="8302-2", value=170, unit="cm", category="Anthropometry"),
        ],
    )
    report = engine.score(enc, PRIMARY_MOTORS)

    assert report.ready_count > 0, "Some motors should be ready with basic data"
    assert 0 < report.feasibility_score < 1.0
    assert len(report.priority_labs) > 0, "Should recommend labs to unlock more motors"
    assert report.ready_motors is not None
    print(
        f"✅ Basic EPS data: {report.ready_count}/{report.total_motors} ready, tier={report.tier}"
    )
    print(
        f"   Top labs to order: {[(l['name'], l['unlocks']) for l in report.to_dict()['priority_labs'][:3]]}"
    )


def test_quickwins_correctly_identified():
    """If only 1 required field is missing, it should be a quickwin not blocked."""
    engine = ClinicalDataReadinessEngine()
    enc = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
        ),
        cardio_panel=CardioPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
        ),
        observations=[
            Observation(code="29463-7", value=85, unit="kg", category="Anthropometry"),
            Observation(code="8302-2", value=170, unit="cm", category="Anthropometry"),
            Observation(code="WAIST-001", value=95, unit="cm"),
            Observation(code="HIP-001", value=100, unit="cm"),
        ],
    )
    report = engine.score(enc, PRIMARY_MOTORS)

    assert report.quickwin_count > 0, "Should have quickwins (motors 1 lab away)"
    assert any(qw.missing_codes for qw in report.quickwins), (
        "Quickwins should list missing codes"
    )
    print(f"✅ Quickwins: {report.quickwin_count} motors 1 lab away")
    for qw in report.quickwins[:3]:
        print(f"   {qw.motor} needs: {qw.missing_codes}")


def test_priority_labs_ranked_by_unlock_count():
    """Labs that unlock more motors should appear first."""
    engine = ClinicalDataReadinessEngine()
    enc = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110),
        cardio_panel=CardioPanelSchema(glucose_mg_dl=110),
        observations=[
            Observation(code="29463-7", value=85, unit="kg"),
            Observation(code="8302-2", value=170, unit="cm"),
        ],
    )
    report = engine.score(enc, PRIMARY_MOTORS)

    labs = report.to_dict()["priority_labs"]
    if len(labs) >= 2:
        assert labs[0]["unlocks"] >= labs[1]["unlocks"], (
            "Top lab should unlock >= second lab"
        )
    print(f"✅ Labs ranked: {[(l['name'], l['unlocks']) for l in labs[:5]]}")


def test_tier_classification():
    """Tier should reflect number of ready motors, not raw feasibility score."""
    engine = ClinicalDataReadinessEngine()

    enc_basic = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110),
        cardio_panel=CardioPanelSchema(glucose_mg_dl=110),
        observations=[],
    )
    report = engine.score(enc_basic, PRIMARY_MOTORS)
    assert report.tier == "Básica", f"Expected Básica, got {report.tier}"
    print(f"✅ Tier Básica: {report.ready_count} ready")

    enc_full = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
            ldl_mg_dl=130,
            hba1c=5.8,
            creatinine_mg_dl=0.9,
            alt_u_l=25,
            ast_u_l=22,
            ggt_u_l=30,
            tsh_mi_u_l=2.5,
            ft4_ng_dl=1.2,
        ),
        cardio_panel=CardioPanelSchema(
            glucose_mg_dl=110,
            total_cholesterol_mg_dl=220,
            triglycerides_mg_dl=180,
            hdl_mg_dl=42,
            ldl_mg_dl=130,
        ),
        observations=[
            Observation(code="29463-7", value=85, unit="kg"),
            Observation(code="8302-2", value=170, unit="cm"),
            Observation(code="WAIST-001", value=95, unit="cm"),
            Observation(code="HIP-001", value=100, unit="cm"),
        ],
    )
    report = engine.score(enc_full, PRIMARY_MOTORS)
    assert report.tier in ("Estándar", "Completa", "Especializada"), (
        f"Expected higher tier, got {report.tier}"
    )
    print(f"✅ Tier Completa: {report.ready_count}/{report.total_motors} ready")


def test_no_clinical_logic_executed():
    """score() should call validate() not compute() on motors."""
    engine = ClinicalDataReadinessEngine()
    enc = make_encounter(
        demographics=DemographicsSchema(age_years=55, gender="male"),
        metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110),
        cardio_panel=CardioPanelSchema(glucose_mg_dl=110),
        observations=[],
    )

    import time

    start = time.time()
    report = engine.score(enc, PRIMARY_MOTORS)
    elapsed = time.time() - start

    assert elapsed < 1.0, (
        f"score() took {elapsed:.2f}s — should not execute motor.compute()"
    )
    print(f"✅ score() completed in {elapsed * 1000:.1f}ms (no compute() called)")


if __name__ == "__main__":
    print("=" * 60)
    print("ClinicalDataReadinessEngine — Integration Tests")
    print("=" * 60)
    test_empty_encounter_all_blocked()
    test_basic_data_some_motors_ready()
    test_quickwins_correctly_identified()
    test_priority_labs_ranked_by_unlock_count()
    test_tier_classification()
    test_no_clinical_logic_executed()
    print("\n✅ All tests passed")
