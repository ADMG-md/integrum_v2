"""
Data export endpoint for research and compliance.
Returns anonymized patient data for analysis.
HIPAA Safe Harbor + Colombia Ley 1581 compliant.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from src.database import get_db
from src.models.encounter import EncounterModel, Patient
from src.models.audit import AdjudicationLog
from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel
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


# ─────────────────────────────────────────────────────────────────────────────
# Motor columns (deterministic order for CSV header stability across exports)
# ─────────────────────────────────────────────────────────────────────────────
MOTOR_COLUMNS = [
    "AcostaPhenotypeMotor",
    "EOSSStagingMotor",
    "BiologicalAgeMotor",
    "MetabolicPrecisionMotor",
    "DeepMetabolicProxyMotor",
    "Lifestyle360Motor",
    "SarcopeniaMonitorMotor",
    "AnthropometryMotor",
    "EndocrineMotor",
    "HypertensionMotor",
    "InflammationMotor",
    "SleepApneaMotor",
    "LaboratoryStewardshipMotor",
    "FunctionalSarcopeniaMotor",
    "FLIMotor",
    "VAIMotor",
    "CMIMotor",
    "GLP1MonitoringMotor",
    "MetforminB12Motor",
    "CancerScreeningMotor",
    "ApoBApoA1Motor",
    "PulsePressureMotor",
    "ACEScoreEngine",
    "SGLT2iBenefitMotor",
    "FreeTestosteroneMotor",
    "VitaminDMotor",
    "CharlsonMotor",
    "KFREMotor",
    "FriedFrailtyMotor",
    "TyGBMIMotor",
    "CVDReclassifierMotor",
    "WomensHealthMotor",
    "MensHealthMotor",
    "CVDHazardMotor",
    "MarkovProgressionMotor",
    "ObesityMasterMotor",
    "ClinicalGuidelinesMotor",
    "LipidRiskPrecisionMotor",
    "DrugInteractionMotor",
    "PediatricNutritionMotor",
    "PrecisionNutritionMotor",
    "PharmaPrecisionMotor",
]


def _build_flat_row(
    patient: Patient,
    enc: EncounterModel,
    decision_map: Dict[str, Dict],  # engine_name → {decision_type, reason_code}
) -> Dict[str, Any]:
    """
    Build one flat row per encounter for research analysis.

    Per-motor columns (5 per motor):
      {Motor}_value      — calculated_value string (e.g. "PHENOTYPE_A", "3.2% risk")
      {Motor}_estado     — estado_ui (CONFIRMED / INDETERMINATE_LOCKED / etc.)
      {Motor}_confidence — float 0.0-1.0
      {Motor}_decision   — physician decision (AGREEMENT / OVERRIDE / None if not audited)
      {Motor}_reason     — ReasonCode structured vocabulary (why agreed/overrode)

    Every field null-safe: NULL means motor did not run or data was unavailable.
    """
    row: Dict[str, Any] = {
        # Identifiers (anonymized, deterministic)
        "patient_id": _anonymize_id(patient.id),
        "encounter_id": _anonymize_id(enc.id),
        "encounter_date": enc.created_at.date().isoformat() if enc.created_at else None,
        "encounter_status": enc.status,
        "reason_for_visit": enc.reason_for_visit,
        # Demographics
        "gender": patient.gender,
        # Physician-AI concordance
        "agreement_rate_pct": enc.agreement_rate,
        # Outcome tracking (Fix 2 — filled at finalize by physician)
        "outcome_weight_current_kg": enc.weight_current_kg,
        "outcome_status": enc.outcome_status,  # MEJORADO / ESTABLE / DETERIORO
        "outcome_adverse_event": enc.adverse_event,
        "outcome_medication_changed": enc.medication_changed,
        "outcome_adherence_reported": enc.adherence_reported,  # ALTA / MEDIA / BAJA
    }

    # Motor outputs — one block of 5 columns per motor
    results = enc.phenotype_result or {}
    for motor in MOTOR_COLUMNS:
        # Stable prefix: "AcostaPheno" from "AcostaPhenotypeMotor"
        prefix = motor.replace("Motor", "").replace("Engine", "")
        res = results.get(motor) or {}
        audit = decision_map.get(motor, {})

        row[f"{prefix}_value"] = res.get("calculated_value")
        row[f"{prefix}_estado"] = res.get("estado_ui")
        row[f"{prefix}_confidence"] = res.get("confidence")
        row[f"{prefix}_decision"] = audit.get("decision_type")  # AGREEMENT / OVERRIDE
        row[f"{prefix}_reason"] = audit.get("reason_code")  # structured vocabulary

    return row


# ─────────────────────────────────────────────────────────────────────────────
# GET /export/research/flat  — THE research dataset endpoint
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/research/flat")
async def export_research_flat(
    fmt: str = "csv",  # "csv" or "json"
    status_filter: str = "all",  # "all", "FINALIZED", "ANALYZED"
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR, UserRole.PHYSICIAN])
    ),
):
    """
    Research-grade flat export. One row per encounter, all motors flattened.

    Output columns:
      patient_id, encounter_id, encounter_date, encounter_status, gender,
      agreement_rate_pct,
      outcome_weight_current_kg, outcome_status, outcome_adverse_event,
      outcome_medication_changed, outcome_adherence_reported,
      {Motor}_value, {Motor}_estado, {Motor}_confidence,
      {Motor}_decision, {Motor}_reason  ← per each of 39 motors

    Usage:
      GET /export/research/flat          → CSV download
      GET /export/research/flat?fmt=json → JSON with metadata
      GET /export/research/flat?status_filter=FINALIZED → only finalized encounters

    Python:
      import pandas as pd
      df = pd.read_csv('integrum_research_export.csv')
      df[df['AcostaPheno_estado'] == 'CONFIRMED']['AcostaPheno_value'].value_counts()

    R:
      df <- read.csv('integrum_research_export.csv')
      table(df$AcostaPheno_value, df$outcome_status)
    """
    check_export_rate_limit(current_user.id)

    # Fetch all patients into a lookup map
    patients_stmt = select(Patient)
    patients_result = await db.execute(patients_stmt)
    patients: Dict[str, Patient] = {p.id: p for p in patients_result.scalars().all()}

    if not patients:
        if fmt == "csv":
            from fastapi.responses import Response

            return Response(content="No patients in database.", media_type="text/plain")
        return {"rows": [], "metadata": {"total_encounters": 0}}

    # Fetch encounters (optionally filtered by status)
    enc_stmt = select(EncounterModel)
    if status_filter != "all":
        enc_stmt = enc_stmt.where(EncounterModel.status == status_filter)
    enc_result = await db.execute(enc_stmt)
    encounters = enc_result.scalars().all()

    rows = []
    for enc in encounters:
        patient = patients.get(enc.patient_id)
        if not patient:
            continue  # Orphaned encounter — skip

        # Fetch physician decision audit (concordance per motor)
        from src.models.audit import DecisionAuditLog

        audit_stmt = select(DecisionAuditLog).where(
            DecisionAuditLog.encounter_id == enc.id
        )
        audit_result = await db.execute(audit_stmt)
        decision_map = {
            log.engine_name: {
                "decision_type": log.decision_type.value if log.decision_type else None,
                "reason_code": log.reason_code.value if log.reason_code else None,
            }
            for log in audit_result.scalars().all()
        }

        rows.append(_build_flat_row(patient, enc, decision_map))

    if not rows:
        if fmt == "csv":
            from fastapi.responses import Response

            return Response(
                content="No encounters match the filter.", media_type="text/plain"
            )
        return {
            "rows": [],
            "metadata": {"total_encounters": 0, "status_filter": status_filter},
        }

    if fmt == "json":
        return {
            "rows": rows,
            "metadata": {
                "total_encounters": len(rows),
                "total_columns": len(rows[0]),
                "motor_columns": MOTOR_COLUMNS,
                "status_filter": status_filter,
                "anonymization": "SHA-256 deterministic (patient_id consistent across exports)",
                "outcome_fields_note": (
                    "outcome_* fields are NULL for encounters not yet finalized "
                    "or finalized without outcome data — standard for T0 encounters."
                ),
            },
        }

    # ── CSV streaming response ─────────────────────────────────────────────
    import csv
    import io
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0].keys()),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    filename = f"integrum_research_{len(rows)}enc_{status_filter}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Legacy endpoints (preserved for backward compatibility)
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/anonymized")
async def export_anonymized_data(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR])
    ),
):
    """
    Anonymized nested JSON export (legacy format).
    For flat CSV suitable for direct analysis, use GET /export/research/flat instead.
    """
    check_export_rate_limit(current_user.id)
    patients_stmt = select(Patient)
    patients_result = await db.execute(patients_stmt)
    patients = patients_result.scalars().all()

    export_data: Dict[str, Any] = {
        "patients": [],
        "encounters": [],
        "adjudication_logs": [],
        "metadata": {
            "total_patients": len(patients),
            "preferred_endpoint": "GET /export/research/flat — flat CSV, one row per encounter",
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
        export_data["patients"].append(
            {"patient_id": _anonymize_id(patient.id), "gender": patient.gender}
        )

        enc_stmt = select(EncounterModel).where(EncounterModel.patient_id == patient.id)
        enc_result = await db.execute(enc_stmt)
        for enc in enc_result.scalars().all():
            export_data["encounters"].append(
                {
                    "encounter_id": _anonymize_id(enc.id),
                    "patient_id": _anonymize_id(enc.patient_id),
                    "status": enc.status,
                    "phenotype_result": enc.phenotype_result,
                    "agreement_rate": enc.agreement_rate,
                    "outcome_status": enc.outcome_status,
                    "outcome_weight_current_kg": enc.weight_current_kg,
                    "outcome_adherence_reported": enc.adherence_reported,
                    "created_at": enc.created_at.isoformat()
                    if enc.created_at
                    else None,
                }
            )

            log_stmt = select(AdjudicationLog).where(
                AdjudicationLog.encounter_id == enc.id
            )
            log_result = await db.execute(log_stmt)
            for log in log_result.scalars().all():
                export_data["adjudication_logs"].append(
                    {
                        "encounter_id": _anonymize_id(log.encounter_id),
                        "engine_name": log.engine_name,
                        "calculated_value": log.calculated_value,
                        "confidence": log.confidence,
                        "is_overridden": log.is_overridden,
                        "override_reason": log.override_reason,
                    }
                )

    return export_data


@router.get("/patient/{patient_id}")
async def export_single_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """Export a single patient's full record (data portability — Ley 1581 Art. 8)."""
    pat_stmt = select(Patient).where(Patient.id == patient_id)
    pat_result = await db.execute(pat_stmt)
    patient = pat_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    enc_stmt = select(EncounterModel).where(EncounterModel.patient_id == patient_id)
    enc_result = await db.execute(enc_stmt)
    encounters = enc_result.scalars().all()

    export_data: Dict[str, Any] = {
        "patient": {
            "id": patient.id,
            "external_id": patient.external_id,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone,
        },
        "encounters": [],
    }

    for enc in encounters:
        log_stmt = select(AdjudicationLog).where(AdjudicationLog.encounter_id == enc.id)
        log_result = await db.execute(log_stmt)
        export_data["encounters"].append(
            {
                "id": enc.id,
                "status": enc.status,
                "reason_for_visit": enc.reason_for_visit,
                "phenotype_result": enc.phenotype_result,
                "clinical_notes": enc.clinical_notes,
                "plan_of_action": enc.plan_of_action,
                "outcome_status": enc.outcome_status,
                "outcome_weight_current_kg": enc.weight_current_kg,
                "outcome_adverse_event": enc.adverse_event,
                "outcome_medication_changed": enc.medication_changed,
                "outcome_adherence_reported": enc.adherence_reported,
                "created_at": enc.created_at.isoformat() if enc.created_at else None,
                "adjudication_logs": [
                    {
                        "engine_name": log.engine_name,
                        "calculated_value": log.calculated_value,
                        "confidence": log.confidence,
                        "is_overridden": log.is_overridden,
                        "physician_value": log.physician_value,
                    }
                    for log in log_result.scalars().all()
                ],
            }
        )

    return export_data
