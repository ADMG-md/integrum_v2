import asyncio
from src.database import SessionLocal
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService
from sqlalchemy import select

async def create_test_user():
    email = "hardening-tester@integrum.ai"
    password = "test-password-123"
    
    async with SessionLocal() as db:
        result = await db.execute(select(UserModel).where(UserModel.email == email))
        user = result.scalars().first()
        
        if not user:
            hashed_password = AuthService.get_password_hash(password)
            user = UserModel(
                email=email,
                hashed_password=hashed_password,
                full_name="Hardening Tester",
                role=UserRole.INTERNAL_MEDICINE.value
            )
            db.add(user)
            await db.commit()
            print(f"✅ User {email} created.")
        else:
            print(f"ℹ️ User {email} already exists.")

if __name__ == "__main__":
    asyncio.run(create_test_user())
