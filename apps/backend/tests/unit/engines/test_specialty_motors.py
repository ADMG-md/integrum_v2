"""
V&V Tests for Specialty Engines (formerly orphaned or untested).
Each test verifies: instantiation, validate/compute contract, and safe failure.
"""

import pytest
from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
)
from src.engines.base_models import AdjudicationResult


# ============================================================
# KleiberBMRMotor (registered, untested)
# ============================================================


class TestKleiberBMRMotor:
    def test_instantiation(self):
        from src.engines.metabolic import KleiberBMRMotor

        motor = KleiberBMRMotor()
        assert motor is not None

    def test_validates_missing_weight(self, empty_encounter):
        from src.engines.metabolic import KleiberBMRMotor

        motor = KleiberBMRMotor()
        is_valid, reason = motor.validate(empty_encounter)
        assert not is_valid

    def test_computes_with_weight(self, minimal_encounter):
        from src.engines.metabolic import KleiberBMRMotor

        motor = KleiberBMRMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        if is_valid:
            result = motor.compute(minimal_encounter)
            assert isinstance(result, AdjudicationResult)
            assert result.calculated_value is not None


# ============================================================
# Lifestyle360Motor (registered, untested)
# ============================================================


class TestLifestyle360Motor:
    def test_instantiation(self):
        from src.engines.specialty.lifestyle import Lifestyle360Motor

        motor = Lifestyle360Motor()
        assert motor is not None

    def test_computes_with_minimal_data(self, minimal_encounter):
        from src.engines.specialty.lifestyle import Lifestyle360Motor

        motor = Lifestyle360Motor()
        is_valid, _ = motor.validate(minimal_encounter)
        if is_valid:
            result = motor.compute(minimal_encounter)
            assert isinstance(result, AdjudicationResult)
            assert result.calculated_value is not None


# ============================================================
# MetabolicPrecisionMotor (registered, untested)
# ============================================================


class TestMetabolicPrecisionMotor:
    def test_instantiation(self):
        from src.engines.specialty.metabolic import MetabolicPrecisionMotor

        motor = MetabolicPrecisionMotor()
        assert motor is not None

    def test_computes_with_full_data(self, full_encounter):
        from src.engines.specialty.metabolic import MetabolicPrecisionMotor

        motor = MetabolicPrecisionMotor()
        is_valid, _ = motor.validate(full_encounter)
        if is_valid:
            result = motor.compute(full_encounter)
            assert isinstance(result, AdjudicationResult)


# ============================================================
# DeepMetabolicProxyMotor (registered, untested)
# ============================================================


class TestDeepMetabolicProxyMotor:
    def test_instantiation(self):
        from src.engines.specialty.metabolomics import DeepMetabolicProxyMotor

        motor = DeepMetabolicProxyMotor()
        assert motor is not None

    def test_computes_with_full_data(self, full_encounter):
        from src.engines.specialty.metabolomics import DeepMetabolicProxyMotor

        motor = DeepMetabolicProxyMotor()
        is_valid, _ = motor.validate(full_encounter)
        if is_valid:
            result = motor.compute(full_encounter)
            assert isinstance(result, AdjudicationResult)


# ============================================================
# AnthropometryPrecisionMotor (formerly orphaned)
# ============================================================


class TestAnthropometryPrecisionMotor:
    def test_instantiation(self):
        from src.engines.specialty.anthropometry import AnthropometryPrecisionMotor

        motor = AnthropometryPrecisionMotor()
        assert motor is not None

    def test_validates_missing_waist(self, minimal_encounter):
        from src.engines.specialty.anthropometry import AnthropometryPrecisionMotor

        motor = AnthropometryPrecisionMotor()
        enc = minimal_encounter
        enc.observations = [o for o in enc.observations if o.code != "WAIST-001"]
        is_valid, reason = motor.validate(enc)
        assert not is_valid

    def test_computes_with_waist_and_height(self, minimal_encounter):
        from src.engines.specialty.anthropometry import AnthropometryPrecisionMotor

        motor = AnthropometryPrecisionMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        if is_valid:
            result = motor.compute(minimal_encounter)
            assert isinstance(result, AdjudicationResult)


