"""
FastAPI dependencies for compliance guards.
HIPAA/GDPR/Ley 1581 compliance enforcement.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_db


async def require_consent(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Dependency that blocks any clinical processing without valid consent.
    HIPAA 45 CFR 164.508 / GDPR Art.6 / Colombia Ley 1581 Art.4
    """
    from src.models.consent import PatientConsent

    stmt = (
        select(PatientConsent)
        .where(PatientConsent.patient_id == patient_id)
        .where(PatientConsent.is_granted == True)
        .order_by(PatientConsent.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()

    if not consent:
        raise HTTPException(
            status_code=403,
            detail="Consentimiento informado no otorgado o revocado. No se puede procesar datos clínicos.",
        )
