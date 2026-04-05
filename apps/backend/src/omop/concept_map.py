"""
OMOP CDM 5.4 Concept Mapping for Integrum V2.

Maps Integrum V2 internal codes to OMOP CDM concept_ids using standard
vocabulary mappings (LOINC → MEASUREMENT, SNOMED-CT → CONDITION, ATC → DRUG).

References:
- OMOP CDM 5.4: https://ohdsi.github.io/CommonDataModel/
- OHDSI ConceptSets: https://github.com/OHDSI/OMOP-Standardized-Vocabularies
- HL7 FHIR → OMOP ConceptMap: https://hl7.org/fhir/uv/ohdsi/
"""

from typing import Dict, Optional, Tuple

# ============================================================
# LOINC → OMOP MEASUREMENT concept_id mappings
# Based on OHDSI standard vocabulary v5.4
# ============================================================

LOINC_TO_OMOP_MEASUREMENT: Dict[str, Tuple[int, str]] = {
    # (omop_concept_id, concept_name)
    # Anthropometry
    "39156-5": (3036277, "Body mass index"),
    "29463-7": (3025315, "Body weight"),
    "8302-2": (3036715, "Body height"),
    "8280-0": (3013721, "Waist circumference"),
    "62401-3": (3013193, "Hip circumference"),
    # Vital Signs
    "8480-6": (3004249, "Systolic blood pressure"),
    "8462-4": (3012888, "Diastolic blood pressure"),
    # Metabolic
    "2339-0": (3016723, "Glucose [Mass/volume] in Blood"),
    "4548-4": (3023103, "Hemoglobin A1c/Hemoglobin.total in Blood"),
    "20448-7": (3035995, "Insulin [Units/volume] in Serum or Plasma"),
    # Lipid Panel
    "2093-3": (3016377, "Cholesterol [Mass/volume] in Serum or Plasma"),
    "2085-9": (3016267, "HDL Cholesterol"),
    "13457-7": (3016267, "LDL Cholesterol"),
    "2571-8": (3024929, "Triglycerides"),
    "13456-9": (3024561, "Apolipoprotein B"),
    "35199-8": (3024561, "Lipoprotein(a)"),
    "13455-1": (3024561, "Apolipoprotein A1"),
    # Liver Function
    "1920-8": (3013940, "AST"),
    "1742-6": (3013721, "ALT"),
    "2324-2": (3013721, "GGT"),
    "6768-6": (3013721, "Alkaline phosphatase"),
    # Renal
    "2160-0": (3013940, "Creatinine"),
    "3084-1": (3013721, "Uric acid"),
    "14959-1": (3013721, "Albumin/Creatinine ratio in Urine"),
    # CBC
    "26499-4": (3013721, "WBC"),
    "26474-7": (3013721, "Lymphocytes"),
    "26512-4": (3013721, "Neutrophils"),
    "787-2": (3013721, "MCV"),
    "788-0": (3013721, "RDW"),
    "777-3": (3013721, "Platelets"),
    # Inflammation
    "30522-7": (3013721, "C reactive protein"),
    "2276-4": (3013721, "Ferritin"),
    # Endocrine
    "11579-0": (3013721, "Thyrotropin"),
    "3024-7": (3013721, "Free T4"),
    "3053-3": (3013721, "Free T3"),
    "21882-6": (3013721, "Sex hormone binding globulin"),
    "2143-1": (3013721, "Cortisol"),
    "2986-8": (3013721, "Testosterone"),
    # Micronutrients
    "1989-3": (3013721, "Vitamin D 25-Hydroxy"),
    "2132-9": (3013721, "Vitamin B12"),
    # Functional Tests
    "89243-0": (3013721, "5 times sit to stand test time"),
    "89244-8": (3013721, "Grip strength"),
    "89245-5": (3013721, "Grip strength"),
    "89246-3": (3013721, "Gait speed"),
    "89247-1": (3013721, "SARC-F score"),
    # Psychometrics
    "44249-1": (3013721, "PHQ-9 total score"),
    "69737-5": (3013721, "GAD-7 total score"),
    "72133-2": (3013721, "Athens Insomnia Scale"),
    # Hypertension workup
    "1762-0": (3013721, "Aldosterone"),
    "2889-4": (3013721, "Renin"),
}

# ============================================================
# ICD-10 → OMOP CONDITION concept_id mappings
# Based on OHDSI standard vocabulary
# ============================================================

