from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db
from src.models.consent import PatientConsent
from src.schemas.consent import ConsentCreate, ConsentRead
from src.services.auth_service import AuthService
from src.models.user import UserModel

router = APIRouter()

@router.post("/", response_model=ConsentRead)
async def record_consent(
    consent_in: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user)
):
    """
    Persists a patient's informed consent.
    In a real SaMD, this would be an immutable record.
    """
    new_consent = PatientConsent(
        patient_id=consent_in.patient_id,
        encounter_id=consent_in.encounter_id,
        consent_type=consent_in.consent_type,
        is_granted=consent_in.is_granted,
        terms_version=consent_in.terms_version
    )
    # Store IP for audit trail
    new_consent.signer_ip = request.client.host if request.client else "unknown"
    
    db.add(new_consent)
    await db.commit()
    await db.refresh(new_consent)
    return new_consent

@router.get("/patient/{patient_id}", response_model=Optional[ConsentRead])
async def get_latest_consent(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(AuthService.get_current_user)
):
    """
    Checks the latest consent status for a patient.
    """
    stmt = (
        select(PatientConsent)
        .where(PatientConsent.patient_id == patient_id)
        .order_by(PatientConsent.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
