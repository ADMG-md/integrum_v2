import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.engines.domain import Encounter, Observation, Condition, MedicationStatement
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.eoss import EOSSStagingMotor
from src.engines.specialty_runner import specialty_runner
from src.services.report_service import report_service
import json

def verify_mission_6():
    print("🕵️ TESTING MISSION 6: THE CLINICAL DETECTIVE (SUGGESTIONS) 🕵️")
    print("-" * 50)

    # 1. Complex Patient setup
    encounter = Encounter(
        id="m6-detetive-test",
        conditions=[Condition(code="I10", title="HTA")], # Hypertensive
        observations=[
            Observation(code="2339-0", value=115.0, category="Clinical"), # Glucose
            Observation(code="2571-8", value=220.0, category="Clinical"), # Triglycerides
            Observation(code="LIFESTYLE-SLEEP-HRS", value=5.5, category="Lifestyle"), # Sleep debt
            Observation(code="1762-0", value=45.0, category="Clinical"), # High Aldo (1762-0)
            Observation(code="2889-4", value=1.0, category="Clinical"), # Low Renin (2889-4)
            Observation(code="11579-0", value=5.1, category="Clinical"), # Subclinical Hypothyroid (TSH > 4.5)
        ],
        medications=[
            MedicationStatement(code="RX-202", name="Prednisone") 
        ]
    )

    # 2. Run engines
    results = {
        "AcostaPhenotypeMotor": AcostaPhenotypeMotor().compute(encounter),
        "EOSSStagingMotor": EOSSStagingMotor().compute(encounter)
    }
    results.update(specialty_runner.run_all(encounter))

    # 3. Generate Report (which triggers SuggestionService)
    report = report_service.generate_report(results, encounter)

    print(f"\nReport ID: {report.report_id}")
    print("\n--- CLINICAL SUGGESTIONS ---")
    for sug in report.suggestions:
        print(f"[{sug.priority}] {sug.category}: {sug.title}")
        print(f"  > {sug.description}")

    # 4. Assertions
    titles = [s.title for s in report.suggestions]
    assert "Confirmación de Aldosteronismo Primario" in titles, "Should detect ARR risk"
    assert "Seguimiento de Perfil Tiroideo" in titles, "Should detect Subclinical Hypothyroidism"
    assert "Intervención en Higiene de Sueño" in titles, "Should detect Sleep/Metabolic link"
    assert "Revisión de Medicación Obesogénica" in titles, "Should detect Prednisone issue"

    print("\n✅ MISSION 6 VERIFIED: The Detective successfully connected the dots and prescribed actions.")

if __name__ == "__main__":
    verify_mission_6()
