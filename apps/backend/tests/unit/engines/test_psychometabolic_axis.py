"""
Unit Tests — PsychometabolicAxisMotor (Sprint 11: Gut-Brain Axis)

Tests cover:
  1. Validation gate (requires PHQ-9 or GAD-7)
  2. Inflammatory Depression phenotype (PHQ-9 ≥ 10 + hs-CRP > 3)
  3. Hedonic Deficit phenotype (TFEQ-Emotional + PHQ-9 ≥ 10)
  4. Suicidal ideation safety gate (PHQ-9 Item 9)
  5. Anxiety-Driven Hyperphagia (GAD-7 ≥ 10 + TFEQ-Uncontrolled)
  6. Serotonin precursor deficit (low ferritin + low vitamin D)
  7. Iatrogenic weight gain detection
  8. Restraint-binge paradox
"""

import pytest
from src.engines.specialty.psychometabolic_axis import PsychometabolicAxisMotor
from src.engines.domain import (
    Encounter, Observation, DemographicsSchema,
    MetabolicPanelSchema, Condition, MedicationStatement,
)
from src.schemas.encounter import CardioPanelSchema
from src.domain.models import ClinicalHistory


def _base_encounter(**overrides):
    """Builds a minimal encounter with psychometric observations."""
    obs = overrides.pop("observations", [])
    meds = overrides.pop("medications", [])
    demographics = overrides.pop("demographics", DemographicsSchema(
        age_years=45, gender="female", weight_kg=95, height_cm=160,
    ))
    history = overrides.pop("history", ClinicalHistory(
        onset_trigger="unknown", pregnancy_status="not_applicable",
    ))
    metabolic_panel = overrides.pop("metabolic_panel", MetabolicPanelSchema(
        glucose_mg_dl=90,
    ))
    cardio_panel = overrides.pop("cardio_panel", CardioPanelSchema(
        total_cholesterol_mg_dl=200,
    ))
    return Encounter(
        id="PSY-TEST",
        demographics=demographics,
        metabolic_panel=metabolic_panel,
        cardio_panel=cardio_panel,
        observations=obs,
        medications=meds,
        history=history,
        **overrides,
    )


motor = PsychometabolicAxisMotor()


class TestValidation:
    """Motor requires at least PHQ-9 or GAD-7."""

    def test_rejects_without_psychometrics(self):
        enc = _base_encounter(observations=[])
        valid, reason = motor.validate(enc)
        assert valid is False
        assert "PHQ-9" in reason

    def test_accepts_phq9_only(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=10),
        ])
        valid, _ = motor.validate(enc)
        assert valid is True

    def test_accepts_gad7_only(self):
        enc = _base_encounter(observations=[
            Observation(code="GAD-7", value=8),
        ])
        valid, _ = motor.validate(enc)
        assert valid is True


class TestInflammatoryDepression:
    """PHQ-9 ≥ 10 + hs-CRP > 3 → Inflammatory Depression phenotype."""

    def test_inflammatory_depression_detected(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="30522-7", value=8.5, unit="mg/L"),
        ])
        result = motor.compute(enc)
        assert "Depresión Inflamatoria" in result.calculated_value
        assert any("ISRS probablemente subóptimos" in a.task for a in result.action_checklist)

    def test_no_inflammatory_depression_with_low_crp(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="30522-7", value=1.5, unit="mg/L"),
        ])
        result = motor.compute(enc)
        assert "Depresión Inflamatoria" not in result.calculated_value

    def test_no_inflammatory_depression_with_low_phq9(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=5),
            Observation(code="30522-7", value=8.5, unit="mg/L"),
        ])
        result = motor.compute(enc)
        assert "Depresión Inflamatoria" not in result.calculated_value


class TestSuicidalIdeation:
    """PHQ-9 Item 9 ≥ 2 → Critical safety flag + bupropion contraindication."""

    def test_item9_critical_blocks_bupropion(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=18),
            Observation(code="PHQ9-I9-001", value=2),
        ])
        result = motor.compute(enc)
        assert result.estado_ui == "PROBABLE_WARNING"
        assert any(
            o.gap_type == "CONTRAINDICATED" and "Bupropión" in o.drug_class
            for o in result.critical_omissions
        )
        assert any("DERIVACIÓN PSIQUIÁTRICA URGENTE" in a.task for a in result.action_checklist)

    def test_item9_passive_flags_evaluation(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=12),
            Observation(code="PHQ9-I9-001", value=1),
        ])
        result = motor.compute(enc)
        assert any("Evaluación psiquiátrica" in a.task for a in result.action_checklist)

    def test_item9_zero_no_flag(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=12),
            Observation(code="PHQ9-I9-001", value=0),
        ])
        result = motor.compute(enc)
        assert not any("URGENTE" in a.task for a in result.action_checklist)