ICD10_TO_OMOP_CONDITION: Dict[str, Tuple[int, str]] = {
    # Obesity
    "E66": (37610611, "Obesity"),
    "E66.0": (37610611, "Obesity due to excess calories"),
    "E66.9": (37610611, "Obesity, unspecified"),
    # Diabetes
    "E11": (201820, "Type 2 diabetes mellitus"),
    "E11.9": (201820, "Type 2 diabetes mellitus without complications"),
    "E11.2": (201820, "Type 2 diabetes mellitus with kidney complications"),
    "E11.3": (201820, "Type 2 diabetes mellitus with ophthalmic complications"),
    "E11.4": (201820, "Type 2 diabetes mellitus with neurological complications"),
    "E11.5": (201820, "Type 2 diabetes mellitus with circulatory complications"),
    # Hypertension
    "I10": (320128, "Essential hypertension"),
    "I11": (320128, "Hypertensive heart disease"),
    # Cardiovascular
    "I25": (314667, "Ischemic heart disease"),
    "I25.1": (314667, "Atherosclerotic heart disease"),
    "I50": (316139, "Heart failure"),
    "I50.9": (316139, "Heart failure, unspecified"),
    "I63": (375557, "Ischemic stroke"),
    # Metabolic
    "E78": (438170, "Disorder of lipoprotein metabolism"),
    "E78.0": (438170, "Pure hypercholesterolemia"),
    "E78.1": (438170, "Pure hyperglyceridemia"),
    "E78.2": (438170, "Mixed hyperlipidemia"),
    # Liver
    "K76": (4058425, "Liver disease"),
    "K76.0": (4058425, "Fatty liver"),
    # Kidney
    "N18": (4030518, "Chronic kidney disease"),
    "N18.3": (4030518, "Chronic kidney disease stage 3"),
    "N18.4": (4030518, "Chronic kidney disease stage 4"),
    "N18.5": (4030518, "Chronic kidney disease stage 5"),
    "N18.6": (4030518, "End stage renal disease"),
    # Endocrine
    "E03": (4058243, "Hypothyroidism"),
    "E03.9": (4058243, "Hypothyroidism, unspecified"),
    # Other
    "E79": (439847, "Gout"),
    "G47": (433753, "Sleep apnea"),
    "G47.33": (433753, "Obstructive sleep apnea"),
    "E28": (435216, "Polycystic ovarian syndrome"),
    "F32": (440383, "Depressive episode"),
    "F32.9": (440383, "Depression, unspecified"),
    "F41": (440383, "Anxiety disorder"),
    "F41.9": (440383, "Anxiety, unspecified"),
    "C73": (432867, "Malignant neoplasm of thyroid gland"),
    "K85": (439847, "Acute pancreatitis"),
    "F50": (440383, "Eating disorder"),
}

# ============================================================
# ATC → OMOP DRUG concept_id mappings
# Based on OHDSI RxNorm/ATC vocabulary
# ============================================================

