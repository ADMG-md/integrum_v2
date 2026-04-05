import asyncio
from src.database import SessionLocal
from src.models.user import UserModel
from sqlalchemy import select

async def list_users():
    async with SessionLocal() as db:
        result = await db.execute(select(UserModel))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.email}, Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(list_users())
