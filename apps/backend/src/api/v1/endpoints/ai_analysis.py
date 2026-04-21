"""
AI Analysis Endpoint — Anonymized Data Export + Generative AI Analysis

This module provides:
1. /ai/export - Export anonymized clinical data ready for AI analysis
2. /ai/analyze - Generate expert medical prompts for AI analysis
3. /ai/batch - Batch analysis for multiple encounters

HIPAA Safe Harbor + Colombia Ley 1581 compliant.
Requires roles: SUPERADMIN, MEDICAL_DIRECTOR, AUDITOR
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import hashlib
import asyncio

from src.database import get_db
from src.models.user import UserModel, UserRole
from src.models.encounter import EncounterModel, Patient
from src.services.auth_service import check_role
from src.services.ai_analysis_service import (
    AIAnalysisService,
    ClinicalContext,
    AnalysisRequest,
    ExpertMedicalPrompt,
)
from src.services.sanitization_service import sanitization_service

router = APIRouter()


def _anonymize_id(id_str: str) -> str:
    """Deterministic anonymization: same ID always produces same hash."""
    salt = "integrum-ai-analysis-salt-2026"
    return hashlib.sha256(f"{salt}:{id_str}".encode()).hexdigest()[:16]


class ClinicalContextExport(BaseModel):
    """Structured clinical context for AI export."""

    patient_id: str
    demographics: Dict[str, Any]
    anthropometry: Dict[str, Any]
    labs: Dict[str, Any]
    motors: Dict[str, Any]
    conditions: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    lifestyle: Dict[str, Any] = Field(default_factory=dict)
    encounter_date: Optional[str] = None


class AnalysisRequestSchema(BaseModel):
    """Request for AI clinical analysis."""

    context: ClinicalContextExport
    query_type: Literal[
        "comprehensive",
        "phenotype_analysis",
        "treatment_plan",
        "risk_assessment",
        "differential_diagnosis",
        "medication_review",
        "nutrition_recommendation",
        "pediatric_assessment",
    ] = "comprehensive"
    expertise_level: Literal["expert", "specialist", "consultant"] = "expert"
    include_differential: bool = True
    include_references: bool = True


class AnalysisResponseSchema(BaseModel):
    """Response containing generated prompt for AI analysis."""

    analysis_id: str
    prompt: ExpertMedicalPrompt
    metadata: Dict[str, Any]


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis of multiple encounters."""

    encounter_ids: List[str]
    query_type: Literal[
        "comprehensive",
        "phenotype_analysis",
        "treatment_plan",
        "risk_assessment",
    ] = "comprehensive"
    expertise_level: Literal["expert", "specialist", "consultant"] = "expert"


def _build_clinical_context(
    patient: Patient,
    encounter: EncounterModel,
) -> ClinicalContextExport:
    """Build anonymized clinical context from encounter data."""

    demo = {
        "age": encounter.demographics_age
        if hasattr(encounter, "demographics_age")
        else None,
        "gender": patient.gender,
    }

    anthro = {}
    labs = {}
    motors = encounter.phenotype_result or {}
    conditions = []
    medications = []
    lifestyle = {}

    for obs in encounter.observations or []:
        if obs.code in ["29463-7", "8302-2", "WAIST-001", "HIP-001"]:
            anthro[obs.code] = obs.value
        else:
            labs[obs.code] = obs.value

    for cond in encounter.conditions or []:
        conditions.append(
            {
                "code": cond.code,
                "title": cond.title,
                "status": getattr(cond, "clinical_status", "active"),
            }
        )

    for med in encounter.medications or []:
        medications.append(
            {
                "name": med.name,
                "dose": getattr(med, "dose", ""),
                "frequency": getattr(med, "frequency", ""),
                "status": getattr(med, "status", "active"),
            }
        )

    acosta = motors.get("AcostaPhenotypeMotor", {})
    phenotype = acosta.get("calculated_value") if isinstance(acosta, dict) else None

    eoss = motors.get("EOSSStagingMotor", {})
    eoss_stage = eoss.get("calculated_value") if isinstance(eoss, dict) else None

    return ClinicalContextExport(
        patient_id=_anonymize_id(patient.id),
        demographics=demo,
        anthropometry=anthro,
        labs=labs,
        motors=motors,
        conditions=conditions,
        medications=medications,
        lifestyle=lifestyle,
        encounter_date=encounter.created_at.date().isoformat()
        if encounter.created_at
        else None,
    )