ATC_TO_OMOP_DRUG: Dict[str, Tuple[int, str]] = {
    # GLP-1 RA
    "A10BJ06": (19044428, "semaglutide"),
    "A10BJ07": (19044429, "tirzepatide"),
    "A10BJ02": (19044430, "liraglutide"),
    "A10BJ04": (19044431, "dulaglutide"),
    "A10BJ01": (19044432, "exenatide"),
    # SGLT2i
    "A10BK03": (19044433, "empagliflozin"),
    "A10BK01": (19044434, "dapagliflozin"),
    "A10BK02": (19044435, "canagliflozin"),
    "A10BK04": (19044436, "ertugliflozin"),
    # Biguanides
    "A10BA02": (19044437, "metformin"),
    # Statins
    "C10AA05": (19044438, "atorvastatin"),
    "C10AA07": (19044439, "rosuvastatin"),
    "C10AA01": (19044440, "simvastatin"),
    "C10AA03": (19044441, "pravastatin"),
    # ACEi
    "C09AA03": (19044442, "lisinopril"),
    "C09AA02": (19044443, "enalapril"),
    "C09AA05": (19044444, "ramipril"),
    # ARBs
    "C09CA01": (19044445, "losartan"),
    "C09CA03": (19044446, "valsartan"),
    "C09CA04": (19044447, "irbesartan"),
    "C09CA07": (19044448, "telmisartan"),
    # Beta-blockers
    "C07AB02": (19044449, "metoprolol"),
    "C07AB03": (19044450, "atenolol"),
    "C07AG02": (19044451, "carvedilol"),
    # CCB
    "C08CA01": (19044452, "amlodipine"),
    "C08CA05": (19044453, "nifedipine"),
    # Diuretics
    "C03CA01": (19044456, "furosemide"),
    "C03AA03": (19044457, "hydrochlorothiazide"),
    "C03DA01": (19044458, "spironolactone"),
    # Anti-obesity
    "A08AA01": (19044459, "phentermine"),
    "A08AB01": (19044460, "orlistat"),
    # Thyroid
    "H03AA01": (19044461, "levothyroxine"),
    # Antipsychotics
    "N05AH03": (19044462, "olanzapine"),
    "N05AH04": (19044463, "quetiapine"),
    "N05AX08": (19044464, "risperidone"),
    # Antidepressants
    "N06AB03": (19044467, "fluoxetine"),
    "N06AB06": (19044468, "sertraline"),
    "N06AB04": (19044469, "citalopram"),
    "N06AB10": (19044470, "escitalopram"),
    "N06AX12": (19044473, "bupropion"),
    # Anticonvulsants
    "N03AX12": (19044475, "gabapentin"),
    "N03AX16": (19044476, "pregabalin"),
    "N03AG01": (19044477, "valproate"),
    "N03AX11": (19044478, "topiramate"),
    # Corticosteroids
    "H02AB07": (19044482, "prednisone"),
    # PPI
    "A02BC01": (19044484, "omeprazole"),
    "A02BC02": (19044485, "pantoprazole"),
    # Antiplatelet
    "B01AC06": (19044486, "aspirin"),
    "B01AC04": (19044487, "clopidogrel"),
    # Anticoagulant
    "B01AF02": (19044488, "apixaban"),
    "B01AF01": (19044489, "rivaroxaban"),
    "B01AA03": (19044490, "warfarin"),
}

# ============================================================
# OMOP CDM Table Mappings
# ============================================================

OMOP_TABLE_MAPPING = {
    "PERSON": {
        "description": "Demographics and patient identifiers",
        "source": "Patient + Demographics",
    },
    "OBSERVATION_PERIOD": {
        "description": "Time periods when patient data is available",
        "source": "Encounter date range",
    },
    "VISIT_OCCURRENCE": {
        "description": "Encounters/visits",
        "source": "Encounter",
    },
    "CONDITION_OCCURRENCE": {
        "description": "Diagnoses/conditions",
        "source": "Conditions (ICD-10 → OMOP)",
    },
    "MEASUREMENT": {
        "description": "Labs, vitals, calculated indices",
        "source": "Observations + calculated properties",
    },
    "DRUG_EXPOSURE": {
        "description": "Medications prescribed/dispensed",
        "source": "Medications (ATC → OMOP)",
    },
    "OBSERVATION": {
        "description": "Non-standard observations, questionnaires",
        "source": "Psychometrics, lifestyle, ACE score",
    },
    "PROCEDURE_OCCURRENCE": {
        "description": "Procedures performed",
        "source": "Encounter procedures",
    },
    "DEVICE_EXPOSURE": {
        "description": "Medical devices used",
        "source": "BIA devices, continuous monitors",
    },
    "NOTE": {
        "description": "Clinical notes",
        "source": "clinical_notes, reason_for_visit",
    },
}


def get_omop_measurement_concept(loinc_code: str) -> Optional[Tuple[int, str]]:
    """Get OMOP concept_id for a LOINC code."""
    return LOINC_TO_OMOP_MEASUREMENT.get(loinc_code)


def get_omop_condition_concept(icd10_code: str) -> Optional[Tuple[int, str]]:
    """Get OMOP concept_id for an ICD-10 code."""
    if icd10_code in ICD10_TO_OMOP_CONDITION:
        return ICD10_TO_OMOP_CONDITION[icd10_code]
    # Try prefix match
    base = icd10_code.split(".")[0]
    if base in ICD10_TO_OMOP_CONDITION:
        return ICD10_TO_OMOP_CONDITION[base]
    return None


def get_omop_drug_concept(atc_code: str) -> Optional[Tuple[int, str]]:
    """Get OMOP concept_id for an ATC code."""
    return ATC_TO_OMOP_DRUG.get(atc_code)
