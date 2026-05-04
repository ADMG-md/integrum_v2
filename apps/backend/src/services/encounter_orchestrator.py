"""
Encounter Orchestrator — handles the full clinical encounter pipeline.

Extracted from the monolithic encounter endpoint to follow Clean Architecture.
Responsibilities:
- Patient lookup with blind index
- Consent validation
- Domain model construction
- Clinical enrichment
- Motor execution
- Audit logging
- Result persistence

This service is async and DB-aware (unlike pure engines).
"""

from datetime import date as pydate
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.domain import (
    Encounter,
    Observation,
    Condition,
    MedicationStatement,
    ClinicalHistory,
    TraumaHistory,
    DrugEntry,
)
from src.engines.specialty_runner import create_runner, PRIMARY_MOTORS
from src.services.clinical_engine_service import clinical_bridge
from src.services.observation_mapper import build_flat_observations
from src.domain.models import DemographicsSchema, MetabolicPanelSchema
from src.schemas.encounter import EncounterCreate
from src.models.encounter import Patient, EncounterModel
from src.models.consent import PatientConsent
from src.services.timeline_service import timeline_service
from src.services.vault_service import vault_service
from src.services.audit_service import audit_service
from src.services.report_service import report_service

import structlog
import uuid

logger = structlog.get_logger()

DEFAULT_CLINICAL_AGE = 40


async def lookup_patient(db: AsyncSession, patient_id: str) -> Patient:
    """Look up patient by ID or blind index hash."""
    search_hash = vault_service.generate_blind_index(patient_id)
    stmt = select(Patient).where(
        (Patient.id == patient_id) | (Patient.external_id_hash == search_hash)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404, detail="Patient not found. Register them first."
        )
    return patient


async def verify_consent(db: AsyncSession, patient: Patient) -> None:
    """Verify legal consent exists for SaMD processing."""
    consent_stmt = (
        select(PatientConsent)
        .where(PatientConsent.patient_id == patient.id)
        .where(PatientConsent.is_granted == True)
        .order_by(PatientConsent.created_at.desc())
        .limit(1)
    )
    consent_res = await db.execute(consent_stmt)
    if not consent_res.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="Legal Consent missing or revoked for this patient. Cannot process SaMD clinical data.",
        )


def calculate_age(patient: Patient) -> int:
    """Calculate patient age from DOB, fallback to DEFAULT_CLINICAL_AGE."""
    if patient.date_of_birth:
        try:
            if isinstance(patient.date_of_birth, str):
                dob = pydate.fromisoformat(patient.date_of_birth[:10])
            else:
                dob = (
                    patient.date_of_birth.date()
                    if hasattr(patient.date_of_birth, "date")
                    else patient.date_of_birth
                )
            return (pydate.today() - dob).days // 365
        except Exception:
            pass
    return DEFAULT_CLINICAL_AGE


def build_domain_encounter(
    encounter_id: str,
    payload: EncounterCreate,
    patient: Patient,
    age: int,
) -> Encounter:
    """Build the enriched domain Encounter model from payload and patient data."""
    flat_observations = build_flat_observations(payload, patient.gender)

    demographics = DemographicsSchema(age_years=age, gender=patient.gender)

    domain_encounter = Encounter(
        id=encounter_id,
        demographics=demographics,
        metabolic_panel=payload.metabolic or MetabolicPanelSchema(),
        conditions=[Condition(**c.model_dump()) for c in payload.conditions],
        observations=[
            o if isinstance(o, Observation) else Observation(**o.model_dump())
            for o in flat_observations
        ],
        medications=[
            MedicationStatement(
                code=m.code or "CUSTOM", name=m.name, is_active=(m.status == "active")
            )
            for m in payload.medications
        ],
        history=payload.history,
        reason_for_visit=payload.reason_for_visit,
        personal_history=payload.personal_history,
        family_history=payload.family_history,
        metadata={
            "sex": patient.gender,
            "age": age,
            "patient_id": str(patient.id),
        },
    )

    # Ensure Age is also an observation for engines that look for codes
    domain_encounter.observations.append(
        Observation(code="AGE-001", value=age, unit="yrs")
    )

    return domain_encounter


async def create_encounter_record(
    db: AsyncSession,
    encounter_id: str,
    payload: EncounterCreate,
    patient: Patient,
    tenant_id: str,
) -> EncounterModel:
    """Create and persist the EncounterModel record."""
    new_encounter = EncounterModel(
        id=encounter_id,
        patient_id=patient.id,
        tenant_id=tenant_id,
        reason_for_visit=payload.reason_for_visit,
        personal_history=payload.personal_history,
        family_history=payload.family_history,
    )
    db.add(new_encounter)
    await db.flush()

    if payload.history:
        new_encounter.clinical_notes = f"History: {payload.history.model_dump_json()}"

    return new_encounter


