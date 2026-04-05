import asyncio
import sys
import os

# Add apps/backend to path
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

from src.database import SessionLocal
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        # 1. Find a physician or superadmin
        stmt = select(UserModel).where(UserModel.role.in_([UserRole.PHYSICIAN, UserRole.SUPERADMIN]))
        res = await db.execute(stmt)
        user = res.scalars().first()
        
        # 2. Find a patient
        from src.models.encounter import Patient
        stmt_p = select(Patient)
        res_p = await db.execute(stmt_p)
        patient = res_p.scalars().first()
        
        if not user:
            print("ERROR: No physician or superadmin found in DB.")
            return

        # Create token
        token = AuthService.create_access_token(data={"sub": user.email, "role": user.role})
        print(f"TOKEN: {token}")
        if patient:
            print(f"PATIENT_ID: {patient.id}")
        else:
            print("PATIENT_ID: NONE")

if __name__ == "__main__":
    asyncio.run(main())
