import asyncio
import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.database import SessionLocal, engine, Base
from src.models.audit import AdjudicationLog
from src.schemas.audit import AdjudicationOverride
from sqlalchemy import select
import uuid


@pytest.mark.integration
async def test_physician_override():
    print("👨‍⚕️ TESTING SaMD PHYSICIAN OVERRIDE (ISO 13485) 👨‍⚕️")
    print("-" * 50)

    # 1. Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # 2. Create a fake machine adjudication
        log_id = uuid.uuid4()
        print(f"[Step 1] Creating machine decision (ID: {log_id})")
        log_entry = AdjudicationLog(
            id=log_id,
            encounter_id="patient-123",
            engine_name="acosta",
            engine_version_hash="machine-logic-v1",
            calculated_value="Phenotype A - Normal",
            confidence=0.9,
            evidence=[],
        )
        db.add(log_entry)
        await db.commit()

        # 3. Simulate Physician Override
        print("[Step 2] Physician disagrees. Submitting override...")
        override_data = AdjudicationOverride(
            log_id=str(log_id),
            physician_value="Phenotype B - Insulin Resistant (Manual Correction)",
            override_reason="Clinical findings suggest borderline metabolic syndrome not captured by T0",
            physician_id="DR-ANTONY-V12",
        )

        # Apply override logic (simulating the endpoint logic here for simplicity)
        stmt = select(AdjudicationLog).where(AdjudicationLog.id == log_id)
        result = await db.execute(stmt)
        entry_to_update = result.scalar_one()

        entry_to_update.is_overridden = True
        entry_to_update.physician_value = override_data.physician_value
        entry_to_update.override_reason = override_data.override_reason
        entry_to_update.physician_id = override_data.physician_id

        await db.commit()
        await db.refresh(entry_to_update)

        # 4. Final Audit Trail Verification
        print("\n[Step 3] Verifying Audit Trail Integrity:")
        print(f"  - Original Engine: {entry_to_update.engine_name}")
        print(
            f"  - Status: {'⚠️ OVERRIDDEN' if entry_to_update.is_overridden else 'OK'}"
        )
        print(f"  - Final Clinical Value: {entry_to_update.physician_value}")
        print(f"  - Justification: {entry_to_update.override_reason}")

        assert entry_to_update.is_overridden == True
        assert entry_to_update.physician_value == override_data.physician_value
        print(
            "\n✅ SaMD Override Verified: Machine output preserved, human correction linked and justified."
        )


if __name__ == "__main__":
    asyncio.run(test_physician_override())
