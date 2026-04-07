"""
FHIR R4 API Endpoint for Integrum V2.

Exposes Integrum V2 encounters as FHIR R4 Bundles, enabling interoperability
with external EHRs, research networks, and OMOP CDM systems.

Endpoints:
- GET /api/v1/fhir/encounter/{encounter_id} - Get encounter as FHIR Bundle
- GET /api/v1/fhir/patient/{patient_id}/encounters - Get all encounters for patient as Bundle
- POST /api/v1/fhir/encounter/{encounter_id}/$export - Export encounter to FHIR JSON file
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.models.encounter import EncounterModel, Patient
from src.fhir.bundle_generator import encounter_to_fhir_bundle

router = APIRouter(tags=["FHIR R4"])  # prefix="/fhir" applied in api.py include_router()


@router.get("/encounter/{encounter_id}")
async def get_encounter_as_fhir(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
    include_calculated: bool = Query(
        True, description="Include calculated indices (HOMA-IR, TyG, etc.)"
    ),
    include_motors: bool = Query(
        True, description="Include motor results as derived Observations"
    ),
):
    """
    Get a single encounter as a FHIR R4 Bundle.

    Returns a FHIR Bundle containing:
    - Patient resource
    - Encounter resource
    - Observation resources (vitals, labs, calculated indices)
    - Condition resources (diagnoses)
    - MedicationStatement resources (medications with ATC coding)
    - QuestionnaireResponse resources (psychometric assessments)

    This endpoint enables interoperability with:
    - HAPI FHIR servers
    - Epic/Cerner EHRs
    - OMOP-on-FHIR systems
    - Research networks using FHIR
    """
    # Get encounter from database
    stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=404, detail=f"Encounter {encounter_id} not found"
        )

    # Convert to FHIR Bundle
    # Note: Motor results would need to be fetched from adjudication_logs
    # For now, we pass None for results
    bundle = encounter_to_fhir_bundle(
        encounter,
        results=None,  # Would need to fetch from adjudication_logs
        include_calculated=include_calculated,
    )

    return bundle.to_dict()


@router.get("/patient/{patient_id}/encounters")
async def get_patient_encounters_as_fhir(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    include_calculated: bool = True,
):
    """
    Get all encounters for a patient as a FHIR Bundle.

    Returns a FHIR Bundle containing all encounters for the specified patient,
    each as a separate entry with full resources.
    """
    # Get patient
    patient_stmt = select(Patient).where(Patient.id == patient_id)
    patient_result = await db.execute(patient_stmt)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    # Get encounters
    enc_stmt = (
        select(EncounterModel)
        .where(EncounterModel.patient_id == patient_id)
        .order_by(EncounterModel.created_at.desc())
        .limit(limit)
    )
    enc_result = await db.execute(enc_stmt)
    encounters = enc_result.scalars().all()

    # Create bundle with all encounters
    from src.fhir.resources import (
        FHIRBundle,
        FHIRPatient,
        FHIREncounter,
        FHIRObservation,
        FHIRCondition,
        FHIRMedicationStatement,
    )

    bundle = FHIRBundle(
        id=f"patient-{patient_id}-encounters",
        type="collection",
    )

    # Add patient once
    fhir_patient = FHIRPatient(
        id=patient.id,
        identifier=[{"system": "urn:oid:integrum", "value": str(patient.id)}],
        gender=patient.gender,
        birthDate=str(patient.date_of_birth) if patient.date_of_birth else None,
    )
    bundle.add_resource(fhir_patient)

    # Add each encounter
    for enc in encounters:
        fhir_enc = FHIREncounter.from_encounter(enc)
        bundle.add_resource(fhir_enc)

        # Add observations
        for obs in enc.observations:
            fhir_obs = FHIRObservation.from_observation(obs, enc.id)
            bundle.add_resource(fhir_obs)

        # Add conditions
        for cond in enc.conditions:
            fhir_cond = FHIRCondition.from_condition(cond, enc.id)
            bundle.add_resource(fhir_cond)

        # Add medications
        for med in enc.medications:
            fhir_med = FHIRMedicationStatement.from_medication(med, enc.id)
            bundle.add_resource(fhir_med)

    return bundle.to_dict()


@router.get("/encounter/{encounter_id}/$export")
async def export_encounter_as_fhir_json(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Export encounter as downloadable FHIR JSON file.

    Returns the FHIR Bundle as a JSON file that can be imported into
    HAPI FHIR servers, research databases, or OMOP-on-FHIR systems.
    """
    from fastapi.responses import JSONResponse

    stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
    result = await db.execute(stmt)
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(
            status_code=404, detail=f"Encounter {encounter_id} not found"
        )

    bundle = encounter_to_fhir_bundle(encounter, results=None, include_calculated=True)

    return JSONResponse(
        content=bundle.to_dict(),
        headers={
            "Content-Disposition": f"attachment; filename=integrum-encounter-{encounter_id}-fhir.json",
            "Content-Type": "application/fhir+json",
        },
    )