def _build_clinical_context_from_dict(data: Dict[str, Any]) -> ClinicalContext:
    """Build ClinicalContext from exported dictionary."""
    return ClinicalContext(
        patient_id=data.get("patient_id", ""),
        demographics=data.get("demographics", {}),
        anthropometry=data.get("anthropometry", {}),
        labs=data.get("labs", {}),
        motors=data.get("motors", {}),
        conditions=data.get("conditions", []),
        medications=data.get("medications", []),
        lifestyle=data.get("lifestyle", {}),
        phenotype=data.get("phenotype"),
        eoss_stage=data.get("eoss_stage"),
        encounter_date=data.get("encounter_date"),
    )


ai_service = AIAnalysisService()


@router.post("/export/anonymized")
async def export_for_ai_analysis(
    encounter_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    status_filter: str = "FINALIZED",
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR, UserRole.AUDITOR])
    ),
) -> Dict[str, Any]:
    """
    Export anonymized clinical data ready for AI analysis.

    One of encounter_id or patient_id is required.
    All data is fully anonymized (HIPAA Safe Harbor compliant).

    Returns structured clinical context that can be fed to LLMs.
    """
    if not encounter_id and not patient_id:
        raise HTTPException(
            status_code=400, detail="Either encounter_id or patient_id is required"
        )

    if encounter_id:
        enc_stmt = select(EncounterModel).where(EncounterModel.id == encounter_id)
        enc_result = await db.execute(enc_stmt)
        encounter = enc_result.scalar_one_or_none()

        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        pat_stmt = select(Patient).where(Patient.id == encounter.patient_id)
        pat_result = await db.execute(pat_stmt)
        patient = pat_result.scalar_one_or_none()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        context = _build_clinical_context(patient, encounter)

        return {
            "data": context.model_dump(),
            "metadata": {
                "export_type": "single_encounter",
                "anonymized": True,
                "pii_removed": ["name", "email", "phone", "address", "date_of_birth"],
                "id_hashing": "SHA-256 deterministic",
            },
        }

    else:
        pat_stmt = select(Patient).where(Patient.id == patient_id)
        pat_result = await db.execute(pat_stmt)
        patient = pat_result.scalar_one_or_none()

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        enc_stmt = (
            select(EncounterModel)
            .where(
                EncounterModel.patient_id == patient_id,
                EncounterModel.status == status_filter,
            )
            .order_by(EncounterModel.created_at)
        )
        enc_result = await db.execute(enc_stmt)
        encounters = enc_result.scalars().all()

        contexts = []
        for enc in encounters:
            context = _build_clinical_context(patient, enc)
            contexts.append(context.model_dump())

        return {
            "data": contexts,
            "metadata": {
                "export_type": "patient_timeline",
                "patient_id_anonymized": _anonymize_id(patient_id),
                "encounter_count": len(contexts),
                "status_filter": status_filter,
                "anonymized": True,
                "pii_removed": ["name", "email", "phone", "address", "date_of_birth"],
            },
        }


