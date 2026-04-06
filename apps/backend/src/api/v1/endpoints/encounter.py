from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.schemas.encounter import (
    EncounterCreate,
    AdjudicationResultSchema,
    EncounterFinalizeSchema,
    EncounterRead,
)
from src.schemas.report import ClinicalReportSchema
from src.engines.domain import (
    Encounter,
    Observation,
    Condition,
    MedicationStatement,
    AdjudicationResult,
)
from src.engines.specialty_runner import specialty_runner
from src.engines.specialty.readiness import readiness_engine
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.eoss import EOSSStagingMotor
from src.services.report_service import report_service
from src.services.audit_service import audit_service
from src.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Union, Optional
import uuid

from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel
import structlog

logger = structlog.get_logger()

router = APIRouter()

from src.schemas.encounter import (
    EncounterCreate,
    AdjudicationResultSchema,
    EncounterFinalizeSchema,
    EncounterRead,
    ProcessResponseSchema,
)


# ... existing imports ...
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
    # 1. Map Schema to Domain Models
    encounter_id = str(uuid.uuid4())

    # Mission 12: Real Workflow Persistence
    from src.models.encounter import Patient, EncounterModel
    from src.services.timeline_service import timeline_service
    from src.services.vault_service import vault_service

    # MISSION 12: Use Blind Index (Hash) for deterministic search
    search_hash = vault_service.generate_blind_index(payload.patient_id)

    stmt = select(Patient).where(
        (Patient.id == payload.patient_id) | (Patient.external_id_hash == search_hash)
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404, detail="Patient not found. Register them first."
        )

    # Mission 12: Legal Consent Guard (SaMD Compliance)
    from src.models.consent import PatientConsent

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

    # Save modern encounter record with reference to real patient
    new_encounter = EncounterModel(
        id=encounter_id,
        patient_id=patient.id,
        tenant_id=current_user.tenant_id,
        reason_for_visit=payload.reason_for_visit,
        personal_history=payload.personal_history,
        family_history=payload.family_history,
    )
    db.add(new_encounter)
    await db.flush()

    # Mission 13: Flatten Hierarchical data into Domain Observations for Engine processing
    flat_observations = list(payload.observations)

    if payload.biometrics:
        b = payload.biometrics
        flat_observations.append(
            Observation(code="29463-7", value=b.weight_kg, unit="kg")
        )
        flat_observations.append(
            Observation(code="8302-2", value=b.height_cm, unit="cm")
        )
        if b.waist_cm:
            flat_observations.append(
                Observation(code="WAIST-001", value=b.waist_cm, unit="cm")
            )
        if b.hip_cm:
            flat_observations.append(
                Observation(code="HIP-001", value=b.hip_cm, unit="cm")
            )
        if b.neck_cm:
            flat_observations.append(
                Observation(code="NECK-001", value=b.neck_cm, unit="cm")
            )
        if b.systolic_bp:
            flat_observations.append(
                Observation(code="8480-6", value=b.systolic_bp, unit="mmHg")
            )
        if b.diastolic_bp:
            flat_observations.append(
                Observation(code="8462-4", value=b.diastolic_bp, unit="mmHg")
            )
        if b.arm_circumference_cm:
            flat_observations.append(
                Observation(code="ARM-CIRC", value=b.arm_circumference_cm, unit="cm")
            )
        if b.calf_circumference_cm:
            flat_observations.append(
                Observation(code="CALF-CIRC", value=b.calf_circumference_cm, unit="cm")
            )
        # BIA observations for Sarcopenia and Metabolic engines
        if b.muscle_mass_kg:
            flat_observations.append(
                Observation(
                    code="MMA-001", value=b.muscle_mass_kg, unit="kg", category="BIA"
                )
            )
            flat_observations.append(
                Observation(
                    code="MUSCLE-KG", value=b.muscle_mass_kg, unit="kg", category="BIA"
                )
            )
            flat_observations.append(
                Observation(
                    code="BIA-MUSCLE-KG",
                    value=b.muscle_mass_kg,
                    unit="kg",
                    category="BIA",
                )
            )
        if b.skeletal_muscle_index:
            flat_observations.append(
                Observation(
                    code="SMI-001",
                    value=b.skeletal_muscle_index,
                    unit="kg/m2",
                    category="BIA",
                )
            )
        if b.body_fat_percent:
            flat_observations.append(
                Observation(
                    code="BIA-FAT-PCT",
                    value=b.body_fat_percent,
                    unit="%",
                    category="BIA",
                )
            )
        if b.fat_mass_kg:
            flat_observations.append(
                Observation(
                    code="BIA-FAT-KG", value=b.fat_mass_kg, unit="kg", category="BIA"
                )
            )
        if b.lean_mass_kg:
            flat_observations.append(
                Observation(
                    code="BIA-LEAN-KG", value=b.lean_mass_kg, unit="kg", category="BIA"
                )
            )
        if b.visceral_fat_area_cm2:
            flat_observations.append(
                Observation(
                    code="BIA-VISCERAL",
                    value=b.visceral_fat_area_cm2,
                    unit="cm2",
                    category="BIA",
                )
            )
        if b.visceral_fat_level:
            flat_observations.append(
                Observation(
                    code="BIA-VISCERAL-LVL",
                    value=b.visceral_fat_level,
                    unit="level",
                    category="BIA",
                )
            )
        if b.basal_metabolic_rate:
            flat_observations.append(
                Observation(
                    code="BIA-BMR",
                    value=b.basal_metabolic_rate,
                    unit="kcal",
                    category="BIA",
                )
            )
        if b.total_body_water_percent:
            flat_observations.append(
                Observation(
                    code="BIA-TBW",
                    value=b.total_body_water_percent,
                    unit="%",
                    category="BIA",
                )
            )
        if b.bone_mass_kg:
            flat_observations.append(
                Observation(
                    code="BIA-BONE", value=b.bone_mass_kg, unit="kg", category="BIA"
                )
            )

    if payload.metabolic:
        m = payload.metabolic
        # Glucose/Insulin
        if m.glucose_mg_dl:
            flat_observations.append(
                Observation(code="2339-0", value=m.glucose_mg_dl, unit="mg/dL")
            )
        if m.hba1c_percent:
            flat_observations.append(
                Observation(code="4548-4", value=m.hba1c_percent, unit="%")
            )
        if m.insulin_mu_u_ml:
            flat_observations.append(
                Observation(code="20448-7", value=m.insulin_mu_u_ml, unit="muU/mL")
            )
        if m.c_peptide_ng_ml:
            flat_observations.append(
                Observation(code="C-PEP-001", value=m.c_peptide_ng_ml, unit="ng/mL")
            )
        if m.gada_antibodies:
            flat_observations.append(
                Observation(
                    code="GADA-001", value=m.gada_antibodies, category="Autoimmune"
                )
            )
        # Renal
        if m.creatinine_mg_dl:
            flat_observations.append(
                Observation(code="2160-0", value=m.creatinine_mg_dl, unit="mg/dL")
            )
        if m.uric_acid_mg_dl:
            flat_observations.append(
                Observation(code="UA-001", value=m.uric_acid_mg_dl, unit="mg/dL")
            )
        # Liver
        if m.ast_u_l:
            flat_observations.append(
                Observation(code="29230-0", value=m.ast_u_l, unit="U/L")
            )
        if m.alt_u_l:
            flat_observations.append(
                Observation(code="22538-3", value=m.alt_u_l, unit="U/L")
            )
        if m.ggt_u_l:
            flat_observations.append(
                Observation(code="GGT-001", value=m.ggt_u_l, unit="U/L")
            )
        if m.alkaline_phosphatase_u_l:
            flat_observations.append(
                Observation(
                    code="ALKPHOS-001", value=m.alkaline_phosphatase_u_l, unit="U/L"
                )
            )
        # CBC
        if m.wbc_k_ul:
            flat_observations.append(
                Observation(code="WBC-001", value=m.wbc_k_ul, unit="k/uL")
            )
        if m.lymphocyte_percent:
            flat_observations.append(
                Observation(code="26474-7", value=m.lymphocyte_percent, unit="%")
            )
        if m.neutrophil_percent:
            flat_observations.append(
                Observation(code="26499-4", value=m.neutrophil_percent, unit="%")
            )
        if m.mcv_fl:
            flat_observations.append(
                Observation(code="MCV-001", value=m.mcv_fl, unit="fL")
            )
        if m.rdw_percent:
            flat_observations.append(
                Observation(code="RDW-001", value=m.rdw_percent, unit="%")
            )
        if m.platelets_k_u_l:
            flat_observations.append(
                Observation(code="PLT-001", value=m.platelets_k_u_l, unit="k/uL")
            )
        # Inflammation/Iron
        if m.hs_crp_mg_l:
            flat_observations.append(
                Observation(code="30522-7", value=m.hs_crp_mg_l, unit="mg/L")
            )
        if m.ferritin_ng_ml:
            flat_observations.append(
                Observation(code="FER-001", value=m.ferritin_ng_ml, unit="ng/mL")
            )
        if m.albumin_g_dl:
            flat_observations.append(
                Observation(code="ALB-001", value=m.albumin_g_dl, unit="g/dL")
            )
        # Thyroid
        if m.tsh_u_iu_ml:
            flat_observations.append(
                Observation(code="11579-0", value=m.tsh_u_iu_ml, unit="uIU/mL")
            )
        if m.ft4_ng_dl:
            flat_observations.append(
                Observation(code="FT4-001", value=m.ft4_ng_dl, unit="ng/dL")
            )
        if m.ft3_pg_ml:
            flat_observations.append(
                Observation(code="FT3-001", value=m.ft3_pg_ml, unit="pg/mL")
            )
        if m.rt3_ng_dl:
            flat_observations.append(
                Observation(code="RT3-001", value=m.rt3_ng_dl, unit="ng/dL")
            )
        if m.shbg_nmol_l:
            flat_observations.append(
                Observation(code="SHBG-001", value=m.shbg_nmol_l, unit="nmol/L")
            )
        if m.cortisol_am_mcg_dl:
            flat_observations.append(
                Observation(code="CORT-AM", value=m.cortisol_am_mcg_dl, unit="mcg/dL")
            )
        if m.aldosterone_ng_dl:
            flat_observations.append(
                Observation(code="ALDO-001", value=m.aldosterone_ng_dl, unit="ng/dL")
            )
        if m.renin_ng_ml_h:
            flat_observations.append(
                Observation(code="RENIN-001", value=m.renin_ng_ml_h, unit="ng/mL/h")
            )
        # Lipids
        if m.total_cholesterol_mg_dl:
            flat_observations.append(
                Observation(
                    code="2093-3", value=m.total_cholesterol_mg_dl, unit="mg/dL"
                )
            )
        if m.ldl_mg_dl:
            flat_observations.append(
                Observation(code="13457-7", value=m.ldl_mg_dl, unit="mg/dL")
            )
        if m.hdl_mg_dl:
            flat_observations.append(
                Observation(code="2085-9", value=m.hdl_mg_dl, unit="mg/dL")
            )
        if m.triglycerides_mg_dl:
            flat_observations.append(
                Observation(code="2571-8", value=m.triglycerides_mg_dl, unit="mg/dL")
            )
        if m.vldl_mg_dl:
            flat_observations.append(
                Observation(code="VLDL-001", value=m.vldl_mg_dl, unit="mg/dL")
            )
        if m.apob_mg_dl:
            flat_observations.append(
                Observation(code="APOB-001", value=m.apob_mg_dl, unit="mg/dL")
            )
        if m.lpa_mg_dl:
            flat_observations.append(
                Observation(code="LPA-001", value=m.lpa_mg_dl, unit="mg/dL")
            )
        if m.apoa1_mg_dl:
            flat_observations.append(
                Observation(code="APOA1-001", value=m.apoa1_mg_dl, unit="mg/dL")
            )

    if payload.psychometrics:
        p = payload.psychometrics
        if p.phq9_score is not None:
            flat_observations.append(
                Observation(code="PHQ-9", value=p.phq9_score, category="Psychometry")
            )
        if p.gad7_score is not None:
            flat_observations.append(
                Observation(code="GAD-7", value=p.gad7_score, category="Psychometry")
            )
        if p.atenas_insomnia_score is not None:
            flat_observations.append(
                Observation(
                    code="AIS-001",
                    value=p.atenas_insomnia_score,
                    category="Psychometry",
                )
            )
        if p.tfeq_emotional_eating is not None:
            flat_observations.append(
                Observation(
                    code="TFEQ-EMOTIONAL",
                    value=p.tfeq_emotional_eating,
                    category="Psychometry",
                )
            )
        if p.tfeq_uncontrolled_eating is not None:
            flat_observations.append(
                Observation(
                    code="TFEQ-UNCONTROLLED",
                    value=p.tfeq_uncontrolled_eating,
                    category="Psychometry",
                )
            )
        if p.tfeq_cognitive_restraint is not None:
            flat_observations.append(
                Observation(
                    code="TFEQ-COGNITIVE",
                    value=p.tfeq_cognitive_restraint,
                    category="Psychometry",
                )
            )

    if payload.lifestyle:
        l = payload.lifestyle
        if l.sleep_hours is not None:
            flat_observations.append(
                Observation(
                    code="LIFE-SLEEP",
                    value=l.sleep_hours,
                    unit="hours",
                    category="Lifestyle",
                )
            )
        if l.physical_activity_min_week is not None:
            flat_observations.append(
                Observation(
                    code="LIFE-EXERCISE",
                    value=l.physical_activity_min_week,
                    unit="min/week",
                    category="Lifestyle",
                )
            )
        if l.stress_level_vas is not None:
            flat_observations.append(
                Observation(
                    code="LIFE-STRESS",
                    value=l.stress_level_vas,
                    unit="1-10",
                    category="Lifestyle",
                )
            )

    from src.services.clinical_engine_service import clinical_bridge

    # MISSION 13: Enriched Domain Model
    from datetime import date as pydate

    age = 40  # Default if DOB missing
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
            age = (pydate.today() - dob).days // 365
        except Exception:
            age = 40

    # MISSION 13: Enriched Domain Model (V1 Parity)
    from src.engines.domain import ClinicalHistory, TraumaHistory, DrugEntry

    history_domain = None
    if payload.history:
        history_domain = ClinicalHistory(
            onset_trigger=payload.history.onset_trigger,
            age_of_onset=payload.history.age_of_onset,
            max_weight_ever_kg=payload.history.max_weight_ever_kg,
            current_medications=[
                DrugEntry(**m.model_dump()) for m in payload.history.current_medications
            ],
            previous_medications=[
                DrugEntry(**m.model_dump())
                for m in payload.history.previous_medications
            ],
            trauma=TraumaHistory(**payload.history.trauma.model_dump())
            if payload.history.trauma
            else None,
            has_type2_diabetes=payload.history.has_type2_diabetes,
            has_prediabetes=payload.history.has_prediabetes,
            has_hypertension=payload.history.has_hypertension,
            has_dyslipidemia=payload.history.has_dyslipidemia,
            has_nafld=payload.history.has_nafld,
            has_gout=payload.history.has_gout,
            has_hypothyroidism=payload.history.has_hypothyroidism,
            has_pcos=payload.history.has_pcos,
            has_osa=payload.history.has_osa,
            has_glaucoma=payload.history.has_glaucoma,
            has_seizures_history=payload.history.has_seizures_history,
            has_eating_disorder_history=payload.history.has_eating_disorder_history,
            family_history_thyroid_cancer=payload.history.family_history_thyroid_cancer,
            smoking_status=payload.history.smoking_status or "never",
            alcohol_intake=payload.history.alcohol_intake or "none",
        )

    from src.schemas.encounter import (
        DemographicsSchema,
        MetabolicPanelSchema,
        CardioPanelSchema,
    )

    demographics = DemographicsSchema(age_years=age, gender=patient.gender)

    metabolic = MetabolicPanelSchema()
    cardio = CardioPanelSchema()

    if payload.metabolic:
        # Optimized zero-mapping ingestion (SSOT compliant)
        m_data = payload.metabolic.model_dump(exclude_unset=True)
        metabolic = MetabolicPanelSchema(**m_data)
        cardio = CardioPanelSchema(**m_data)

    domain_encounter = Encounter(
        id=encounter_id,
        demographics=demographics,
        metabolic_panel=metabolic,
        cardio_panel=cardio,
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
        history=history_domain,
        reason_for_visit=payload.reason_for_visit,
        personal_history=payload.personal_history,
        family_history=payload.family_history,
        metadata={
            "sex": patient.gender,  # Maps to "M" or "F" expected by motors
            "age": age,
            "patient_id": str(patient.id),
        },
    )

    # MISSION 13: Ensure Age is also an observation for engines that look for codes
    domain_encounter.observations.append(
        Observation(code="AGE-001", value=age, unit="yrs")
    )

    # 1.5 Clinical Intelligence Pulse (Auto-Enrichment)
    domain_encounter = clinical_bridge.enrich(domain_encounter)

    if payload.history:
        new_encounter.clinical_notes = f"History: {payload.history.model_dump_json()}"

    await timeline_service.record_encounter(
        db, patient.id, encounter_id, domain_encounter.observations
    )

    # 4. ClinicalDataReadinessEngine — score data readiness before running motors
    readiness = readiness_engine.score(
        domain_encounter, specialty_runner.PRIMARY_MOTORS
    )
    readiness_report = readiness.to_dict()

    # 5. Run Unified Clinical Engines (Mission 2.2 Hardening)
    results = specialty_runner.run_all(domain_encounter)

    # 5. SaMD Audit Trail (Inmutable Logging)
    # Map engine instances for version/requirement tracking
    engines_map = {m.__class__.__name__: m for m in specialty_runner.get_all_motors()}

    audit_results = await audit_service.log_adjudications(
        db, encounter_id, results, engines_map
    )

    # 6. Persist Results (Mission 12 Hardening)
    persistent_results = {name: res.model_dump() for name, res in results.items()}

    # Inject Audit Metadata (Log ID + Integrity Hash) into persistent JSON
    for name, meta in audit_results.items():
        if name in persistent_results:
            persistent_results[name]["log_id"] = meta["log_id"]
            persistent_results[name]["integrity_hash"] = meta["integrity_hash"]

    new_encounter.phenotype_result = persistent_results
    new_encounter.status = "ANALYZED"
    await db.commit()

    # 6. Generate Full Report if requested
    if generate_report:
        report = report_service.generate_report(results, domain_encounter, encounter_id)
        report["data_readiness"] = readiness_report
        return report

    # 8. Return raw results (Fallback)
    return {
        "encounter_id": encounter_id,
        "results": persistent_results,
        "data_readiness": readiness_report,
    }


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

    # 7. Human-AI Interaction Audit (MinCiencias Compliance) & Integrity Validation
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

            # If all validations pass, schedule append (Atomic, bounds to db.commit() at the end)
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
                # Catches Enum constraint errors early
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

    # Return objects directly for Pydantic to serialize according to EncounterRead
    return encounters
