"""
FHIR R4 Resource Models for Integrum V2.

Pydantic models that map Integrum V2 internal data structures to HL7 FHIR R4
resources. These models enable interoperability with EHRs, research networks,
and OMOP CDM via standard FHIR APIs.

References:
- HL7 FHIR R4: http://hl7.org/fhir/R4/
- US Core Vitals: http://hl7.org/fhir/us/vitals/
- OMOP-on-FHIR: https://github.com/OHDSI/OMOPonFHIR
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.fhir.concept_map import (
    get_loinc_for_code,
    get_snomed_for_icd10,
    get_atc_for_medication,
)


# ============================================================
# FHIR Core Types
# ============================================================


class FHIRIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None
    use: Optional[str] = None  # usual | official | temp | secondary | old


class FHIRCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    coding: List[FHIRCoding] = []
    text: Optional[str] = None


class FHIRQuantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = "http://unitsofmeasure.org"
    code: Optional[str] = None


class FHIRReference(BaseModel):
    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRPeriod(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


# ============================================================
# FHIR Resources
# ============================================================


class FHIRPatient(BaseModel):
    """FHIR Patient resource mapped from Integrum Patient."""

    resourceType: str = "Patient"
    id: Optional[str] = None
    identifier: List[FHIRIdentifier] = []
    gender: Optional[str] = None  # male | female | other | unknown
    birthDate: Optional[str] = None
    extension: List[Dict[str, Any]] = []

    @classmethod
    def from_encounter(cls, encounter) -> FHIRPatient:
        """Create FHIR Patient from Integrum Encounter."""
        patient = encounter.patient if hasattr(encounter, "patient") else None
        demographics = encounter.demographics

        gender_map = {"male": "male", "female": "female", "m": "male", "f": "female"}
        gender = gender_map.get(
            demographics.gender.lower() if demographics.gender else "", "unknown"
        )

        identifiers = []
        if patient:
            identifiers.append(
                FHIRIdentifier(
                    system="urn:oid:integrum", value=str(patient.id), use="official"
                )
            )
        identifiers.append(
            FHIRIdentifier(
                system="urn:oid:integrum-encounter", value=encounter.id, use="temp"
            )
        )

        extensions = []
        if (
            demographics
            and hasattr(demographics, "ethnicity")
            and demographics.ethnicity
        ):
            extensions.append(
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-ethnicity",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-Race",
                                "code": demographics.ethnicity.upper(),
                            }
                        ]
                    },
                }
            )

        return cls(
            id=encounter.id,
            identifier=identifiers,
            gender=gender,
            birthDate=str(demographics.date_of_birth)
            if demographics and demographics.date_of_birth
            else None,
            extension=extensions,
        )


class FHIREncounter(BaseModel):
    """FHIR Encounter resource."""

    resourceType: str = "Encounter"
    id: Optional[str] = None
    status: str = "finished"  # planned | arrived | triaged | in-progress | onleave | finished | cancelled
    class_code: Dict[str, str] = Field(
        default_factory=lambda: {
            "code": "AMB",
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        }
    )
    subject: Optional[FHIRReference] = None
    period: Optional[FHIRPeriod] = None
    reasonCode: List[FHIRCodeableConcept] = []
    type: List[FHIRCodeableConcept] = []

    @classmethod
    def from_encounter(cls, encounter) -> FHIREncounter:
        """Create FHIR Encounter from Integrum Encounter."""
        reason_code = []
        if encounter.reason_for_visit:
            reason_code.append(FHIRCodeableConcept(text=encounter.reason_for_visit))

        return cls(
            id=encounter.id,
            status="finished"
            if getattr(encounter, "status", None) == "FINALIZED"
            else "in-progress",
            subject=FHIRReference(
                reference=f"Patient/{encounter.id}", display="Patient"
            ),
            period=FHIRPeriod(
                start=encounter.created_at.isoformat() if encounter.created_at else None
            ),
            reasonCode=reason_code,
            type=[
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://snomed.info/sct",
                            code="308335008",
                            display="Patient encounter procedure",
                        )
                    ]
                )
            ],
        )


class FHIRObservation(BaseModel):
    """FHIR Observation resource for vitals, labs, and calculated indices."""

    resourceType: str = "Observation"
    id: Optional[str] = None
    status: str = "final"  # registered | preliminary | final | amended | corrected
    category: List[FHIRCodeableConcept] = []
    code: FHIRCodeableConcept
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    effectiveDateTime: Optional[str] = None
    valueQuantity: Optional[FHIRQuantity] = None
    valueString: Optional[str] = None
    valueCodeableConcept: Optional[FHIRCodeableConcept] = None
    valueInteger: Optional[int] = None
    component: List[Dict[str, Any]] = []
    derivedFrom: List[FHIRReference] = []
    referenceRange: List[Dict[str, Any]] = []

    @classmethod
    def from_observation(cls, obs, encounter_id: str) -> FHIRObservation:
        """Create FHIR Observation from Integrum Observation."""
        loinc_info = get_loinc_for_code(obs.code)

        if loinc_info:
            loinc_code, display, unit = loinc_info
        else:
            loinc_code = obs.code
            display = obs.code
            unit = obs.unit or ""

        # Determine value type
        value_quantity = None
        value_string = None
        value_integer = None

        if obs.value is not None:
            try:
                float_val = float(obs.value)
                value_quantity = FHIRQuantity(value=float_val, unit=unit)
            except (ValueError, TypeError):
                value_string = str(obs.value)

        # Category based on code type
        category = []
        if any(
            prefix in obs.code
            for prefix in ["29463-7", "8302-2", "8280-0", "WAIST", "MMA", "MUSCLE"]
        ):
            category.append(
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="vital-signs",
                            display="Vital Signs",
                        )
                    ]
                )
            )
        elif any(
            prefix in obs.code
            for prefix in [
                "GLUCOSE",
                "HBA1C",
                "INSULIN",
                "TC",
                "HDL",
                "LDL",
                "TG",
                "AST",
                "ALT",
                "GGT",
                "CREAT",
                "UA",
                "CRP",
                "TSH",
                "FT4",
                "FT3",
            ]
        ):
            category.append(
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="laboratory",
                            display="Laboratory",
                        )
                    ]
                )
            )
        elif any(prefix in obs.code for prefix in ["PHQ9", "GAD7", "ATENAS", "SARCF"]):
            category.append(
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="survey",
                            display="Survey",
                        )
                    ]
                )
            )
        else:
            category.append(
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="exam",
                            display="Exam",
                        )
                    ]
                )
            )

        return cls(
            id=f"obs-{obs.code}-{encounter_id}",
            status="final",
            category=category,
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system="http://loinc.org", code=loinc_code, display=display
                    )
                ],
                text=display,
            ),
            subject=FHIRReference(reference=f"Patient/{encounter_id}"),
            encounter=FHIRReference(reference=f"Encounter/{encounter_id}"),
            valueQuantity=value_quantity,
            valueString=value_string,
            valueInteger=value_integer,
        )

    @classmethod
    def calculated(
        cls,
        code: str,
        display: str,
        value: float,
        unit: str,
        encounter_id: str,
        threshold: Optional[str] = None,
        derived_from: Optional[List[str]] = None,
    ) -> FHIRObservation:
        """Create a calculated/derived FHIR Observation (e.g., HOMA-IR, TyG, FLI)."""
        return cls(
            id=f"calc-{code}-{encounter_id}",
            status="final",
            category=[
                FHIRCodeableConcept(
                    coding=[
                        FHIRCoding(
                            system="http://terminology.hl7.org/CodeSystem/observation-category",
                            code="laboratory",
                            display="Laboratory",
                        )
                    ]
                )
            ],
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(system="http://loinc.org", code=code, display=display)
                ],
                text=display,
            ),
            subject=FHIRReference(reference=f"Patient/{encounter_id}"),
            encounter=FHIRReference(reference=f"Encounter/{encounter_id}"),
            valueQuantity=FHIRQuantity(value=value, unit=unit),
            derivedFrom=[
                FHIRReference(reference=f"Observation/{ref}")
                for ref in (derived_from or [])
            ],
            referenceRange=[{"text": threshold}] if threshold else [],
        )


class FHIRCondition(BaseModel):
    """FHIR Condition resource for diagnoses."""

    resourceType: str = "Condition"
    id: Optional[str] = None
    clinicalStatus: FHIRCodeableConcept = Field(
        default_factory=lambda: FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                    code="active",
                    display="Active",
                )
            ]
        )
    )
    verificationStatus: FHIRCodeableConcept = Field(
        default_factory=lambda: FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    code="confirmed",
                    display="Confirmed",
                )
            ]
        )
    )
    category: List[FHIRCodeableConcept] = []
    code: FHIRCodeableConcept
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    onsetDateTime: Optional[str] = None

    @classmethod
    def from_condition(cls, condition, encounter_id: str) -> FHIRCondition:
        """Create FHIR Condition from Integrum Condition."""
        snomed_info = get_snomed_for_icd10(condition.code)

        if snomed_info:
            snomed_code, display = snomed_info
        else:
            snomed_code = condition.code
            display = condition.title or condition.code

        codings = [
            FHIRCoding(
                system="http://snomed.info/sct", code=snomed_code, display=display
            )
        ]
        if condition.code:
            codings.append(
                FHIRCoding(
                    system="http://hl7.org/fhir/sid/icd-10",
                    code=condition.code,
                    display=display,
                )
            )

        return cls(
            id=f"cond-{condition.code}-{encounter_id}",
            code=FHIRCodeableConcept(coding=codings, text=display),
            subject=FHIRReference(reference=f"Patient/{encounter_id}"),
            encounter=FHIRReference(reference=f"Encounter/{encounter_id}"),
            onsetDateTime=condition.onset_date.isoformat()
            if condition.onset_date
            else None,
        )


class FHIRMedicationStatement(BaseModel):
    """FHIR MedicationStatement resource."""

    resourceType: str = "MedicationStatement"
    id: Optional[str] = None
    status: str = "active"  # active | completed | entered-in-error | intended |stopped | on-hold | unknown
    medicationCodeableConcept: FHIRCodeableConcept
    subject: Optional[FHIRReference] = None
    effectivePeriod: Optional[FHIRPeriod] = None
    dosage: List[Dict[str, Any]] = []

    @classmethod
    def from_medication(cls, medication, encounter_id: str) -> FHIRMedicationStatement:
        """Create FHIR MedicationStatement from Integrum Medication."""
        atc_info = get_atc_for_medication(medication.name)

        codings = []
        if atc_info:
            atc_code, display, atc_class = atc_info
            codings.append(
                FHIRCoding(
                    system="http://www.whocc.no/atc",
                    code=atc_code,
                    display=f"{display} ({atc_class})",
                )
            )
        codings.append(
            FHIRCoding(
                system="http://snomed.info/sct",
                code=medication.code or medication.name,
                display=medication.name,
            )
        )

        dosage_info = []
        if medication.dose_amount or medication.frequency:
            dosage_info.append(
                {
                    "text": f"{medication.dose_amount or ''} {medication.frequency or ''}".strip(),
                    "route": FHIRCodeableConcept(
                        coding=[
                            FHIRCoding(
                                system="http://snomed.info/sct",
                                code="26643006",
                                display="Oral route",
                            )
                        ]
                    )
                    if medication.name
                    else None,
                }
            )

        return cls(
            id=f"med-{medication.code or medication.name}-{encounter_id}",
            status="active" if medication.is_active else "completed",
            medicationCodeableConcept=FHIRCodeableConcept(
                coding=codings, text=medication.name
            ),
            subject=FHIRReference(reference=f"Patient/{encounter_id}"),
            effectivePeriod=FHIRPeriod(
                start=medication.start_date.isoformat()
                if medication.start_date
                else None,
                end=medication.end_date.isoformat() if medication.end_date else None,
            ),
            dosage=dosage_info,
        )


class FHIRQuestionnaireResponse(BaseModel):
    """FHIR QuestionnaireResponse for psychometric assessments."""

    resourceType: str = "QuestionnaireResponse"
    id: Optional[str] = None
    status: str = "completed"  # in-progress | completed | entered-in-error | stopped
    questionnaire: Optional[str] = None
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    authored: Optional[str] = None
    item: List[Dict[str, Any]] = []
    totalScore: Optional[Dict[str, Any]] = None

    @classmethod
    def from_psychometric(
        cls,
        questionnaire_id: str,
        score: float,
        responses: Dict[str, int],
        encounter_id: str,
        authored: Optional[datetime] = None,
    ) -> FHIRQuestionnaireResponse:
        """Create FHIR QuestionnaireResponse from psychometric data."""
        items = []
        for q_id, value in responses.items():
            items.append(
                {
                    "linkId": q_id,
                    "answer": [{"valueInteger": value}],
                }
            )

        return cls(
            id=f"qr-{questionnaire_id}-{encounter_id}",
            status="completed",
            questionnaire=f"Questionnaire/{questionnaire_id}",
            subject=FHIRReference(reference=f"Patient/{encounter_id}"),
            encounter=FHIRReference(reference=f"Encounter/{encounter_id}"),
            authored=authored.isoformat() if authored else None,
            item=items,
            totalScore={"valueInteger": int(score)},
        )


class FHIRBundle(BaseModel):
    """FHIR Bundle resource (collection type)."""

    resourceType: str = "Bundle"
    type: str = "collection"
    id: Optional[str] = None
    timestamp: Optional[str] = None
    entry: List[Dict[str, Any]] = []

    def add_resource(self, resource: BaseModel) -> None:
        """Add a FHIR resource to the bundle."""
        self.entry.append({"resource": resource.model_dump(exclude_none=True)})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=True)