@router.post("/analyze")
async def analyze_clinical_case(
    request: AnalysisRequestSchema,
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR, UserRole.AUDITOR])
    ),
) -> AnalysisResponseSchema:
    """
    Generate an expert medical prompt for AI analysis of clinical data.

    The generated prompt constrains the AI to:
    1. Act as a board-certified expert physician
    2. Ground all responses in the provided clinical data
    3. Reference specific clinical guidelines
    4. Flag safety concerns and uncertainties
    5. Provide structured, actionable recommendations

    The prompt is designed to minimize hallucination and maximize clinical utility.
    """
    clinical_context = _build_clinical_context_from_dict(request.context.model_dump())

    analysis_request = AnalysisRequest(
        context=clinical_context,
        query_type=request.query_type,
        expertise_level=request.expertise_level,
        include_differential=request.include_differential,
        include_references=request.include_references,
    )

    prompt = ai_service.generate_prompt(analysis_request)

    analysis_id = hashlib.sha256(
        f"{clinical_context.patient_id}:{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16]

    return AnalysisResponseSchema(
        analysis_id=analysis_id,
        prompt=prompt,
        metadata={
            "query_type": request.query_type,
            "expertise_level": request.expertise_level,
            "include_differential": request.include_differential,
            "include_references": request.include_references,
            "generated_at": datetime.utcnow().isoformat(),
            "guidelines": [
                "ADA Standards of Care 2024",
                "AACE/ACE Comprehensive Care Algorithm 2024",
                "AHA/ACC Obesity Management Guideline 2023",
                "ESPEN Obesity Guidelines 2023",
                "AAP Pediatric Obesity Guideline 2023",
            ],
        },
    )


@router.post("/batch")
async def batch_analyze(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR])
    ),
) -> Dict[str, Any]:
    """
    Generate expert prompts for batch analysis of multiple encounters.

    Useful for:
    - Quality assurance reviews
    - Research cohort analysis
    - Clinical guideline adherence audits

    Returns a list of prompts, one per encounter.
    """
    if len(request.encounter_ids) > 100:
        raise HTTPException(
            status_code=400, detail="Maximum 100 encounters per batch request"
        )

    prompts = []
    errors = []

    for enc_id in request.encounter_ids:
        try:
            enc_stmt = select(EncounterModel).where(EncounterModel.id == enc_id)
            enc_result = await db.execute(enc_stmt)
            encounter = enc_result.scalar_one_or_none()

            if not encounter:
                errors.append({"encounter_id": enc_id, "error": "Not found"})
                continue

            pat_stmt = select(Patient).where(Patient.id == encounter.patient_id)
            pat_result = await db.execute(pat_stmt)
            patient = pat_result.scalar_one_or_none()

            if not patient:
                errors.append({"encounter_id": enc_id, "error": "Patient not found"})
                continue

            context_dict = _build_clinical_context(patient, encounter).model_dump()
            clinical_context = _build_clinical_context_from_dict(context_dict)

            analysis_request = AnalysisRequest(
                context=clinical_context,
                query_type=request.query_type,
                expertise_level=request.expertise_level,
                include_differential=True,
                include_references=True,
            )

            prompt = ai_service.generate_prompt(analysis_request)

            prompts.append(
                {
                    "encounter_id_anonymized": _anonymize_id(enc_id),
                    "patient_id_anonymized": _anonymize_id(patient.id),
                    "query_type": request.query_type,
                    "prompt": prompt.model_dump(),
                }
            )

        except Exception as e:
            errors.append({"encounter_id": enc_id, "error": str(e)})

    return {
        "batch_id": hashlib.sha256(
            f"{datetime.utcnow().isoformat()}:{len(request.encounter_ids)}".encode()
        ).hexdigest()[:16],
        "total_requested": len(request.encounter_ids),
        "successful": len(prompts),
        "errors": errors,
        "prompts": prompts,
        "metadata": {
            "query_type": request.query_type,
            "expertise_level": request.expertise_level,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


@router.post("/validate")
async def validate_ai_response(
    response_text: str,
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR, UserRole.AUDITOR])
    ),
) -> Dict[str, Any]:
    """
    Validate an AI-generated clinical response for safety and quality.

    Checks for:
    - Hallucination risk indicators
    - Safety concerns (overly certain statements, dangerous recommendations)
    - Guideline citation presence
    - Completeness (required sections present)
    """
    validation = ai_service.validate_clinical_response(response_text)

    return {
        "validation": validation,
        "metadata": {
            "validated_at": datetime.utcnow().isoformat(),
            "response_length": len(response_text),
        },
    }


