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

    # Extracción y persistencia de índices cardiometabólicos calculados
    from src.engines.domain import Observation
    index_mappings = {
        "CALC-TYG": domain_encounter.tyg_index,
        "CALC-TYG-BMI": domain_encounter.tyg_bmi,
        "CALC-HOMA-IR": domain_encounter.homa_ir,
        "CALC-METS-IR": domain_encounter.mets_ir,
        "CALC-VAI": domain_encounter.visceral_adiposity_index,
        "CALC-FIB4": domain_encounter.fib4,
        "CALC-AIP": domain_encounter.aip,
        "CALC-BRI": domain_encounter.body_roundness_index,
    }

    for code, value in index_mappings.items():
        if value is not None:
            domain_encounter.observations.append(
                Observation(
                    code=code,
                    value=str(value),
                    unit="Index",
                    category="Calculated"
                )
            )

    # Record timeline
    await timeline_service.record_encounter(
        db, patient_id, encounter_id, domain_encounter.observations
    )

    # Data Readiness (REMOVED: Dead Code)
    readiness_report = {}

    # Run engines (has per-motor try/except internally)
    try:
        results = create_runner().run_all(domain_encounter)

        # 4.1 Build Typed Decision Context
        from src.engines.domain import DecisionContext
        
        ctx = DecisionContext()
        
        # Source: ClinicalPhenotypeEngine (Axis A)
        if "ATaxonomyMotor" in results:
            a_res = results["ATaxonomyMotor"]
            ctx.axis_a_code = a_res.metadata.get("code")
            a_label = str(a_res.calculated_value)
            # Derivation: 'A3' or explicit 'Lenta' keyword marks slow burn
            ctx.is_slow_burn = ctx.axis_a_code == "A3" or "Lenta" in a_label
            # Derivation: explicit 'Sarcopenia' keyword marks sarcopenic risk
            ctx.has_sarcopenic_risk = "Sarcopenia" in a_label
            
        # Source: BehavioralDomainEngine (Axis B)
        if "BDomainScoresMotor" in results:
            b_res = results["BDomainScoresMotor"]
            b_domains = b_res.metadata.get("domain_scores", [])
            for ds in b_domains:
                code = ds.get("code")
                comp = ds.get("completeness_status")
                # Derivation: 'complete' state means threshold crossed and confirmed
                if code == "B_UNCONTROLLED" and comp == "complete":
                    ctx.has_uncontrolled_eating = True
                elif code == "B_EMOTIONAL" and comp == "complete":
                    ctx.has_emotional_eating = True
                elif code == "B_AFFECT" and comp == "partial":
                    ctx.has_affective_traits = True
                elif code == "B_SLEEP" and comp == "complete":
                    ctx.has_clinical_insomnia = True

        # Source: LongitudinalTrajectoryEngine (Axis C)
        if "CStateMachineMotor" in results:
            c_res = results["CStateMachineMotor"]
            ctx.axis_c_code = "C2" if "C2" in str(c_res.calculated_value) else "C0"
            c_label = str(c_res.calculated_value)
            ctx.has_suboptimal_c = "C2" in c_label or "NON_RESPONDER" in c_label or "SUBOPTIMAL" in c_label

        # External Constraints & Context (Mocked placeholders for now)
        # Source: Medical History / Labs (Not yet implemented, default to False)
        ctx.has_advanced_ckd = False
        ctx.has_malnutrition_risk = False
        ctx.has_active_behavioral_referral = False

        # 4.2 Run Core Decisions
        from src.engines.core_decisions import CoreClinicalDecisionEngine
        core_engine = CoreClinicalDecisionEngine()
        core_result = core_engine.compute_from_context(domain_encounter, ctx)
        results[core_engine.__class__.__name__] = core_result


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
    # Add Core Engine manually to the map since it's not in the primary runner
    from src.engines.core_decisions import CoreClinicalDecisionEngine
    engines_map["CoreClinicalDecisionEngine"] = CoreClinicalDecisionEngine()

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

    # 3.5 Inject active chronic conditions
    from src.models.encounter import PatientConditionModel, ConditionStatus
    from src.engines.domain import Condition
    
    cond_stmt = select(PatientConditionModel).where(
        PatientConditionModel.patient_id == patient.id,
        PatientConditionModel.status == ConditionStatus.ACTIVE
    )
    cond_res = await db.execute(cond_stmt)
    active_conditions = cond_res.scalars().all()
    
    for ac in active_conditions:
        # Avoid duplicates if the payload also sent it
        if not domain_encounter.has_condition(ac.code):
            domain_encounter.conditions.append(
                Condition(code=ac.code, title=ac.title, system=ac.system)
            )

    # 3.6 Extract longitudinal history (last 90 days) for Axis C (C_state)
    from src.models.encounter import EncounterModel, ObservationModel
    from src.domain.models import LongitudinalEncounterEntry
    from datetime import timedelta
    from sqlalchemy.orm import selectinload
    
    ninety_days_ago = new_encounter.created_at - timedelta(days=90)
    
    stmt_history = (
        select(EncounterModel)
        .options(selectinload(EncounterModel.observations))
        .where(EncounterModel.patient_id == patient.id)
        .order_by(EncounterModel.created_at.desc())
        .limit(20)
    )
    res_hist = await db.execute(stmt_history)
    past_encounters = res_hist.scalars().all()
    
    valid_encounters = []
    found_older = False
    for enc in past_encounters:
        if enc.id == encounter_id:
            continue
        if enc.created_at >= ninety_days_ago:
            valid_encounters.append(enc)
        elif not found_older:
            valid_encounters.append(enc)
            found_older = True
            
    # Add current encounter
    valid_encounters.insert(0, new_encounter)
    
    history_entries = []
    for enc in valid_encounters:
        weight = enc.weight_current_kg
        ffm = None
        for obs in getattr(enc, 'observations', []):
            if obs.code in ["W-001", "29463-7"] and weight is None:
                try: weight = float(obs.value)
                except: pass
            elif obs.code in ["BIA-FFM-KG", "BIA-LEAN-KG"]:
                try: ffm = float(obs.value)
                except: pass
        
        # Pull from payload for current encounter
        if enc.id == encounter_id and payload.biometrics:
            weight = weight or payload.biometrics.weight_kg
            ffm = ffm or payload.biometrics.lean_mass_kg
            
        history_entries.append(LongitudinalEncounterEntry(
            encounter_id=enc.id,
            encounter_date=enc.created_at,
            weight_kg=weight,
            ffm_kg=ffm,
            adherence_self_report=enc.adherence_self_report if hasattr(enc, 'adherence_self_report') else None
        ))
        
    domain_encounter.longitudinal_encounters = history_entries


    # 4. Run clinical pipeline
    results, persistent_results, readiness_report = await run_clinical_pipeline(
        db, domain_encounter, encounter_id, patient.id
    )

    # 5. Persist results
    new_encounter.phenotype_result = persistent_results
    new_encounter.status = "ANALYZED"

    # 5.1 Populate derived classifications (A-B-C-E)
    from src.models.encounter import DerivedClassification, AxisType, CompletenessStatus
    import re

    axis_mappings = {
        "ATaxonomyMotor": AxisType.A,
        "PsychometabolicAxisMotor": AxisType.B,
        "BDomainScoresMotor": AxisType.B,
        "CMDSStagingMotor": AxisType.E,
        "CStateMachineMotor": AxisType.C,
    }

    for engine_name, axis in axis_mappings.items():
        if engine_name in persistent_results:
            res_dict = persistent_results[engine_name]
            
            if engine_name == "BDomainScoresMotor":
                domain_scores = res_dict.get("metadata", {}).get("domain_scores", [])
                for ds in domain_scores:
                    db.add(DerivedClassification(
                        patient_id=patient.id,
                        encounter_id=encounter_id,
                        axis=AxisType.B,
                        code=ds["code"],
                        label=ds["label"],
                        source_engine=engine_name,
                        rule_version_semantic="B_domains_v0.1",
                        engine_hash=res_dict.get("integrity_hash") or "UNKNOWN",
                        completeness_status=CompletenessStatus(ds["completeness_status"])
                    ))
                continue

            label = res_dict.get("calculated_value") or "Unknown"

            # Map completeness status
            estado_ui = res_dict.get("estado_ui")
            metadata = res_dict.get("metadata", {})
            completeness_meta = metadata.get("completeness_status")
            
            if completeness_meta == "complete":
                completeness = CompletenessStatus.COMPLETE
            elif completeness_meta == "partial":
                completeness = CompletenessStatus.PARTIAL
            elif completeness_meta == "indeterminate":
                completeness = CompletenessStatus.INDETERMINATE
            else:
                if estado_ui == "CONFIRMED_ACTIVE":
                    completeness = CompletenessStatus.COMPLETE
                elif estado_ui == "PROBABLE_WARNING":
                    completeness = CompletenessStatus.PARTIAL
                else:
                    completeness = CompletenessStatus.INDETERMINATE

            # Map axis code (string like A1, E3, etc.)
            code = str(axis.value)  # Fallback to "A", "B", etc.
            if axis == AxisType.E:
                match = re.search(r"Stage\s+(\d+)", label)
                if match:
                    code = f"E{match.group(1)}"
            elif axis == AxisType.A:
                code = metadata.get("code", "A0")
            elif axis == AxisType.B:
                # B phenotypes: Depresión Inflamatoria -> B1, Hiperfagia Ansiogénica -> B2, etc.
                if "Depresión Inflamatoria" in label:
                    code = "B1"
                elif "Hiperfagia Ansiogénica" in label:
                    code = "B2"
                elif "Déficit Hedónico" in label:
                    code = "B3"
            elif axis == AxisType.C:
                if "C1_RESPONDER_SAFE" in label:
                    code = "C1"
                elif "C2_NON_RESPONDER" in label:
                    code = "C2"
                elif "C3_RESPONDER_SARKOPENIC_RISK" in label:
                    code = "C3"
                else:
                    code = "C0"

            rule_version = "ABCE_v0.1"
            if axis == AxisType.E:
                rule_version = "EOSS_legacy_placeholder"
            elif axis == AxisType.A:
                rule_version = "A_taxonomy_v0.1"
            elif axis == AxisType.C:
                rule_version = "C_trajectory_v0.2"


            derived_clf = DerivedClassification(
                patient_id=patient.id,
                encounter_id=encounter_id,
                axis=axis,
                code=code,
                label=label[:255] if label else "Unknown",
                source_engine=engine_name,
                rule_version_semantic=rule_version,
                engine_hash=res_dict.get("integrity_hash") or "UNKNOWN",
                completeness_status=completeness,
            )
            db.add(derived_clf)

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