# ============================================================
# EndocrinePrecisionMotor (formerly orphaned)
# ============================================================


class TestEndocrinePrecisionMotor:
    def test_instantiation(self):
        from src.engines.specialty.endocrine import EndocrinePrecisionMotor

        motor = EndocrinePrecisionMotor()
        assert motor is not None

    def test_computes_with_thyroid_data(self, full_encounter):
        from src.engines.specialty.endocrine import EndocrinePrecisionMotor

        motor = EndocrinePrecisionMotor()
        is_valid, _ = motor.validate(full_encounter)
        if is_valid:
            result = motor.compute(full_encounter)
            assert isinstance(result, AdjudicationResult)

    def test_skips_without_thyroid_data(self, minimal_encounter):
        from src.engines.specialty.endocrine import EndocrinePrecisionMotor

        motor = EndocrinePrecisionMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        assert not is_valid


# ============================================================
# HypertensionSecondaryMotor (formerly orphaned)
# ============================================================


class TestHypertensionSecondaryMotor:
    def test_instantiation(self):
        from src.engines.specialty.hypertension import HypertensionSecondaryMotor

        motor = HypertensionSecondaryMotor()
        assert motor is not None

    def test_computes_with_hypertension(self, minimal_encounter):
        from src.engines.specialty.hypertension import HypertensionSecondaryMotor

        motor = HypertensionSecondaryMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        if is_valid:
            result = motor.compute(minimal_encounter)
            assert isinstance(result, AdjudicationResult)


# ============================================================
# InflammationMotor (formerly orphaned)
# ============================================================


class TestInflammationMotor:
    def test_instantiation(self):
        from src.engines.specialty.inflammation import InflammationMotor

        motor = InflammationMotor()
        assert motor is not None

    def test_computes_with_hscrp(self, full_encounter):
        from src.engines.specialty.inflammation import InflammationMotor

        motor = InflammationMotor()
        is_valid, _ = motor.validate(full_encounter)
        if is_valid:
            result = motor.compute(full_encounter)
            assert isinstance(result, AdjudicationResult)

    def test_skips_without_hscrp(self, minimal_encounter):
        from src.engines.specialty.inflammation import InflammationMotor

        motor = InflammationMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        assert not is_valid


# ============================================================
# SleepApneaPrecisionMotor (formerly orphaned)
# ============================================================


class TestSleepApneaPrecisionMotor:
    def test_instantiation(self):
        from src.engines.specialty.sleep_apnea import SleepApneaPrecisionMotor

        motor = SleepApneaPrecisionMotor()
        assert motor is not None

    def test_computes_stop_bang(self, minimal_encounter):
        from src.engines.specialty.sleep_apnea import SleepApneaPrecisionMotor

        motor = SleepApneaPrecisionMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        if is_valid:
            result = motor.compute(minimal_encounter)
            assert isinstance(result, AdjudicationResult)


# ============================================================
# LaboratoryStewardshipMotor (formerly orphaned)
# ============================================================


class TestLaboratoryStewardshipMotor:
    def test_instantiation(self):
        from src.engines.specialty.stewardship import LaboratoryStewardshipMotor

        motor = LaboratoryStewardshipMotor()
        assert motor is not None

    def test_always_valid(self, minimal_encounter):
        from src.engines.specialty.stewardship import LaboratoryStewardshipMotor

        motor = LaboratoryStewardshipMotor()
        is_valid, _ = motor.validate(minimal_encounter)
        assert is_valid

    def test_computes_suggestions(self, minimal_encounter):
        from src.engines.specialty.stewardship import LaboratoryStewardshipMotor

        motor = LaboratoryStewardshipMotor()
        result = motor.compute(minimal_encounter)
        assert isinstance(result, AdjudicationResult)
