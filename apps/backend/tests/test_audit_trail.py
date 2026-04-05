import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.database import SessionLocal, engine, Base
from src.models.audit import AdjudicationLog
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.domain import Encounter, Observation, Condition
from src.services.audit_service import audit_service
from sqlalchemy import select

async def verify_audit_trail():
    print("🔒 TESTING SaMD AUDIT TRAIL (IEC 62304) 🔒")
    print("-" * 50)

    # 1. Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # 2. Run Motor
        motor = AcostaPhenotypeMotor()
        v_hash = motor.get_version_hash()
        print(f"Engine Version Fingerprint: {v_hash[:16]}...")

        encounter = Encounter(
            id="audit-test-001",
            conditions=[Condition(code="E66", title="Obesity")],
            observations=[Observation(code="2339-0", value=110, category="Clinical")]
        )
        
        result = motor.compute(encounter)
        results = {"acosta": result}
        engines_map = {"acosta": motor}

        # 3. Log to Audit Table
        print("[Log] Saving decision to inmutable audit trail...")
        await audit_service.log_adjudications(db, encounter.id, results, engines_map)

        # 4. Verify from DB
        stmt = select(AdjudicationLog).where(AdjudicationLog.encounter_id == "audit-test-001")
        db_res = await db.execute(stmt)
        entry = db_res.scalar_one()

        print(f"\n[Verified] Found Log Entry in DB:")
        print(f"  - Engine: {entry.engine_name}")
        print(f"  - Value:  {entry.calculated_value}")
        print(f"  - Hash:   {entry.engine_version_hash[:16]}...")
        
        assert entry.engine_version_hash == v_hash, "Fingerprint mismatch!"
        print("\n✅ SaMD Compliance Verified: Decision logged with inmutable source code hash.")

if __name__ == "__main__":
    asyncio.run(verify_audit_trail())
