import sys
import os
import unittest

# Ensure src is in the path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.append(backend_root)

from src.engines.domain import Encounter, Observation
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema, CardioPanelSchema
from src.engines.specialty_runner import SpecialtyRunner

class TestScrappyResilienceV2(unittest.TestCase):
    """
    Validation of 'Paciente Scrappy' behavior (Mission 12 Hardening).
    Verifies that:
    1. Risk Engines (CVD) block properly when labs are missing (Honest Gating).
    2. Behavioral Engines (Acosta) remain informative with psychometrics only.
    """

    def setUp(self):
        self.runner = SpecialtyRunner()

    def test_scrappy_patient_flow(self):
        # 1. Setup 'Scrappy Patient' (BMI + Psychometrics only, No Labs)
        observations = [
            # Biometrics
            Observation(code="29463-7", value=95.0, unit="kg"), # Weight
            Observation(code="8302-2", value=170.0, unit="cm"), # Height
            # Psychometrics (Mental Health Hub)
            Observation(code="GAD-7", value=12, category="Psychometry"),      # Moderate Anxiety
            Observation(code="AIS-001", value=8, category="Psychometry"),     # Sleep Deprivation (Athens)
            Observation(code="TFEQ-EMOTIONAL", value=3.5, category="Psychometry") # High Emotional Eating
        ]
        
        metadata = {"sex": "F", "patient_age": 45}
        
        demographics = DemographicsSchema(age_years=45.0, gender="female")
        metabolic = MetabolicPanelSchema() # ZERO LABS
        cardio = CardioPanelSchema() # ZERO LABS
        
        encounter = Encounter(
            id="test-scrappy-001",
            demographics=demographics,
            metabolic_panel=metabolic,
            cardio_panel=cardio,
            observations=observations,
            conditions=[], # No dx
            metadata=metadata
        )

        # 2. Run All Motors
        results = self.runner.run_all(encounter)

        # 3. Assertions: CVD (Risk) SHOULD BE LOCKED
        cvd_result = results.get("CVDHazardMotor")
        self.assertIsNotNone(cvd_result, "CVD Motor should have run")
        self.assertEqual(cvd_result.estado_ui, "INDETERMINATE_LOCKED", 
                         "CVD Motor must return INDETERMINATE_LOCKED with missing labs (Honest Gating)")

        # 4. Assertions: Acosta (Behavioral) SHOULD BE ACTIVE
        acosta_result = results.get("AcostaPhenotypeMotor")
        self.assertIsNotNone(acosta_result, "Acosta Motor should have run")
        self.assertEqual(acosta_result.estado_ui, "CONFIRMED_ACTIVE", 
                         f"Acosta should be ACTIVE with psychometrics. Got: {acosta_result.estado_ui}")
        self.assertIn("Hambre Emocional", acosta_result.calculated_value)
        self.assertIn("Privación de Sueño", acosta_result.calculated_value)
        self.assertGreater(acosta_result.confidence, 0.65, 
                           "Confidence should be elevated based on multi-marker psychometrics")

        # 5. Assertions: Connectivity / Resilience
        # SpecialtyRunner must not crash and include all motors in report
        self.assertIn("ObesityMasterMotor", results, "Aggregator motor should be present")

        print("✅ Scrappy Resilience Verified successfully in V2 Engine.")

if __name__ == "__main__":
    unittest.main()
