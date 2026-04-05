from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from src.database import get_db
from src.models.tenant import Tenant
from src.schemas.tenant import TenantCreate, TenantRead
from src.services.auth_service import check_role
from src.models.user import UserModel, UserRole

router = APIRouter()

@router.post("/", response_model=TenantRead)
async def create_tenant(
    tenant_in: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.SUPERADMIN]))
):
    """
    Registers a new Enterprise Client (Tenant).
    """
    # Check if slug exists
    stmt = select(Tenant).where(Tenant.slug == tenant_in.slug)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tenant slug already occupied.")
        
    new_tenant = Tenant(**tenant_in.model_dump())
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)
    return new_tenant

@router.get("/", response_model=List[TenantRead])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.SUPERADMIN, UserRole.AUDITOR]))
):
    """
    Lists all active tenants.
    """
    stmt = select(Tenant)
    result = await db.execute(stmt)
    return result.scalars().all()
