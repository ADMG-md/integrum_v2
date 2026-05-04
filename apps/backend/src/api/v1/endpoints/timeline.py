from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.timeline_service import timeline_service
from typing import Dict, List, Any
import structlog

from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel

logger = structlog.get_logger()

router = APIRouter()

@router.get("/{patient_id}")
async def get_patient_timeline(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.AUDITOR]))
):
    """
    Retrieves the clinical timeline for a patient.
    Aggregates all motor decisions over time.
    """
    try:
        data = await timeline_service.get_patient_progress(db, patient_id)
        if not data:
            return {"message": "No history found for this patient", "timeline": {}}
        return {"patient_id": patient_id, "timeline": data}
    except Exception as e:
        logger.error("timeline_error", patient_id=patient_id, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Error retrieving clinical timeline")