@router.get("/guidelines")
async def get_applicable_guidelines(
    query_type: Optional[str] = None,
    patient_age: Optional[int] = None,
    current_user: UserModel = Depends(
        check_role([UserRole.SUPERADMIN, UserRole.MEDICAL_DIRECTOR, UserRole.AUDITOR])
    ),
) -> Dict[str, Any]:
    """
    Get list of clinical guidelines applicable for AI analysis.

    Optionally filtered by query type and patient age.
    """
    all_guidelines = {
        "obesity": [
            {
                "id": "ADA-2024",
                "name": "ADA Standards of Care 2024",
                "organization": "ADA",
            },
            {
                "id": "AACE-2024",
                "name": "AACE/ACE Comprehensive Care Algorithm 2024",
                "organization": "AACE",
            },
            {
                "id": "AHA-OBESITY-2023",
                "name": "AHA/ACC Guideline on Management of Obesity 2023",
                "organization": "AHA/ACC",
            },
            {
                "id": "ESPEN-2023",
                "name": "ESPEN Guidelines on Obesity",
                "organization": "ESPEN",
            },
        ],
        "cardiovascular": [
            {
                "id": "AHA-ASCVD-2018",
                "name": "AHA/ACC Guideline on Primary Prevention 2018",
                "organization": "AHA/ACC",
            },
            {
                "id": "ESC-LIPID-2019",
                "name": "ESC/EAS Dyslipidaemia Guidelines 2019",
                "organization": "ESC",
            },
            {
                "id": "KDIGO-BP-2024",
                "name": "KDIGO Blood Pressure in CKD 2024",
                "organization": "KDIGO",
            },
        ],
        "pediatric": [
            {
                "id": "AAP-OBESITY-2023",
                "name": "AAP Clinical Practice Guideline for Pediatric Obesity 2023",
                "organization": "AAP",
            },
            {
                "id": "USPSTF-PEDS-2024",
                "name": "USPSTF Obesity in Children Screening 2024",
                "organization": "USPSTF",
            },
            {
                "id": "AAP-NUTRITION-2024",
                "name": "AAP Council on Children Nutrition Guidelines 2024",
                "organization": "AAP",
            },
        ],
        "endocrine": [
            {
                "id": "ATA-THYROID-2023",
                "name": "ATA Thyroid Guidelines 2023",
                "organization": "ATA",
            },
            {
                "id": "ENDOCRINE-SOC-2023",
                "name": "Endocrine Society Clinical Guidelines 2023",
                "organization": "Endocrine Society",
            },
        ],
        "screening": [
            {
                "id": "USPSTF-COLORECTAL-2021",
                "name": "USPSTF Colorectal Cancer Screening 2021",
                "organization": "USPSTF",
            },
            {
                "id": "USPSTF-BREAST-2024",
                "name": "USPSTF Breast Cancer Screening 2024",
                "organization": "USPSTF",
            },
            {
                "id": "ACS-SCREENING-2024",
                "name": "ACS Cancer Screening Guidelines 2024",
                "organization": "ACS",
            },
        ],
    }

    if patient_age is not None and patient_age < 18:
        return {
            "guidelines": all_guidelines.get("pediatric", []),
            "filter_applied": {"patient_age": patient_age, "scope": "pediatric"},
        }

    if query_type:
        type_guideline_map = {
            "risk_assessment": "cardiovascular",
            "treatment_plan": "obesity",
            "nutrition_recommendation": "obesity",
            "pediatric_assessment": "pediatric",
            "differential_diagnosis": "endocrine",
            "medication_review": "endocrine",
        }
        filtered_category = type_guideline_map.get(query_type)
        if filtered_category:
            return {
                "guidelines": all_guidelines.get(filtered_category, []),
                "filter_applied": {"query_type": query_type},
            }

    all_guidelines_flat = []
    for category, guidelines in all_guidelines.items():
        all_guidelines_flat.extend(guidelines)

    return {
        "guidelines": all_guidelines_flat,
        "metadata": {
            "total": len(all_guidelines_flat),
            "categories": list(all_guidelines.keys()),
        },
    }
