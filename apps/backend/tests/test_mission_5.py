import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.engines.domain import Encounter, Observation, Condition, MedicationStatement
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.eoss import EOSSStagingMotor
from src.engines.specialty_runner import create_runner
from src.services.report_service import report_service
import json

def verify_mission_5():
    print("Testing Misión 5: Report Generation and Narrative Aggregation...")
    
    # 1. Create a 360-degree patient
    encounter = Encounter(
        id="m5-report-test",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="2339-0", value=115, category="Clinical"), # Glucose
            Observation(code="2571-8", value=210, category="Clinical"), # Triglycerides
            Observation(code="LIFESTYLE-SLEEP-HRS", value=5, category="Lifestyle"), # Sleep debt
            Observation(code="TFEQ-HEDONIC", value=20, category="Psychometry"), # High hedonic
            Observation(code="30522-7", value=4.5, category="Clinical"), # Inflammation
        ],
        medications=[
            MedicationStatement(code="RX-202", name="Prednisone") # Pharma sabotage
        ]
    )

    # 2. Run all engines
    acosta = AcostaPhenotypeMotor()
    eoss = EOSSStagingMotor()
    results = {
        "acosta": acosta.compute(encounter),
        "eoss": eoss.compute(encounter)
    }
    results.update(create_runner().run_all(encounter))

    # 3. Generate Report
    print("\n[Generating Final Clinical Report]...")
    report = report_service.generate_report(results, encounter)
    
    print(f"\nReport ID: {report.report_id}")
    print("\n--- TECHNICAL SUMMARY ---")
    print(report.technical_summary)
    print("\n--- RADAR DATA ---")
    print(json.dumps(report.phenotype_radar_data, indent=2))

    # 4. Assertions
    assert "desregulación metabólico-circadiana" in report.technical_summary, "Narrative should correlate Sleep + Metabolic"
    assert "sabotaje farmacológico" in report.technical_summary, "Narrative should include pharma findings"
    assert report.phenotype_radar_data["Inflammation"] > 0, "Radar data should contain inflammation score"

    print("\n✅ Misión 5 Logic Verified: Report contains a professional, correlated narrative and structured radar data.")

if __name__ == "__main__":
    verify_mission_5()
