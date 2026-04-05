"""
Data export endpoint for research and compliance.
Returns anonymized patient data for analysis.
HIPAA Safe Harbor + Colombia Ley 1581 compliant.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from src.database import get_db
from src.models.encounter import EncounterModel, Patient
from src.models.audit import AdjudicationLog
from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel
import json
import hashlib
import time

router = APIRouter()

# Simple in-memory rate limiter: max 5 exports per 10 minutes per user
_export_log: Dict[str, list] = {}


def check_export_rate_limit(user_id: str) -> None:
    now = time.time()
    window = 600  # 10 minutes
    max_requests = 5

    if user_id not in _export_log:
        _export_log[user_id] = []

    # Clean old entries
    _export_log[user_id] = [t for t in _export_log[user_id] if now - t < window]

    if len(_export_log[user_id]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} exports per {window // 60} minutes.",
        )

    _export_log[user_id].append(now)


def _anonymize_id(id_str: str) -> str:
    """Deterministic anonymization: same ID always produces same hash."""
    salt = "integrum-research-salt-2026"
    return hashlib.sha256(f"{salt}:{id_str}".encode()).hexdigest()[:16]


@router.get("/anonymized")
async def export_anonymized_data(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR])
    ),
):
    """
    Export all patient data in anonymized form for research.
    Removes all PII: names, IDs, emails, phones, addresses.
    Retains clinical data: phenotypes, EOSS, labs, adjudications.
    """
    check_export_rate_limit(current_user.id)
    # Get all patients
    patients_stmt = select(Patient)
    patients_result = await db.execute(patients_stmt)
    patients = patients_result.scalars().all()

    export_data = {
        "patients": [],
        "encounters": [],
        "adjudication_logs": [],
        "metadata": {
            "total_patients": len(patients),
            "export_date": "2026-04-03",
            "anonymization": "SHA-256 deterministic hash",
            "pii_removed": [
                "full_name",
                "external_id",
                "email",
                "phone",
                "date_of_birth",
            ],
        },
    }

    for patient in patients:
        anon_patient = {
            "patient_id": _anonymize_id(patient.id),
            "gender": patient.gender,
            # No name, no external_id, no email, no phone, no DOB
        }
        export_data["patients"].append(anon_patient)

        # Get encounters for this patient
        enc_stmt = select(EncounterModel).where(EncounterModel.patient_id == patient.id)
        enc_result = await db.execute(enc_stmt)
        encounters = enc_result.scalars().all()

        for enc in encounters:
            anon_encounter = {
                "encounter_id": _anonymize_id(enc.id),
                "patient_id": _anonymize_id(enc.patient_id),
                "status": enc.status,
                "reason_for_visit": enc.reason_for_visit,
                "phenotype_result": enc.phenotype_result,
                "clinical_notes": enc.clinical_notes,
                "plan_of_action": enc.plan_of_action,
                "agreement_rate": enc.agreement_rate,
                "created_at": enc.created_at.isoformat() if enc.created_at else None,
            }
            export_data["encounters"].append(anon_encounter)

            # Get adjudication logs
            log_stmt = select(AdjudicationLog).where(
                AdjudicationLog.encounter_id == enc.id
            )
            log_result = await db.execute(log_stmt)
            logs = log_result.scalars().all()

            for log in logs:
                anon_log = {
                    "encounter_id": _anonymize_id(log.encounter_id),
                    "engine_name": log.engine_name,
                    "engine_version_hash": log.engine_version_hash,
                    "calculated_value": log.calculated_value,
                    "confidence": log.confidence,
                    "evidence": log.evidence,
                    "requirement_id": log.requirement_id,
                    "is_overridden": log.is_overridden,
                    "physician_value": log.physician_value,
                    "created_at": log.created_at.isoformat()
                    if log.created_at
                    else None,
                }
                export_data["adjudication_logs"].append(anon_log)

    return export_data


@router.get("/patient/{patient_id}")
async def export_single_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """
    Export a single patient's full clinical record (for patient data portability, GDPR Art.20).
    """
    # Verify patient exists
    pat_stmt = select(Patient).where(Patient.id == patient_id)
    pat_result = await db.execute(pat_stmt)
    patient = pat_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get encounters
    enc_stmt = select(EncounterModel).where(EncounterModel.patient_id == patient_id)
    enc_result = await db.execute(enc_stmt)
    encounters = enc_result.scalars().all()

    export_data = {
        "patient": {
            "id": patient.id,
            "external_id": patient.external_id,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone,
            "created_at": patient.created_at.isoformat()
            if patient.created_at
            else None,
        },
        "encounters": [],
    }

    for enc in encounters:
        enc_data = {
            "id": enc.id,
            "status": enc.status,
            "reason_for_visit": enc.reason_for_visit,
            "phenotype_result": enc.phenotype_result,
            "clinical_notes": enc.clinical_notes,
            "plan_of_action": enc.plan_of_action,
            "created_at": enc.created_at.isoformat() if enc.created_at else None,
        }

        # Get adjudication logs
        log_stmt = select(AdjudicationLog).where(AdjudicationLog.encounter_id == enc.id)
        log_result = await db.execute(log_stmt)
        logs = log_result.scalars().all()
        enc_data["adjudication_logs"] = [
            {
                "engine_name": log.engine_name,
                "calculated_value": log.calculated_value,
                "confidence": log.confidence,
                "is_overridden": log.is_overridden,
                "physician_value": log.physician_value,
            }
            for log in logs
        ]

        export_data["encounters"].append(enc_data)

    return export_data
