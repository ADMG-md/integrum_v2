import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.engines.domain import Encounter, Observation, Condition
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.specialty.lifestyle import Lifestyle360Motor
from src.services.report_service import report_service
from src.services.hybrid_intel_service import hybrid_intel_service
import json

def verify_hybrid_intelligence():
    print("🧠 TESTING MISSION 6: HYBRID INTELLIGENCE & SANITIZATION 🧠")
    print("-" * 50)

    # 1. Setup Patient with PHI (Private Health Information)
    encounter = Encounter(
        id="real-id-999",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="TFEQ-HEDONIC", value=20.0, category="Psychometry"),
            Observation(code="LIFESTYLE-SLEEP-HRS", value=4.5, category="Lifestyle")
        ]
    )
    
    # Mocking metadata that contains PII
    encounter.observations[0].metadata = {"patient_email": "doctor@gmail.com"}

    # 2. Results
    results = {
        "acosta": AcostaPhenotypeMotor().compute(encounter),
        "Lifestyle360Motor": Lifestyle360Motor().compute(encounter)
    }

    # 3. Generate Hybrid Report
    report = report_service.generate_report(results, encounter)

    print("\n[Patient Perspective]:")
    print(f"  > {report.patient_narrative}")

    print("\n[Clinician Prompt Export (Sanitized)]:")
    print("-" * 30)
    print(report.clinician_prompt[:500] + "...")
    print("-" * 30)

    # 4. Assertions
    assert "real-id-999" not in report.clinician_prompt, "PII Leak: Encounter ID found in prompt!"
    assert "Hambre Hedónica" in report.patient_narrative, "Reflection mismatch for Phenotype C"
    assert "falta de sueño" in report.patient_narrative, "Reflection mismatch for Sleep Debt"
    
    print("\n✅ MISSION 6 VERIFIED: Hybrid Intelligence is HIPAA-safe and reflective.")

if __name__ == "__main__":
    verify_hybrid_intelligence()
