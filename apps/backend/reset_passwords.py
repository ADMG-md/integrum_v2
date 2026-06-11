import asyncio
from src.database import SessionLocal
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService
from sqlalchemy import select

async def reset_users():
    users_to_ensure = [
        {
            "email": "doctor@integrum.ai",
            "password": "doctor123",
            "name": "Dr. Precision (Endocrino)",
            "role": UserRole.PHYSICIAN.value
        },
        {
            "email": "hardening-tester@integrum.ai",
            "password": "test-password-123",
            "name": "Hardening Tester",
            "role": UserRole.PHYSICIAN.value
        },
        {
            "email": "admin@integrum.ai",
            "password": "admin123",
            "name": "Integrum Super Admin",
            "role": UserRole.SUPERADMIN.value
        }
    ]

    async with SessionLocal() as db:
        for u_info in users_to_ensure:
            result = await db.execute(select(UserModel).where(UserModel.email == u_info["email"]))
            user = result.scalars().first()
            
            hashed = AuthService.get_password_hash(u_info["password"])
            if user:
                user.hashed_password = hashed
                user.role = u_info["role"]
                print(f"🔄 Password and role reset for user: {u_info['email']}")
            else:
                user = UserModel(
                    email=u_info["email"],
                    hashed_password=hashed,
                    full_name=u_info["name"],
                    role=u_info["role"]
                )
                db.add(user)
                print(f"✅ User created: {u_info['email']}")
        
        await db.commit()
    print("All credentials have been synchronized.")

if __name__ == "__main__":
    asyncio.run(reset_users())
