from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from src.database import get_db
from src.models.user import UserModel, UserRole
from src.services.auth_service import AuthService, check_role
from pydantic import BaseModel, EmailStr

router = APIRouter()

class ProfessionalCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

class ProfessionalRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    tenant_id: str

@router.post("/", response_model=ProfessionalRead)
async def register_professional(
    prof_in: ProfessionalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.SUPERADMIN, UserRole.ADMINSTAFF]))
):
    """
    Registers a new health professional or administrative staff.
    """
    # Check if user exists
    result = await db.execute(select(UserModel).where(UserModel.email == prof_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already registered")

    # If ADMINSTAFF is creating, they can only create for their own tenant
    tenant_id = current_user.tenant_id
    
    hashed_password = AuthService.get_password_hash(prof_in.password)
    user = UserModel(
        email=prof_in.email,
        hashed_password=hashed_password,
        full_name=prof_in.full_name,
        role=prof_in.role.value,
        tenant_id=tenant_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/", response_model=List[ProfessionalRead])
async def list_professionals(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.SUPERADMIN, UserRole.ADMINSTAFF, UserRole.AUDITOR]))
):
    """
    Lists all professionals for the current tenant.
    """
    stmt = select(UserModel).where(UserModel.tenant_id == current_user.tenant_id)
    if current_user.role == UserRole.SUPERADMIN:
        stmt = select(UserModel) # Superadmin sees all
        
    result = await db.execute(stmt)
    return result.scalars().all()
