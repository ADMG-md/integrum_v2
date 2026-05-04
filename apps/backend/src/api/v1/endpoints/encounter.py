from fastapi import APIRouter, HTTPException, Depends
from src.schemas.encounter import (
    EncounterCreate,
    EncounterFinalizeSchema,
    ProcessResponseSchema,
)
from src.services.encounter_orchestrator import process_encounter, finalize_encounter_logic
from src.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
import structlog

from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel

logger = structlog.get_logger()
router = APIRouter()


@router.post("/process", response_model=ProcessResponseSchema)
async def process_encounter_t0(
    payload: EncounterCreate,
    generate_report: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """
    T0 Clinical Engine Entry point.
    Receives clinical, genomic, and epigenetic data, runs all engines, and returns high-precision insights.
    """
    return await process_encounter(db, payload, current_user, generate_report)


@router.patch("/{encounter_id}/finalize")
async def finalize_encounter(
    encounter_id: str,
    payload: EncounterFinalizeSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role(
            [UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.NUTRITION_PHYSICIAN]
        )
    ),
):
    """
    Finalize the clinical encounter, locking it for further changes.
    Persists clinical notes and prescribed action plan.
    Business logic delegated to encounter_orchestrator.finalize_encounter_logic (DT-01).
    """
    return await finalize_encounter_logic(db, encounter_id, payload, current_user)


@router.get("/{encounter_id}")
async def get_encounter(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role(
            [UserRole.PHYSICIAN, UserRole.SUPERADMIN, UserRole.NUTRITION_PHYSICIAN]
        )
    ),
):
    """Retrieve full details of a single encounter."""
    from src.models.encounter import EncounterModel

    stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    return {
        "id": encounter.id,
        "patient_id": encounter.patient_id,
        "status": encounter.status,
        "reason_for_visit": encounter.reason_for_visit,
        "personal_history": encounter.personal_history,
        "family_history": encounter.family_history,
        "phenotype_result": encounter.phenotype_result,
        "ai_narrative": encounter.ai_narrative,
        "clinical_notes": encounter.clinical_notes,
        "plan_of_action": encounter.plan_of_action,
        "agreement_rate": encounter.agreement_rate,
        "created_at": encounter.created_at.isoformat()
        if encounter.created_at
        else None,
    }


@router.get("/patient/{patient_id}/latest")
async def get_latest_encounter(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """
    Returns the most recent finalized/analysed encounter for a patient.
    Used to pre-populate follow-up consultation forms (control mode).
    """
    from src.models.encounter import EncounterModel

    stmt = (
        select(EncounterModel)
        .where(EncounterModel.patient_id == patient_id)
        .where(EncounterModel.phenotype_result.isnot(None))
        .order_by(EncounterModel.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        return None

    return {
        "id": encounter.id,
        "status": encounter.status,
        "reason_for_visit": encounter.reason_for_visit,
        "phenotype_result": encounter.phenotype_result,
        "clinical_notes": encounter.clinical_notes,
        "plan_of_action": encounter.plan_of_action,
        "personal_history": encounter.personal_history,
        "family_history": encounter.family_history,
        "psychometrics": encounter.psychometrics,
        "created_at": encounter.created_at.isoformat()
        if encounter.created_at
        else None,
    }


@router.get("/patient/{patient_id}")
async def get_patient_encounters(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """List all encounters for a specific patient."""
    from src.models.encounter import EncounterModel

    stmt = (
        select(EncounterModel)
        .where(EncounterModel.patient_id == patient_id)
        .options(
            selectinload(EncounterModel.observations),
            selectinload(EncounterModel.conditions),
        )
        .order_by(EncounterModel.created_at.desc())
    )
    result = await db.execute(stmt)
    encounters = result.scalars().all()

    return encounters
