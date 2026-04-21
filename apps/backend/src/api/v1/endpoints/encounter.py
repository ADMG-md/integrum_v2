from fastapi import APIRouter, HTTPException, Depends
from src.schemas.encounter import (
    EncounterCreate,
    EncounterFinalizeSchema,
    ProcessResponseSchema,
)
from src.services.encounter_orchestrator import process_encounter
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
    """
    from src.models.encounter import EncounterModel

    stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # Human-AI Interaction Audit (MinCiencias Compliance) & Integrity Validation
    original_results = encounter.phenotype_result or {}
    total_audits = len(payload.audit_payload) if payload.audit_payload else 0
    agreements_count = 0

    if not payload.audit_payload and len(original_results) > 0:
        raise HTTPException(
            status_code=400,
            detail="AUDIT_REQUIRED: All AI interpretations must be audited before finalization.",
        )

    from src.models.audit import DecisionAuditLog, DecisionType, ReasonCode

    if payload.audit_payload:
        for audit in payload.audit_payload:
            eng_name = audit["engine_name"]
            req_decision = audit["decision_type"]
            req_hash = audit.get("engine_version_hash")

            # Validation 1: Version Hash Mismatch
            orig_hash = (
                original_results.get(eng_name, {}).get("integrity_hash") or "UNKNOWN"
            )
            if req_hash != orig_hash:
                raise HTTPException(
                    status_code=409,
                    detail=f"Version mismatch for {eng_name}. UI sent {req_hash}, DB expects {orig_hash}.",
                )

            # Validation 2: Cannot blindly force AGREEMENT on low-confidence insights
            orig_confidence = original_results.get(eng_name, {}).get("confidence", 1.0)
            estado_ui = original_results.get(eng_name, {}).get("estado_ui", "ANALYZED")

            if req_decision == "AGREEMENT" and (
                estado_ui == "INDETERMINATE_LOCKED" or orig_confidence < 0.65
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Integrity Violation: Cannot blindly validate '{eng_name}' (Confidence: {orig_confidence}). It requires manual context Override.",
                )

            if req_decision == "AGREEMENT":
                agreements_count += 1

            try:
                audit_log = DecisionAuditLog(
                    encounter_id=encounter_id,
                    engine_name=eng_name,
                    engine_version_hash=req_hash,
                    decision_type=DecisionType(req_decision),
                    reason_code=ReasonCode(audit["reason_code"]),
                    physician_id=current_user.id,
                )
                db.add(audit_log)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    # Calculate Agreement Rate
    if total_audits > 0:
        encounter.agreement_rate = round((agreements_count / total_audits) * 100, 2)

    encounter.status = "FINALIZED"
    encounter.clinical_notes = payload.clinical_notes
    encounter.plan_of_action = payload.plan_of_action
    encounter.physician_id = current_user.id

    # Persist outcome tracking fields (research dataset quality)
    if payload.weight_current_kg is not None:
        encounter.weight_current_kg = payload.weight_current_kg
    if payload.outcome_status is not None:
        encounter.outcome_status = payload.outcome_status
    if payload.adverse_event is not None:
        encounter.adverse_event = payload.adverse_event
    if payload.medication_changed is not None:
        encounter.medication_changed = payload.medication_changed
    if payload.adherence_reported is not None:
        encounter.adherence_reported = payload.adherence_reported

    await db.commit()
    return {"status": "finalized", "encounter_id": encounter_id}


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