async def run_clinical_pipeline(
    db: AsyncSession,
    domain_encounter: Encounter,
    encounter_id: str,
    patient_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Run the full clinical engine pipeline:
    1. Clinical intelligence enrichment
    2. Timeline recording
    3. Data readiness scoring
    4. Motor execution
    5. Audit logging

    Returns: (results, persistent_results, readiness_report)
    """
    # Clinical Intelligence Pulse
    domain_encounter = clinical_bridge.enrich(domain_encounter)

    # Record timeline
    await timeline_service.record_encounter(
        db, patient_id, encounter_id, domain_encounter.observations
    )

    # Data Readiness (REMOVED: Dead Code)
    readiness_report = {}

    # Run engines (has per-motor try/except internally)
    try:
        results = create_runner().run_all(domain_encounter)
    except Exception as e:
        import logging

        logging.getLogger("integrum.encounter").error(
            f"create_runner().run_all() critical failure for encounter {encounter_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Clinical engine pipeline failed for encounter {encounter_id}. "
                f"The encounter was saved but motor results are unavailable. "
                f"Error: {str(e)}"
            ),
        )

    # Audit Trail
    engines_map = {m.__class__.__name__: m for m in create_runner().get_all_motors()}
    audit_results = await audit_service.log_adjudications(
        db, encounter_id, results, engines_map
    )

    # Build persistent results with audit metadata
    persistent_results = {name: res.model_dump() for name, res in results.items()}
    for name, meta in audit_results.items():
        if name in persistent_results:
            persistent_results[name]["log_id"] = meta["log_id"]
            persistent_results[name]["integrity_hash"] = meta["integrity_hash"]

    return results, persistent_results, readiness_report


async def process_encounter(
    db: AsyncSession,
    payload: EncounterCreate,
    current_user,
    generate_report: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point: process a clinical encounter end-to-end.

    This replaces the 600+ line process_encounter_t0 endpoint.
    """
    encounter_id = str(uuid.uuid4())

    # 1. Lookup & consent
    patient = await lookup_patient(db, payload.patient_id)
    await verify_consent(db, patient)

    # 2. Create encounter record
    new_encounter = await create_encounter_record(
        db, encounter_id, payload, patient, current_user.tenant_id
    )

    # 3. Build domain model
    age = calculate_age(patient)
    domain_encounter = build_domain_encounter(encounter_id, payload, patient, age)

    # 4. Run clinical pipeline
    results, persistent_results, readiness_report = await run_clinical_pipeline(
        db, domain_encounter, encounter_id, patient.id
    )

    # 5. Persist results
    new_encounter.phenotype_result = persistent_results
    new_encounter.status = "ANALYZED"
    await db.commit()

    # 6. Return
    if generate_report:
        report = report_service.generate_report(results, domain_encounter, encounter_id)
        report["data_readiness"] = readiness_report
        return report

    return {
        "encounter_id": encounter_id,
        "results": persistent_results,
        "data_readiness": readiness_report,
    }


async def finalize_encounter_logic(
    db: AsyncSession,
    encounter_id: str,
    payload,  # EncounterFinalizeSchema
    current_user,
) -> Dict[str, Any]:
    """
    DT-01: Business logic for finalizing a clinical encounter.

    Extracted from the HTTP endpoint to follow Clean Architecture.
    Responsibilities:
    - Tenant isolation check
    - MinCiencias audit compliance (version hash + confidence validation)
    - Agreement rate calculation
    - Outcome field persistence
    - Encounter status transition → FINALIZED
    """
    from src.models.encounter import EncounterModel
    from src.models.audit import DecisionAuditLog, DecisionType, ReasonCode

    stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # Tenant isolation: a physician can only finalize their own tenant's encounters
    if encounter.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: encounter belongs to a different tenant.",
        )

    original_results = encounter.phenotype_result or {}
    total_audits = len(payload.audit_payload) if payload.audit_payload else 0
    agreements_count = 0

    if not payload.audit_payload and len(original_results) > 0:
        raise HTTPException(
            status_code=400,
            detail="AUDIT_REQUIRED: All AI interpretations must be audited before finalization.",
        )

    if payload.audit_payload:
        for audit in payload.audit_payload:
            eng_name = audit["engine_name"]
            req_decision = audit["decision_type"]
            req_hash = audit.get("engine_version_hash")

            # Validation 1: Version Hash Mismatch (integrity guard)
            orig_hash = (
                original_results.get(eng_name, {}).get("integrity_hash") or "UNKNOWN"
            )
            if req_hash != orig_hash:
                raise HTTPException(
                    status_code=409,
                    detail=f"Version mismatch for {eng_name}. UI sent {req_hash}, DB expects {orig_hash}.",
                )

            # Validation 2: Cannot blindly AGREE on low-confidence or locked insights
            orig_confidence = original_results.get(eng_name, {}).get("confidence", 1.0)
            estado_ui = original_results.get(eng_name, {}).get("estado_ui", "ANALYZED")

            if req_decision == "AGREEMENT" and (
                estado_ui == "INDETERMINATE_LOCKED" or orig_confidence < 0.65
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Integrity Violation: Cannot blindly validate '{eng_name}' "
                        f"(Confidence: {orig_confidence}). Requires manual Override."
                    ),
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

    # Agreement rate (MinCiencias compliance metric)
    if total_audits > 0:
        encounter.agreement_rate = round((agreements_count / total_audits) * 100, 2)

    encounter.status = "FINALIZED"
    encounter.clinical_notes = payload.clinical_notes
    encounter.plan_of_action = payload.plan_of_action
    encounter.physician_id = current_user.id

    # Outcome tracking (research dataset quality)
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

    logger.info(
        "encounter_finalized",
        encounter_id=encounter_id,
        physician_id=current_user.id,
        agreement_rate=encounter.agreement_rate,
    )
    return {"status": "finalized", "encounter_id": encounter_id}

