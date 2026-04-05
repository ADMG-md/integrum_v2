"""
FHIR R4 Profile: Obesity Cardiometabolic Phenotype

Defines the minimum set of FHIR resources required to represent
a patient encounter for obesity and cardiometabolic risk assessment.

This profile extends the US Core Vital Signs profile and adds:
- Waist circumference (LOINC 8280-0)
- Calculated indices (HOMA-IR, TyG, FLI, VAI, etc.)
- Psychometric assessments (PHQ-9, GAD-7, TFEQ-R18, Athens, FNQ)
- Medication statements with ATC coding
- Condition diagnoses with SNOMED-CT/ICD-10

References:
- US Core Vital Signs: http://hl7.org/fhir/us/vitals/
- HL7 FHIR R4: http://hl7.org/fhir/R4/
- LOINC: https://loinc.org/
"""

OBESITY_CARDIOMETABOLIC_PROFILE = {
    "resourceType": "StructureDefinition",
    "url": "http://integrum.ai/fhir/StructureDefinition/obesity-cardiometabolic-phenotype",
    "name": "ObesityCardiometabolicPhenotype",
    "status": "draft",
    "date": "2026-04-04",
    "publisher": "Integrum V2",
    "description": "Minimum dataset for obesity and cardiometabolic risk phenotyping",
    "fhirVersion": "4.0.1",
    "kind": "resource",
    "abstract": False,
    "type": "Bundle",
    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Bundle",
    "derivation": "constraint",
    "differential": {
        "element": [
            {
                "id": "Bundle",
                "path": "Bundle",
                "short": "Obesity Cardiometabolic Phenotype Bundle",
                "definition": "A collection of FHIR resources representing a complete obesity/cardiometabolic assessment",
            },
            {
                "id": "Bundle.type",
                "path": "Bundle.type",
                "min": 1,
                "fixedCode": "collection",
            },
            {
                "id": "Bundle.entry",
                "path": "Bundle.entry",
                "min": 3,
                "slicing": {
                    "discriminator": [{"type": "type", "path": "resource"}],
                    "rules": "open",
                },
                "comment": "Must include at least Patient, Encounter, and one Observation",
            },
            {
                "id": "Bundle.entry:patient",
                "path": "Bundle.entry",
                "sliceName": "patient",
                "min": 1,
                "max": "1",
            },
            {
                "id": "Bundle.entry:encounter",
                "path": "Bundle.entry",
                "sliceName": "encounter",
                "min": 1,
                "max": "1",
            },
            {
                "id": "Bundle.entry:bmi",
                "path": "Bundle.entry",
                "sliceName": "bmi",
                "min": 0,
                "max": "1",
                "comment": "BMI Observation (LOINC 39156-5)",
            },
            {
                "id": "Bundle.entry:waist",
                "path": "Bundle.entry",
                "sliceName": "waist",
                "min": 0,
                "max": "1",
                "comment": "Waist circumference Observation (LOINC 8280-0)",
            },
            {
                "id": "Bundle.entry:bloodPressure",
                "path": "Bundle.entry",
                "sliceName": "bloodPressure",
                "min": 0,
                "max": "1",
                "comment": "Blood pressure Observation (LOINC 85354-9)",
            },
            {
                "id": "Bundle.entry:glucose",
                "path": "Bundle.entry",
                "sliceName": "glucose",
                "min": 0,
                "max": "1",
                "comment": "Fasting glucose Observation (LOINC 1558-6)",
            },
            {
                "id": "Bundle.entry:hba1c",
                "path": "Bundle.entry",
                "sliceName": "hba1c",
                "min": 0,
                "max": "1",
                "comment": "HbA1c Observation (LOINC 4548-4)",
            },
            {
                "id": "Bundle.entry:lipidPanel",
                "path": "Bundle.entry",
                "sliceName": "lipidPanel",
                "min": 0,
                "max": "*",
                "comment": "Lipid panel Observations (TC, HDL, LDL, TG)",
            },
            {
                "id": "Bundle.entry:calculatedIndices",
                "path": "Bundle.entry",
                "sliceName": "calculatedIndices",
                "min": 0,
                "max": "*",
                "comment": "Calculated indices: HOMA-IR, TyG, FLI, VAI, NFS, etc.",
            },
            {
                "id": "Bundle.entry:conditions",
                "path": "Bundle.entry",
                "sliceName": "conditions",
                "min": 0,
                "max": "*",
                "comment": "Condition diagnoses with SNOMED-CT/ICD-10",
            },
            {
                "id": "Bundle.entry:medications",
                "path": "Bundle.entry",
                "sliceName": "medications",
                "min": 0,
                "max": "*",
                "comment": "MedicationStatement with ATC coding",
            },
            {
                "id": "Bundle.entry:questionnaireResponses",
                "path": "Bundle.entry",
                "sliceName": "questionnaireResponses",
                "min": 0,
                "max": "*",
                "comment": "Psychometric QuestionnaireResponses (PHQ-9, GAD-7, etc.)",
            },
        ]
    },
}

# Required LOINC codes for the phenotype
REQUIRED_OBSERVATIONS = {
    "bmi": "39156-5",
    "weight": "29463-7",
    "height": "8302-2",
    "waist": "8280-0",
    "systolic_bp": "8480-6",
    "diastolic_bp": "8462-4",
    "glucose_fasting": "1558-6",
    "hba1c": "4548-4",
    "total_cholesterol": "2093-3",
    "hdl": "2085-9",
    "ldl": "13457-7",
    "triglycerides": "2571-8",
}

# Recommended (nice to have)
RECOMMENDED_OBSERVATIONS = {
    "insulin_fasting": "20448-7",
    "ast": "1920-8",
    "alt": "1742-6",
    "ggt": "2324-2",
    "creatinine": "2160-0",
    "uric_acid": "3084-1",
    "hs_crp": "30522-7",
    "ferritin": "2276-4",
    "tsh": "11579-0",
    "ft4": "3024-7",
    "apob": "13456-9",
    "apoa1": "13455-1",
    "lpa": "35199-8",
    "vitamin_d": "1989-3",
    "vitamin_b12": "2132-9",
}

# Calculated indices (derived from required observations)
CALCULATED_INDICES = {
    "homa_ir": "89242-2",
    "tyg_index": "89243-0",
    "tyg_bmi": "89244-8",
    "fli": "89245-5",
    "vai": "89246-3",
    "nfs": "89247-1",
    "egfr": "33914-3",
    "uacr": "14959-1",
    "pulse_pressure": "8479-8",
    "remnant_cholesterol": "89248-9",
    "apob_apoa1_ratio": "89249-7",
}

# Psychometric questionnaires
PSYCHOMETRIC_QUESTIONNAIRES = {
    "phq9": "44249-1",
    "gad7": "69737-5",
    "tf_eq_r18": "89250-5",
    "athens": "72133-2",
    "fnq": "89251-3",
}
