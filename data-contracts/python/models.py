"""
INTEGRUM V2 - SINGLE SOURCE OF TRUTH (SSOT)
Core Domain Models & Clinical Data Structures (Pydantic V2)

Este módulo es un espejo exacto del contrato en TypeScript (v2_core_types.ts).
Diseñado para la validación estricta de FastAPI y el almacenamiento NoSQL/JSONB
en la base de datos de Integrum V2.

Se rige estrictamente por HL7 FHIR y la taxonomía ICD-11/LOINC.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from uuid import UUID, uuid4

# ============================================================================
# 1. SISTEMAS DE CODIFICACIÓN (MEDICAL TAXONOMY)
# ============================================================================

class CodingSystem(str, Enum):
    ICD_11 = "ICD-11"
    ICD_10 = "ICD-10"
    SNOMED_CT = "SNOMED-CT"
    LOINC = "LOINC"
    CUSTOM = "INTEGRUM-CUSTOM"

class ClinicalStatus(str, Enum):
    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"

class VerificationStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"

class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

# ============================================================================
# 2. HL7 FHIR RESOURCES (CORE)
# ============================================================================

class ClinicalCondition(BaseModel):
    """
    Define comorbilidades y patologías. Reemplaza los 60+ booleanos de V1.
    Ejemplo: Diabetes Tipo 2 se representa como un bloque ICD-11 con código '5A11'.
    """
    code: str = Field(..., description="E.g., '5A11'")
    system: CodingSystem = Field(default=CodingSystem.ICD_11)
    display: str = Field(..., description="E.g., 'Type 2 diabetes mellitus'")
    
    clinical_status: ClinicalStatus
    verification_status: VerificationStatus
    
    onset_date_time: Optional[datetime] = None
    severity: Optional[SeverityLevel] = None
    
    integrum_tags: Optional[List[str]] = Field(
        default=None, 
        description="Metadata oculta para indexación interna y motores IA (e.g. ['OBESOGENIC'])"
    )

class ObservationValue(BaseModel):
    value: float
    unit: str

class ClinicalObservation(BaseModel):
    """
    Medibles, laboratorios y cuestionarios (TSH, Peso, GAD-7, PHQ-9).
    """
    code: str = Field(..., description="LOINC code or INTERNAL-ID")
    system: CodingSystem
    display: str = Field(..., description="E.g., 'Body Weight'")
    
    value_quantity: Optional[ObservationValue] = None
    value_string: Optional[str] = None
    
    effective_date_time: datetime = Field(default_factory=datetime.utcnow)

class DosageInstruction(BaseModel):
    text: str
    timing_frequency: Optional[int] = None
    timing_period_unit: Optional[str] = None  # h, d, wk, mo

class MedicationStatement(BaseModel):
    """
    Farmacovigilancia y tratamientos activos.
    """
    code: str
    display: str = Field(..., description="E.g., 'Metformin 850mg'")
    status: str = Field(..., description="active, completed, stopped, intended")
    
    dosage_instruction: Optional[DosageInstruction] = None
    is_obesity_inducing: bool = Field(default=False)

# ============================================================================
# 3. ENCOUNTER E INTELIGENCIA ARTIFICIAL (QMS / DECISIONES CLINICAS)
# ============================================================================

class EncounterType(str, Enum):
    T0_BASELINE = "T0_BASELINE"
    T1_FOLLOW_UP = "T1_FOLLOW_UP"
    URGENT = "URGENT"

class EngineName(str, Enum):
    ACOSTA_PHENOTYPE = "ACOSTA_PHENOTYPE"
    EOSS_STAGING = "EOSS_STAGING"
    METABOLIC_ROUTER = "METABOLIC_ROUTER"
    CARDIO_RISK = "CARDIO_RISK"

class AdjudicationResult(BaseModel):
    """
    Output inmutable de las reglas determinísticas y modelos de IA.
    Registra sobreescritura clínica explícita para SaMD FDA/INVIMA compliance.
    """
    engine_name: EngineName
    version: str = Field(..., description="e.g. 'v2.1.0' - Deterministic Traceability")
    
    calculated_value: str = Field(..., description="e.g., 'Phenotype C - Hedonic'")
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Especialista / Criterio Médico (Human-In-The-Loop)
    is_overridden: bool = Field(default=False)
    override_value: Optional[str] = None
    override_reason: Optional[str] = None
    override_clinician_id: Optional[UUID] = None

class ClinicalEncounter(BaseModel):
    """
    Payload absoluto y consolidado de una consulta. 
    Este esquema es lo que la API de V2 recibe del Frontend y almacena.
    """
    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    tenant_id: UUID
    
    status: str = Field(..., description="planned, in-progress, finished, cancelled")
    encounter_type: EncounterType
    
    period_start: datetime
    period_end: Optional[datetime] = None

    # Arrays Estructurados (Terminamos con el "Data Flattening")
    conditions: List[ClinicalCondition] = Field(default_factory=list)
    observations: List[ClinicalObservation] = Field(default_factory=list)
    medications: List[MedicationStatement] = Field(default_factory=list)
    
    ai_adjudications: List[AdjudicationResult] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "123e4567-e89b-12d3-a456-426614174000",
                "encounter_type": "T0_BASELINE",
                "conditions": [
                    {
                        "code": "5A11",
                        "system": "ICD-11",
                        "display": "Type 2 diabetes mellitus",
                        "clinical_status": "active",
                        "verification_status": "confirmed"
                    }
                ]
            }
        }
    )
