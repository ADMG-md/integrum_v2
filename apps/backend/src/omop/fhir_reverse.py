"""
OMOP CDM 5.4 → FHIR R4 Reverse Transformation.

Converts OMOP CDM data back to FHIR R4 resources, enabling:
- OMOP-on-FHIR exposure
- EHR integration from research data
- Bidirectional sync (TermX-style)
- Clinical apps consuming OMOP data via FHIR

Based on HL7 FHIR → OMOP ConceptMap and TermX transformation rules.
References:
- TermX: Ardel et al., 2026 (Frontiers in Medicine)
- OMOP-on-FHIR: https://github.com/OHDSI/OMOPonFHIR
- HL7 FHIR → OMOP ConceptMap: https://hl7.org/fhir/uv/ohdsi/
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.fhir.resources import (
    FHIRBundle,
    FHIRPatient,
    FHIREncounter,
    FHIRObservation,
    FHIRCondition,
    FHIRMedicationStatement,
    FHIRQuantity,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRReference,
)
from src.fhir.concept_map import (
    LOINC_TO_OBSERVATION,
    CONDITION_TO_SNOMED,
    MEDICATION_TO_ATC,
)
from src.omop.concept_map import (
    LOINC_TO_OMOP_MEASUREMENT,
    ICD10_TO_OMOP_CONDITION,
    ATC_TO_OMOP_DRUG,
)


# Reverse mappings: OMOP concept_id → FHIR code
OMOP_MEASUREMENT_TO_LOINC: Dict[int, str] = {
    omop_id: loinc for loinc, (omop_id, _) in LOINC_TO_OMOP_MEASUREMENT.items()
}

OMOP_CONDITION_TO_ICD10: Dict[int, str] = {
    omop_id: icd10 for icd10, (omop_id, _) in ICD10_TO_OMOP_CONDITION.items()
}

OMOP_DRUG_TO_ATC: Dict[int, str] = {
    omop_id: atc for atc, (omop_id, _) in ATC_TO_OMOP_DRUG.items()
}


def omop_to_fhir_bundle(
    omop_data: Dict[str, List[Dict[str, Any]]],
    person_id: int,
) -> FHIRBundle:
    """
    Convert OMOP CDM data to a FHIR R4 Bundle.

    Args:
        omop_data: Dict mapping OMOP table names to lists of row dicts.
            Expected keys: PERSON, VISIT_OCCURRENCE, MEASUREMENT,
            CONDITION_OCCURRENCE, DRUG_EXPOSURE, OBSERVATION
        person_id: OMOP person_id to filter by

    Returns:
        FHIRBundle containing Patient, Encounters, Observations,
        Conditions, and MedicationStatements
    """
    bundle = FHIRBundle(
        id=f"omop-person-{person_id}",
        type="collection",
        timestamp=datetime.utcnow().isoformat(),
    )

    # 1. PERSON → Patient
    person_rows = omop_data.get("PERSON", [])
    for person in person_rows:
        if person.get("person_id") == person_id:
            fhir_patient = _person_to_fhir_patient(person)
            bundle.add_resource(fhir_patient)

    # 2. VISIT_OCCURRENCE → Encounter
    visit_rows = omop_data.get("VISIT_OCCURRENCE", [])
    for visit in visit_rows:
        if visit.get("person_id") == person_id:
            fhir_encounter = _visit_to_fhir_encounter(visit, person_id)
            bundle.add_resource(fhir_encounter)

    # 3. MEASUREMENT → Observation
    measurement_rows = omop_data.get("MEASUREMENT", [])
    for meas in measurement_rows:
        if meas.get("person_id") == person_id:
            fhir_obs = _measurement_to_fhir_observation(meas, person_id)
            if fhir_obs:
                bundle.add_resource(fhir_obs)

    # 4. CONDITION_OCCURRENCE → Condition
    condition_rows = omop_data.get("CONDITION_OCCURRENCE", [])
    for cond in condition_rows:
        if cond.get("person_id") == person_id:
            fhir_cond = _condition_to_fhir_condition(cond, person_id)
            if fhir_cond:
                bundle.add_resource(fhir_cond)

    # 5. DRUG_EXPOSURE → MedicationStatement
    drug_rows = omop_data.get("DRUG_EXPOSURE", [])
    for drug in drug_rows:
        if drug.get("person_id") == person_id:
            fhir_med = _drug_to_fhir_medication(drug, person_id)
            if fhir_med:
                bundle.add_resource(fhir_med)

    # 6. OBSERVATION → QuestionnaireResponse or Observation
    obs_rows = omop_data.get("OBSERVATION", [])
    for obs in obs_rows:
        if obs.get("person_id") == person_id:
            fhir_obs = _omop_observation_to_fhir(obs, person_id)
            if fhir_obs:
                bundle.add_resource(fhir_obs)

    return bundle


def _person_to_fhir_patient(person: Dict[str, Any]) -> FHIRPatient:
    """Convert OMOP PERSON to FHIR Patient."""
    gender_map = {8507: "male", 8532: "female", 0: "unknown"}
    omop_gender = person.get("gender_concept_id", 0)
    gender = gender_map.get(omop_gender, "unknown")

    identifiers = []
    if person.get("person_id"):
        identifiers.append(
            {
                "system": "urn:oid:omop",
                "value": str(person["person_id"]),
                "use": "official",
            }
        )

    extensions = []
    if person.get("race_concept_id"):
        extensions.append(
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-race",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-Race",
                            "code": str(person["race_concept_id"]),
                        }
                    ]
                },
            }
        )

    return FHIRPatient(
        id=str(person.get("person_id")),
        identifier=identifiers,
        gender=gender,
        birthDate=str(person.get("year_of_birth", ""))[:4]
        if person.get("year_of_birth")
        else None,
        extension=extensions,
    )


def _visit_to_fhir_encounter(visit: Dict[str, Any], person_id: int) -> FHIREncounter:
    """Convert OMOP VISIT_OCCURRENCE to FHIR Encounter."""
    visit_class_map = {
        9201: "IP",  # Inpatient
        9202: "AMB",  # Ambulatory
        9203: "EMER",  # Emergency
        581476: "VR",  # Virtual
    }
    omop_class = visit.get("visit_concept_id", 9202)
    visit_class = visit_class_map.get(omop_class, "AMB")

    return FHIREncounter(
        id=str(visit.get("visit_occurrence_id")),
        status="finished" if visit.get("visit_end_date") else "in-progress",
        class_code={
            "code": visit_class,
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        },
        subject=FHIRReference(reference=f"Patient/{person_id}"),
    )


def _measurement_to_fhir_observation(
    meas: Dict[str, Any], person_id: int
) -> Optional[FHIRObservation]:
    """Convert OMOP MEASUREMENT to FHIR Observation."""
    concept_id = meas.get("measurement_concept_id", 0)
    loinc_code = OMOP_MEASUREMENT_TO_LOINC.get(concept_id)

    if not loinc_code:
        # No LOINC mapping found — return generic observation
        return FHIRObservation(
            id=f"meas-{meas.get('measurement_id')}",
            status="final",
            code=FHIRCodeableConcept(
                coding=[
                    FHIRCoding(
                        system="http://omop.org",
                        code=str(concept_id),
                        display=meas.get("measurement_source_value", "Unknown"),
                    )
                ],
                text=meas.get("measurement_source_value", "Unknown"),
            ),
            subject=FHIRReference(reference=f"Patient/{person_id}"),
            effectiveDateTime=str(meas.get("measurement_date", ""))[:10]
            if meas.get("measurement_date")
            else None,
            valueQuantity=FHIRQuantity(
                value=meas.get("value_as_number"),
                unit=meas.get("unit_source_value", ""),
            )
            if meas.get("value_as_number") is not None
            else None,
        )

    # Get display name from reverse mapping
    from src.fhir.concept_map import OBSERVATION_TO_LOINC

    display = OBSERVATION_TO_LOINC.get(loinc_code, (loinc_code, "Unknown", ""))[1]
    unit = OBSERVATION_TO_LOINC.get(loinc_code, (loinc_code, "Unknown", ""))[2]

    return FHIRObservation(
        id=f"meas-{meas.get('measurement_id')}",
        status="final",
        code=FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://loinc.org",
                    code=loinc_code,
                    display=display,
                )
            ],
            text=display,
        ),
        subject=FHIRReference(reference=f"Patient/{person_id}"),
        effectiveDateTime=str(meas.get("measurement_date", ""))[:10]
        if meas.get("measurement_date")
        else None,
        valueQuantity=FHIRQuantity(
            value=meas.get("value_as_number"),
            unit=unit or meas.get("unit_source_value", ""),
        )
        if meas.get("value_as_number") is not None
        else None,
    )


def _condition_to_fhir_condition(
    cond: Dict[str, Any], person_id: int
) -> Optional[FHIRCondition]:
    """Convert OMOP CONDITION_OCCURRENCE to FHIR Condition."""
    concept_id = cond.get("condition_concept_id", 0)
    icd10_code = OMOP_CONDITION_TO_ICD10.get(concept_id)

    if not icd10_code:
        # Try to get from source value
        source_value = cond.get("condition_source_value", "")
        if source_value:
            icd10_code = (
                source_value.split(".")[0] if "." in source_value else source_value
            )

    if not icd10_code:
        return None

    # Get SNOMED display
    from src.fhir.concept_map import CONDITION_TO_SNOMED

    snomed_info = CONDITION_TO_SNOMED.get(icd10_code)
    display = snomed_info[1] if snomed_info else icd10_code

    codings = []
    if snomed_info:
        codings.append(
            FHIRCoding(
                system="http://snomed.info/sct",
                code=snomed_info[0],
                display=display,
            )
        )
    codings.append(
        FHIRCoding(
            system="http://hl7.org/fhir/sid/icd-10",
            code=icd10_code,
            display=display,
        )
    )

    return FHIRCondition(
        id=f"cond-{cond.get('condition_occurrence_id')}",
        code=FHIRCodeableConcept(coding=codings, text=display),
        subject=FHIRReference(reference=f"Patient/{person_id}"),
        onsetDateTime=str(cond.get("condition_start_date", ""))[:10]
        if cond.get("condition_start_date")
        else None,
    )


def _drug_to_fhir_medication(
    drug: Dict[str, Any], person_id: int
) -> Optional[FHIRMedicationStatement]:
    """Convert OMOP DRUG_EXPOSURE to FHIR MedicationStatement."""
    concept_id = drug.get("drug_concept_id", 0)
    atc_code = OMOP_DRUG_TO_ATC.get(concept_id)

    if not atc_code:
        # Try source value
        source_value = drug.get("drug_source_value", "")
        from src.fhir.concept_map import MEDICATION_TO_ATC

        for key, (atc, display, cls) in MEDICATION_TO_ATC.items():
            if key.lower() in source_value.lower():
                atc_code = atc
                break

    if not atc_code:
        return None

    from src.fhir.concept_map import MEDICATION_TO_ATC

    med_info = MEDICATION_TO_ATC.get(atc_code)
    display = med_info[1] if med_info else atc_code

    codings = [
        FHIRCoding(system="http://www.whocc.no/atc", code=atc_code, display=display),
        FHIRCoding(
            system="http://snomed.info/sct", code=str(concept_id), display=display
        ),
    ]

    return FHIRMedicationStatement(
        id=f"drug-{drug.get('drug_exposure_id')}",
        status="active" if not drug.get("drug_exposure_end_date") else "completed",
        medicationCodeableConcept=FHIRCodeableConcept(coding=codings, text=display),
        subject=FHIRReference(reference=f"Patient/{person_id}"),
        effectivePeriod={
            "start": str(drug.get("drug_exposure_start_date", ""))[:10]
            if drug.get("drug_exposure_start_date")
            else None,
            "end": str(drug.get("drug_exposure_end_date", ""))[:10]
            if drug.get("drug_exposure_end_date")
            else None,
        },
    )


def _omop_observation_to_fhir(
    obs: Dict[str, Any], person_id: int
) -> Optional[FHIRObservation]:
    """Convert OMOP OBSERVATION to FHIR Observation (for psychometrics, etc.)."""
    concept_id = obs.get("observation_concept_id", 0)
    value = obs.get("value_as_number") or obs.get("value_as_string")

    if not value:
        return None

    return FHIRObservation(
        id=f"obs-{obs.get('observation_id')}",
        status="final",
        code=FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://omop.org",
                    code=str(concept_id),
                    display=obs.get("observation_source_value", "Unknown"),
                )
            ],
            text=obs.get("observation_source_value", "Unknown"),
        ),
        subject=FHIRReference(reference=f"Patient/{person_id}"),
        effectiveDateTime=str(obs.get("observation_date", ""))[:10]
        if obs.get("observation_date")
        else None,
        valueQuantity=FHIRQuantity(value=float(value))
        if isinstance(value, (int, float))
        else None,
        valueString=str(value) if isinstance(value, str) else None,
    )
