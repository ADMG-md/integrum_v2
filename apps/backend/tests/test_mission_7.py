import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.database import SessionLocal, engine, Base
from src.models.encounter import Patient, EncounterModel, ObservationModel
from src.models.audit import AdjudicationLog
from src.schemas.encounter import EncounterCreate, ObservationSchema
from src.api.v1.endpoints.encounter import process_encounter_t0
import json

async def verify_mission_7_timeline():
    print("📈 TESTING MISSION 7: TIMELINE & REJUVENATION 📈")
    print("-" * 50)

    # 1. Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        patient_id = "PAT-TIMELINE-007"
        
        # --- ENCOUNTER 1 (T0): UNHEALTHY STATE ---
        print("[Step 1] Processing T0: Patient with metabolic syndrome...")
        t0_payload = EncounterCreate(
            patient_id=patient_id,
            observations=[
                ObservationSchema(code="PATIENT-AGE", value=50.0),
                ObservationSchema(code="2339-0", value=120.0), # High Glucose
                ObservationSchema(code="1988-5", value=4.5),   # High CRP
            ]
        )
        t0_res = await process_encounter_t0(t0_payload, generate_report=True, db=db)
        bio_age_t0 = t0_res.engine_adjudications["BiologicalAgeMotor"].calculated_value
        print(f"  > Chrono Age: 50 | BioAge T0: {bio_age_t0}")

        # --- ENCOUNTER 2 (T1): IMPROVED STATE ---
        print("\n[Step 2] Processing T1 (3 months later): Patient optimized...")
        t1_payload = EncounterCreate(
            patient_id=patient_id,
            observations=[
                ObservationSchema(code="PATIENT-AGE", value=50.25), # Aging slightly
                ObservationSchema(code="2339-0", value=85.0),  # Optimal Glucose
                ObservationSchema(code="1988-5", value=0.4),   # Optimal CRP
            ]
        )
        t1_res = await process_encounter_t0(t1_payload, generate_report=True, db=db)
        bio_age_t1 = t1_res.engine_adjudications["BiologicalAgeMotor"].calculated_value
        print(f"  > Chrono Age: 50.25 | BioAge T1: {bio_age_t1}")

        # --- VERIFY TIMELINE ---
        from src.services.timeline_service import timeline_service
        timeline = await timeline_service.get_patient_progress(db, patient_id)
        
        bio_age_history = timeline.get("BiologicalAgeMotor", [])
        print("\n[Step 3] Timeline Verification:")
        for entry in bio_age_history:
            print(f"  - {entry['date']}: {entry['value']}")

        # Assertions
        assert len(bio_age_history) == 2, "Should have 2 points in timeline"
        
        # Extract numeric age from string "XX.X años"
        age0 = float(bio_age_t0.split()[0])
        age1 = float(bio_age_t1.split()[0])
        
        assert age1 < age0, "Rejuvenecimiento failed: BioAge T1 should be LOWER than T0"
        
        print("\n✅ MISSION 7 CORE VERIFIED: BioAge calculation and Timeline persistence working.")

if __name__ == "__main__":
    asyncio.run(verify_mission_7_timeline())