class TestHedonicDeficit:
    """TFEQ-Emotional ≥ 2.5 + PHQ-9 ≥ 10 → Naltrexone/Bupropion candidate."""

    def test_hedonic_deficit_recommends_contrave(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="PHQ9-I9-001", value=0),
            Observation(code="TFEQ-EMOTIONAL", value=3.2),
        ])
        result = motor.compute(enc)
        assert "Déficit Hedónico" in result.calculated_value
        assert any("Naltrexona/Bupropión" in a.task for a in result.action_checklist)

    def test_hedonic_deficit_blocked_by_suicidal_ideation(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="PHQ9-I9-001", value=2),
            Observation(code="TFEQ-EMOTIONAL", value=3.2),
        ])
        result = motor.compute(enc)
        assert any("CONTRAINDICADO" in a.task for a in result.action_checklist)

    def test_emotional_eating_without_depression_recommends_tcc(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=5),
            Observation(code="TFEQ-EMOTIONAL", value=3.5),
        ])
        result = motor.compute(enc)
        assert "Comida Emocional sin Depresión Clínica" in result.calculated_value
        assert any("TCC" in a.task or "Mindful" in a.task for a in result.action_checklist)


class TestAnxietyHyperphagia:
    """GAD-7 ≥ 10 + TFEQ-Uncontrolled ≥ 2.5 → Anxiety-driven hyperphagia."""

    def test_anxiety_hyperphagia_detected(self):
        enc = _base_encounter(observations=[
            Observation(code="GAD-7", value=14),
            Observation(code="TFEQ-UNCONTROLLED", value=3.0),
        ])
        result = motor.compute(enc)
        assert "Hiperfagia Ansiogénica" in result.calculated_value
        assert any("ansiedad antes" in a.task.lower() for a in result.action_checklist)


class TestSerotoninPrecursors:
    """Low ferritin + low vitamin D + depression → correct cofactors first."""

    def test_serotonin_precursor_deficit(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=12),
            Observation(code="FERRITIN-001", value=15, unit="ng/mL"),
            Observation(code="VITD-001", value=12, unit="ng/mL"),
        ])
        result = motor.compute(enc)
        assert "Déficit de Precursores Serotoninérgicos" in result.calculated_value
        assert any("cofactores" in a.task.lower() for a in result.action_checklist)


class TestIatrogenicWeightGain:
    """Detect weight-gaining psychotropics."""

    def test_detects_paroxetine(self):
        enc = _base_encounter(
            observations=[Observation(code="PHQ9-SCORE", value=8)],
            medications=[
                MedicationStatement(code="PAROXETINE", name="Paroxetina 20mg", is_active=True),
            ],
        )
        result = motor.compute(enc)
        assert "Ganancia Iatrogénica" in result.calculated_value
        assert any("Paroxetina" in a.task for a in result.action_checklist)

    def test_ignores_inactive_medications(self):
        enc = _base_encounter(
            observations=[Observation(code="PHQ9-SCORE", value=8)],
            medications=[
                MedicationStatement(code="PAROXETINE", name="Paroxetina 20mg", is_active=False),
            ],
        )
        result = motor.compute(enc)
        assert "Ganancia Iatrogénica" not in result.calculated_value


class TestRestraintParadox:
    """TFEQ-Cognitive ≥ 3.0 + PHQ-9 ≥ 10 → Binge risk."""

    def test_restraint_binge_cycle_detected(self):
        enc = _base_encounter(observations=[
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="TFEQ-COGNITIVE", value=3.5),
        ])
        result = motor.compute(enc)
        assert "Paradoja de Restricción Cognitiva" in result.calculated_value
        assert any("Restricción-Atracón" in a.task for a in result.action_checklist)


class TestDeterminism:
    """Same input → same output (IEC 62304 compliance)."""

    def test_deterministic_output(self):
        obs = [
            Observation(code="PHQ9-SCORE", value=14),
            Observation(code="PHQ9-I9-001", value=0),
            Observation(code="GAD-7", value=12),
            Observation(code="TFEQ-EMOTIONAL", value=3.2),
            Observation(code="30522-7", value=5.0, unit="mg/L"),
        ]
        enc = _base_encounter(observations=obs)
        r1 = motor.compute(enc)
        r2 = motor.compute(enc)
        assert r1.calculated_value == r2.calculated_value
        assert r1.confidence == r2.confidence
        assert len(r1.evidence) == len(r2.evidence)
        assert len(r1.action_checklist) == len(r2.action_checklist)
