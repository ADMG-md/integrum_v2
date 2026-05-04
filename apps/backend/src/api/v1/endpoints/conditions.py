from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.condition import Condition
from src.models.user import UserModel, UserRole
from src.schemas.condition import ConditionCreate, ConditionRead
from src.services.auth_service import AuthService, check_role
from typing import List

router = APIRouter()


@router.post("/", response_model=ConditionRead)
async def create_condition(
    condition_in: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.NUTRITION_PHYSICIAN])
    ),
):
    # NEW-01 fix: endpoint now requires authenticated physician or superadmin
    db_condition = Condition(**condition_in.model_dump())
    db.add(db_condition)
    await db.commit()
    await db.refresh(db_condition)
    return db_condition


@router.get("/", response_model=List[ConditionRead])
async def list_conditions(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    # NEW-01 fix: requires authentication to read clinical condition catalog
    result = await db.execute(select(Condition))
    return result.scalars().all()
