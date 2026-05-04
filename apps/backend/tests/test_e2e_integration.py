import sys
import os
import json
from datetime import datetime

# Add apps/backend to path
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

from src.engines.domain import (
    Encounter,
    Observation,
    Condition,
    DemographicsSchema,
    MetabolicPanelSchema,
)
from src.engines.specialty_runner import create_runner
from src.schemas.encounter import AdjudicationResultSchema
from src.schemas.report import ClinicalReportSchema

def verify_e2e_flow():
    print("🚀 INTEGRUM V2.6: HARDENED END-TO-END INTEGRATION VERIFICATION")
    
    # 1. Simulate Engine Execution (The "Clinical Pulse")
    print("\n[STEP 1] Running Clinical Engines...")
    e = Encounter(
        id="E2E-TEST-VOLT",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(),
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="GAD-7", value=12), # Acosta Probable
            Observation(code="8302-2", value=175.0),
            Observation(code="29463-7", value=115.0),
            Observation(code="2160-0", value=1.8), # Renal Priority
            Observation(code="FFM-001", value=80.0),
        ],
        metadata={"sex": "M", "age": 45}
    )
    
    results = create_runner().run_all(e)
    # Inject Acosta and EOSS which are usually run in the endpoint loop
    from src.engines.acosta import AcostaPhenotypeMotor
    from src.engines.eoss import EOSSStagingMotor
    results["acosta"] = AcostaPhenotypeMotor().compute(e)
    results["eoss"] = EOSSStagingMotor().compute(e)
    
    print(f"   Motors executed: {list(results.keys())}")
    
    # 2. Simulate Database Persistence Structure
    print("\n[STEP 2] Simulating JSON Persistence (phenotype_result)...")
    persistent_results = {name: res.model_dump() for name, res in results.items()}
    
    # Verify presence of Maestro fields in the dict (what goes to DB)
    acosta_db = persistent_results["acosta"]
    print(f"   DB check (Acosta): estado_ui={acosta_db.get('estado_ui')}, recs={acosta_db.get('recomendacion_farmacologica')}")
    assert "estado_ui" in acosta_db, "Missing estado_ui in DB-ready dict"
    
    # 3. Simulate API Serialization (The "Front-End Bridge")
    print("\n[STEP 3] Verifying Pydantic Serialization...")
    # This mimics what ReportService.generate_report does
    report = ClinicalReportSchema(
        report_id="E2E-REPORT-001",
        technical_summary="E2E Integration proof.",
        engine_adjudications={name: AdjudicationResultSchema(**res) for name, res in persistent_results.items()},
        suggestions=[]
    )
    
    json_payload = report.model_dump_json()
    parsed_json = json.loads(json_payload)
    
    # Verify the final JSON sent to the browser
    front_acosta = parsed_json["engine_adjudications"]["acosta"]
    print(f"   Front-end JSON check (Acosta):")
    print(f"     - estado_ui: {front_acosta.get('estado_ui')}")
    print(f"     - dato_faltante: {front_acosta.get('dato_faltante')}")
    print(f"     - pharma_recs: {front_acosta.get('recomendacion_farmacologica')}")
    
    assert front_acosta.get("estado_ui") == "PROBABLE_WARNING", "Serialization failure: estado_ui lost"
    assert len(front_acosta.get("recomendacion_farmacologica", [])) > 0, "Serialization failure: Pharma recs lost"
    
    print("\n🏆 E2E CONNECTIVITY VERIFIED. Engine -> DB -> API -> UI flow is intact.")

if __name__ == "__main__":
    try:
        verify_e2e_flow()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ E2E VERIFICATION FAILED: {str(e)}")
        sys.exit(1)
