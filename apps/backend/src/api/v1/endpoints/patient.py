from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from src.database import get_db
from src.models.encounter import Patient
from src.schemas.encounter import PatientRead, PatientCreate

from src.services.auth_service import AuthService
from src.models.user import UserModel

router = APIRouter()

@router.post("/", response_model=PatientRead)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user)
):
    """
    Register a new patient securely with demographics.
    """
    new_patient = Patient(
        tenant_id=current_user.tenant_id,
        external_id=patient_in.external_id,
    )
    new_patient.full_name = patient_in.full_name
    new_patient.date_of_birth = patient_in.date_of_birth
    new_patient.gender = patient_in.gender
    new_patient.email = patient_in.email
    new_patient.phone = patient_in.phone
    
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    return new_patient

@router.get("/", response_model=List[PatientRead])
async def get_patients(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user)
):
    """
    List patients for the current tenant.
    """
    result = await db.execute(
        select(Patient).where(Patient.tenant_id == current_user.tenant_id)
    )
    patients = result.scalars().all()
    return patients
@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user)
):
    """
    Retrieve a single patient by ID or external ID.
    """
    from src.services.vault_service import vault_service
    search_hash = vault_service.generate_blind_index(patient_id)
    
    stmt = select(Patient).where(
        (Patient.id == patient_id) | (Patient.external_id_hash == search_hash)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
