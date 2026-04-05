from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.condition import Condition
from src.schemas.condition import ConditionCreate, ConditionRead
from typing import List

router = APIRouter()

@router.post("/", response_model=ConditionRead)
async def create_condition(condition_in: ConditionCreate, db: AsyncSession = Depends(get_db)):
    db_condition = Condition(**condition_in.model_dump())
    db.add(db_condition)
    await db.commit()
    await db.refresh(db_condition)
    return db_condition

@router.get("/", response_model=List[ConditionRead])
async def list_conditions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Condition))
    return result.scalars().all()
