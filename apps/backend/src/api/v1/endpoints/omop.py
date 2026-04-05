"""
OMOP CDM API Endpoint for Integrum V2.

Exposes OMOP CDM 5.4 ETL capabilities via REST API:
- POST /api/v1/omop/encounter/{id}/etl - Generate OMOP SQL for encounter
- GET /api/v1/omop/cohorts - List available cohort definitions
- POST /api/v1/omop/cohorts/{name}/sql - Get SQL for a specific cohort
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any

from src.omop.etl import encounter_to_omop_sql
from src.omop.cohorts import (
    COHORT_DEFINITIONS,
    OUTCOME_DEFINITIONS,
    FEATURE_DEFINITIONS,
)
from src.omop.fhir_reverse import omop_to_fhir_bundle

router = APIRouter(prefix="/omop", tags=["OMOP CDM 5.4"])


@router.post("/encounter/{encounter_id}/etl")
async def generate_omop_etl_sql(
    encounter_id: str,
    person_id: int = Query(1, description="OMOP person_id"),
    visit_occurrence_id: int = Query(1, description="OMOP visit_occurrence_id"),
):
    """
    Generate OMOP CDM 5.4 SQL INSERT statements for an encounter.

    Returns SQL that can be executed against an OMOP CDM database to
    insert the encounter data into the appropriate CDM tables.

    This is a preview of the ETL — for production use, implement a proper
    ETL pipeline using WhiteRabbit/Rabbit-In-A-Hat.
    """
    # Note: This endpoint would need access to the database to fetch the encounter
    # For now, it returns a template showing the structure
    return {
        "encounter_id": encounter_id,
        "person_id": person_id,
        "visit_occurrence_id": visit_occurrence_id,
        "omop_version": "5.4",
        "tables": list(COHORT_DEFINITIONS.keys()),
        "note": "This is a preview endpoint. For production ETL, use WhiteRabbit/Rabbit-In-A-Hat.",
        "cohort_templates": {
            name: sql[:200] + "..." for name, sql in COHORT_DEFINITIONS.items()
        },
    }


@router.get("/cohorts")
async def list_omop_cohorts():
    """
    List all available OMOP cohort definitions.

    Returns cohort names and descriptions for use in OHDSI/HADES analysis.
    """
    cohorts = {}
    for name, sql in COHORT_DEFINITIONS.items():
        # Extract first comment as description
        lines = sql.strip().split("\n")
        description = ""
        for line in lines:
            if line.strip().startswith("--"):
                description = line.strip().replace("--", "").strip()
                break
        cohorts[name] = description

    outcomes = {}
    for name, sql in OUTCOME_DEFINITIONS.items():
        lines = sql.strip().split("\n")
        description = ""
        for line in lines:
            if line.strip().startswith("--"):
                description = line.strip().replace("--", "").strip()
                break
        outcomes[name] = description

    features = {}
    for name, sql in FEATURE_DEFINITIONS.items():
        lines = sql.strip().split("\n")
        description = ""
        for line in lines:
            if line.strip().startswith("--"):
                description = line.strip().replace("--", "").strip()
                break
        features[name] = description

    return {
        "cohorts": cohorts,
        "outcomes": outcomes,
        "features": features,
        "omop_version": "5.4",
    }


@router.get("/cohorts/{cohort_name}/sql")
async def get_cohort_sql(cohort_name: str):
    """
    Get the SQL for a specific OMOP cohort definition.

    Available cohorts:
    - obesity_bmi: Adults with BMI >= 30
    - t2dm: Type 2 Diabetes Mellitus
    - obesity_t2dm: Obesity + T2DM
    - metabolic_syndrome: Metabolic Syndrome (ATP III)
    - nafld: NAFLD/MASLD
    - glp1_eligible: GLP-1 RA eligible (FDA criteria)

    Available outcomes:
    - mace: Major Adverse Cardiovascular Events

    Available features:
    - baseline: Baseline characteristics for cohort
    """
    if cohort_name in COHORT_DEFINITIONS:
        return {
            "cohort_name": cohort_name,
            "type": "cohort",
            "sql": COHORT_DEFINITIONS[cohort_name],
            "omop_version": "5.4",
        }
    elif cohort_name in OUTCOME_DEFINITIONS:
        return {
            "cohort_name": cohort_name,
            "type": "outcome",
            "sql": OUTCOME_DEFINITIONS[cohort_name],
            "omop_version": "5.4",
        }
    elif cohort_name in FEATURE_DEFINITIONS:
        return {
            "cohort_name": cohort_name,
            "type": "feature",
            "sql": FEATURE_DEFINITIONS[cohort_name],
            "omop_version": "5.4",
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Cohort '{cohort_name}' not found. Available: {list(COHORT_DEFINITIONS.keys()) + list(OUTCOME_DEFINITIONS.keys()) + list(FEATURE_DEFINITIONS.keys())}",
        )


@router.post("/to-fhir")
async def convert_omop_to_fhir(
    omop_data: Dict[str, Any],
    person_id: int = Query(1, description="OMOP person_id to convert"),
):
    """
    Convert OMOP CDM data to a FHIR R4 Bundle.

    This is the reverse transformation (OMOP → FHIR) enabling:
    - OMOP-on-FHIR exposure
    - EHR integration from research data
    - Bidirectional sync (TermX-style)

    Expected input format:
    {
        "PERSON": [{"person_id": 1, "gender_concept_id": 8507, ...}],
        "VISIT_OCCURRENCE": [{"visit_occurrence_id": 1, "person_id": 1, ...}],
        "MEASUREMENT": [{"measurement_id": 1, "person_id": 1, ...}],
        "CONDITION_OCCURRENCE": [{"condition_occurrence_id": 1, ...}],
        "DRUG_EXPOSURE": [{"drug_exposure_id": 1, ...}],
        "OBSERVATION": [{"observation_id": 1, ...}]
    }
    """
    bundle = omop_to_fhir_bundle(omop_data, person_id)
    return bundle.to_dict()
