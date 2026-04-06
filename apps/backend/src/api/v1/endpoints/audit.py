from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.audit import AdjudicationLog
from src.schemas.audit import AdjudicationOverride
from sqlalchemy import select
import uuid

from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel

router = APIRouter()

@router.post("/override")
async def override_adjudication(
    payload: AdjudicationOverride, 
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN]))
):
    """
    SaMD Physician Override. 
    Allows a physician to correct a machine-generated decision.
    Ensures Audit Trail compliance as per IEC 62304.
    """
    stmt = select(AdjudicationLog).where(AdjudicationLog.id == uuid.UUID(payload.log_id))
    result = await db.execute(stmt)
    log_entry = result.scalar_one_or_none()

    if not log_entry:
        raise HTTPException(status_code=404, detail="Adjudication log not found")

    # Update with override data
    # override_reason_code is the structured field for research analysis.
    # override_reason stores the enum value as string for backward compatibility.
    log_entry.is_overridden = True
    log_entry.physician_value = payload.physician_value
    log_entry.override_reason = payload.override_reason_code.value  # structured, not free text
    log_entry.physician_id = payload.physician_id

    await db.commit()

    return {
        "status": "overridden",
        "log_id": str(log_entry.id),
        "new_value": log_entry.physician_value,
        "override_reason_code": payload.override_reason_code.value,
        "override_reason_text": payload.override_reason_text,
    }
