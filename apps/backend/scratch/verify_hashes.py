import asyncio
from src.database import SessionLocal
from src.models.user import UserModel
from src.services.auth_service import AuthService
from sqlalchemy import select

async def verify_hashes():
    async with SessionLocal() as db:
        result = await db.execute(select(UserModel))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.email}")
            print(f"  Hash: {u.hashed_password}")
            # Try to verify some common/default passwords
            for p in ["admin123", "doctor123", "paciente123", "auditor123", "gerente123", "nutri123", "test-password-123"]:
                try:
                    verified = AuthService.verify_password(p, u.hashed_password)
                    if verified:
                        print(f"  --> MATCH FOUND: password is '{p}'")
                except Exception as e:
                    print(f"  --> Error verifying '{p}': {e}")

if __name__ == "__main__":
    asyncio.run(verify_hashes())
