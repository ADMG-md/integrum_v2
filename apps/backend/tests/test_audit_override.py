import sys
import os
import httpx
import asyncio

# Add apps/backend to path
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

BASE_URL = "http://localhost:8000/api/v1/encounters"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkb2N0b3JAaW50ZWdydW0uYWkiLCJyb2xlIjoicGh5c2ljaWFuIiwiZXhwIjoxNzc0Nzk5MjEzfQ.cCbgZA5z6kYkBmlhGGZbbcz49GJjONOehOF9PU57IQY"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

async def verify_audit_lock():
    print("🧪 VERIFYING HUMAN-AI AUDIT LOCK (MINCIENCIAS)")
    
    async with httpx.AsyncClient() as client:
        # 1. Create Encounter that triggers a recommendation
        # GAD-7 = 15 -> Acosta suggests Naltrexona/Bupropión
        payload = {
            "patient_id": "6b56042f-0dd8-4922-a11d-2ba29b7ec26d",
            "observations": [
                {"code": "GAD-7", "value": 15},
                {"code": "8302-2", "value": 170.0},
                {"code": "29463-7", "value": 110.0}
            ],
            "reason_for_visit": "Test Audit Lock",
            "conditions": [{"code": "E66.9", "title": "Obesity, unspecified"}]
        }
        
        print("   Step 1: Processing encounter...")
        resp = await client.post(f"{BASE_URL}/process", json=payload, headers=HEADERS)
        if resp.status_code != 200:
            print(f"❌ Failed to process encounter: {resp.text}")
            return
        
        results = resp.json()
        encounter_id = results.get("acosta", {}).get("log_id") # Extract ID if returned in schema, or find it
        # Actually in our /process it returns a dict of results. Let's get encounter_id from somewhere.
        # Wait, /process in encounter.py returns persistent_results which is names -> results.
        # The encounter_id is not directly in the JSON response of /process based on my last view.
        # But our test database will have it. 
        # For simplicity in this test script, assuming we have a way to get the last encounter.
        
        # Let's use a simpler approach: Just try to finalize a known encounter ID.
        # Since I can't easily get the ID from /process without modifying it to return it,
        # I'll check the db for the last one.
        
        from src.database import SessionLocal
        from src.models.encounter import EncounterModel
        from sqlalchemy import select
        
        async with SessionLocal() as db:
            stmt = select(EncounterModel).order_by(EncounterModel.created_at.desc()).limit(1)
            res = await db.execute(stmt)
            enc = res.scalar_one_or_none()
        
        if not enc:
            print("❌ No encounter found in DB.")
            return
            
        encounter_id = enc.id
        print(f"   Using Encounter ID: {encounter_id}")
        
        # 2. Try to Finalize WITHOUT the recommendation and WITHOUT audit payload
        print("   Step 2: Testing Discrepancy Lock (No Audit Payload)...")
        finalize_payload = {
            "clinical_notes": "Patient refuses medication.",
            "plan_of_action": {
                "prescribed_medications": [] # Bypassing Naltrexona/Bupropión
            }
        }
        
        resp = await client.patch(f"{BASE_URL}/{encounter_id}/finalize", json=finalize_payload, headers=HEADERS)
        print(f"   Response Status: {resp.status_code}")
        if resp.status_code == 400 and "AUDIT_REQUIRED" in resp.text:
            print("✅ Passed: System correctly blocked finalization without audit justification.")
        else:
            print(f"❌ Failed: System did not block finalization. Response: {resp.text}")
            return

        # 3. Try to Finalize WITH audit payload
        print("\n   Step 3: Testing Discrepancy with Audit Payload...")
        finalize_payload["audit_payload"] = [
            {
                "engine_name": "AcostaPhenotypeMotor",
                "engine_version_hash": "PROTOTYPE-V2.2",
                "decision_type": "OVERRIDE",
                "reason_code": "OVERRIDE_PATIENT_REFUSAL",
                "physician_id": "DR-001"
            }
        ]
        
        resp = await client.patch(f"{BASE_URL}/{encounter_id}/finalize", json=finalize_payload, headers=HEADERS)
        print(f"   Response Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✅ Passed: System accepted finalization with audit justification.")
        else:
            print(f"❌ Failed: System rejected valid finalization. Response: {resp.text}")
            return

if __name__ == "__main__":
    asyncio.run(verify_audit_lock())
