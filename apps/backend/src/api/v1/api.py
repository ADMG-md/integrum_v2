from fastapi import APIRouter
from src.api.v1.endpoints import (
    conditions,
    encounter,
    extraction,
    audit,
    timeline,
    auth,
    patient,
    tenant,
    professional,
    consent,
    export,
    fhir,
    omop,
    metadata,
    ai_analysis,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
api_router.include_router(patient.router, prefix="/patients", tags=["patients"])
api_router.include_router(conditions.router, prefix="/conditions", tags=["conditions"])
api_router.include_router(encounter.router, prefix="/encounters", tags=["encounters"])
api_router.include_router(extraction.router, prefix="/extraction", tags=["extraction"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
api_router.include_router(tenant.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(
    professional.router, prefix="/professionals", tags=["professionals"]
)
api_router.include_router(consent.router, prefix="/consent", tags=["consent"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(fhir.router, prefix="/fhir", tags=["FHIR R4"])
api_router.include_router(omop.router, prefix="", tags=["OMOP CDM 5.4"])
api_router.include_router(ai_analysis.router, prefix="/ai", tags=["AI Analysis"])
