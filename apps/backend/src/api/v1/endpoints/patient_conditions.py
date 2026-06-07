from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database import get_db
from src.models.encounter import PatientConditionModel
from src.schemas.patient_condition import PatientConditionCreate, PatientConditionUpdate, PatientConditionRead
from src.services.auth_service import AuthService, check_role
from src.models.user import UserModel, UserRole

router = APIRouter()

@router.post("/", response_model=PatientConditionRead)
async def create_patient_condition(
    condition_in: PatientConditionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.NUTRITION_PHYSICIAN])
    ),
):
    db_condition = PatientConditionModel(**condition_in.model_dump())
    db.add(db_condition)
    await db.commit()
    await db.refresh(db_condition)
    return db_condition


@router.get("/patient/{patient_id}", response_model=List[PatientConditionRead])
async def list_patient_conditions(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user),
):
    stmt = select(PatientConditionModel).where(PatientConditionModel.patient_id == patient_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{condition_id}", response_model=PatientConditionRead)
async def update_patient_condition_status(
    condition_id: str,
    update_in: PatientConditionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.NUTRITION_PHYSICIAN])
    ),
):
    stmt = select(PatientConditionModel).where(PatientConditionModel.id == condition_id)
    result = await db.execute(stmt)
    db_condition = result.scalar_one_or_none()

    if not db_condition:
        raise HTTPException(status_code=404, detail="Condition not found")

    db_condition.status = update_in.status
    await db.commit()
    await db.refresh(db_condition)
    return db_condition
