"""
FHIR ConceptMap: Local observation codes → LOINC / SNOMED-CT / ATC

This module provides bidirectional mapping between Integrum V2 internal codes
and standard healthcare terminologies (LOINC for observations, SNOMED-CT for
conditions, ATC for medications).

References:
- HL7 FHIR R4: http://hl7.org/fhir/R4/
- LOINC: https://loinc.org/
- SNOMED-CT: https://www.snomed.org/
- ATC: https://www.whocc.no/atc_ddd_index/
- OMOP CDM 5.4: https://ohdsi.github.io/CommonDataModel/
"""

from typing import Dict, Optional, Tuple

# ============================================================
# Observation Code Mapping (Integrum → LOINC)
# ============================================================

OBSERVATION_TO_LOINC: Dict[str, Tuple[str, str, str]] = {
    # code: (loinc_code, display_name, unit)
    # Anthropometry
    "29463-7": ("29463-7", "Body weight", "kg"),
    "8302-2": ("8302-2", "Body height", "cm"),
    "WAIST-001": ("8280-0", "Waist circumference", "cm"),
    "HIP-001": ("62401-3", "Hip circumference", "cm"),
    "W-001": ("29463-7", "Body weight", "kg"),
    "H-001": ("8302-2", "Body height", "cm"),
    # Vital Signs
    "8480-6": ("8480-6", "Systolic blood pressure", "mmHg"),
    "8462-4": ("8462-4", "Diastolic blood pressure", "mmHg"),
    # Body Composition
    "MMA-001": ("90590-4", "Appendicular lean mass", "kg"),
    "MUSCLE-KG": ("72072-2", "Lean body mass", "kg"),
    "BIA-FFM-KG": ("72072-2", "Fat free mass", "kg"),
    "ARM-CIRC": ("26228-0", "Mid-upper arm circumference", "cm"),
    "CALF-CIRC": ("26229-8", "Calf circumference", "cm"),
    # Metabolic
    "GLUCOSE-001": ("2339-0", "Glucose [Mass/volume] in Blood", "mg/dL"),
    "HBA1C-001": ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "%"),
    "INSULIN-001": ("20448-7", "Insulin [Units/volume] in Serum or Plasma", "μU/mL"),
    # Lipid Panel
    "TC-001": ("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "mg/dL"),
    "HDL-001": ("2085-9", "HDL Cholesterol", "mg/dL"),
    "LDL-001": ("13457-7", "LDL Cholesterol", "mg/dL"),
    "TG-001": ("2571-8", "Triglycerides", "mg/dL"),
    "APOB-001": ("13456-9", "Apolipoprotein B", "mg/dL"),
    "LPA-001": ("35199-8", "Lipoprotein(a)", "mg/dL"),
    "APOA1-001": ("13455-1", "Apolipoprotein A1", "mg/dL"),
    # Liver Function
    "AST-001": ("1920-8", "AST", "U/L"),
    "ALT-001": ("1742-6", "ALT", "U/L"),
    "GGT-001": ("2324-2", "GGT", "U/L"),
    "ALKPHOS-001": ("6768-6", "Alkaline phosphatase", "U/L"),
    # Renal
    "CREAT-001": ("2160-0", "Creatinine", "mg/dL"),
    "UA-001": ("3084-1", "Uric acid", "mg/dL"),
    "UACR-001": ("14959-1", "Albumin/Creatinine ratio in Urine", "mg/g"),
    # CBC
    "WBC-001": ("26499-4", "WBC", "K/μL"),
    "LYMPH-001": ("26474-7", "Lymphocytes", "%"),
    "NEUT-001": ("26512-4", "Neutrophils", "%"),
    "MCV-001": ("787-2", "MCV", "fL"),
    "RDW-001": ("788-0", "RDW", "%"),
    "PLT-001": ("777-3", "Platelets", "K/μL"),
    # Inflammation
    "CRP-001": ("30522-7", "hs-CRP", "mg/L"),
    "FER-001": ("2276-4", "Ferritin", "ng/mL"),
    # Endocrine
    "TSH-001": ("11579-0", "TSH", "μIU/mL"),
    "FT4-001": ("3024-7", "Free T4", "ng/dL"),
    "FT3-001": ("3053-3", "Free T3", "pg/mL"),
    "SHBG-001": ("21882-6", "SHBG", "nmol/L"),
    "CORTISOL-001": ("2143-1", "Cortisol", "μg/dL"),
    "TESTO-001": ("2986-8", "Testosterone", "ng/dL"),
    # Micronutrients
    "VITD-001": ("1989-3", "Vitamin D 25-OH", "ng/mL"),
    "VITB12-001": ("2132-9", "Vitamin B12", "pg/mL"),
    # Functional Tests
    "5XSTS-SEC": ("89243-0", "5 times sit to stand test time", "s"),
    "GRIP-STR-R": ("89244-8", "Grip strength right hand", "kg"),
    "GRIP-STR-L": ("89245-5", "Grip strength left hand", "kg"),
    "GAIT-SPEED": ("89246-3", "Gait speed", "m/s"),
    "SARCF-SCORE": ("89247-1", "SARC-F score", "{score}"),
    # Psychometrics
    "PHQ9-SCORE": ("44249-1", "PHQ-9 total score", "{score}"),
    "GAD7-SCORE": ("69737-5", "GAD-7 total score", "{score}"),
    "ATENAS-001": ("72133-2", "Athens Insomnia Scale", "{score}"),
    # Hypertension workup
    "ALDO-001": ("1762-0", "Aldosterone", "ng/dL"),
    "RENIN-001": ("2889-4", "Renin", "ng/mL/h"),
}

# Reverse mapping: LOINC → Integrum code
LOINC_TO_OBSERVATION: Dict[str, str] = {
    loinc: code for code, (loinc, _, _) in OBSERVATION_TO_LOINC.items()
}

# ============================================================
# Condition Code Mapping (ICD-10 → SNOMED-CT)
# ============================================================

CONDITION_TO_SNOMED: Dict[str, Tuple[str, str]] = {
    # code: (snomed_code, display_name)
    # Obesity
    "E66": ("414916001", "Obesity"),
    "E66.0": ("414916001", "Obesity due to excess calories"),
    "E66.1": ("414916001", "Drug-induced obesity"),
    "E66.2": ("414916001", "Extreme obesity with alveolar hypoventilation"),
    "E66.9": ("414916001", "Obesity, unspecified"),
    # Diabetes
    "E11": ("44054006", "Type 2 diabetes mellitus"),
    "E11.9": ("44054006", "Type 2 diabetes mellitus without complications"),
    "E11.2": ("44054006", "Type 2 diabetes mellitus with kidney complications"),
    "E11.3": ("44054006", "Type 2 diabetes mellitus with ophthalmic complications"),
    "E11.4": ("44054006", "Type 2 diabetes mellitus with neurological complications"),
    "E11.5": ("44054006", "Type 2 diabetes mellitus with circulatory complications"),
    # Hypertension
    "I10": ("38341003", "Essential hypertension"),
    "I11": ("38341003", "Hypertensive heart disease"),
    # Cardiovascular
    "I25": ("414545008", "Ischemic heart disease"),
    "I25.1": ("414545008", "Atherosclerotic heart disease"),
    "I50": ("84114007", "Heart failure"),
    "I50.9": ("84114007", "Heart failure, unspecified"),
    "I63": ("422504002", "Ischemic stroke"),
    # Metabolic
    "E78": ("267431005", "Disorder of lipoprotein metabolism"),
    "E78.0": ("13644009", "Pure hypercholesterolemia"),
    "E78.1": ("55827005", "Pure hyperglyceridemia"),
    "E78.2": ("410429000", "Mixed hyperlipidemia"),
    # Liver
    "K76": ("235856003", "Liver disease"),
    "K76.0": ("235856003", "Fatty liver"),
    # Kidney
    "N18": ("709044004", "Chronic kidney disease"),
    "N18.3": ("709044004", "Chronic kidney disease stage 3"),
    "N18.4": ("709044004", "Chronic kidney disease stage 4"),
    "N18.5": ("709044004", "Chronic kidney disease stage 5"),
    "N18.6": ("709044004", "End stage renal disease"),
    # Endocrine
    "E03": ("40930008", "Hypothyroidism"),
    "E03.9": ("40930008", "Hypothyroidism, unspecified"),
    # Other
    "E79": ("53651007", "Gout"),
    "G47": ("115351000", "Sleep apnea"),
    "G47.33": ("78275009", "Obstructive sleep apnea"),
    "E28": ("237063007", "Polycystic ovarian syndrome"),
    "F32": ("35489007", "Depressive episode"),
    "F32.9": ("35489007", "Depression, unspecified"),
    "F41": ("197480006", "Anxiety disorder"),
    "F41.9": ("197480006", "Anxiety, unspecified"),
    "C73": ("363418001", "Malignant neoplasm of thyroid gland"),
    "K85": ("54520002", "Acute pancreatitis"),
    "F50": ("190891000", "Eating disorder"),
}

# ============================================================
# Medication Code Mapping (Integrum → ATC)
# ============================================================

MEDICATION_TO_ATC: Dict[str, Tuple[str, str, str]] = {
    # code: (atc_code, display_name, atc_class)
    # GLP-1 RA
    "SEMAGLUTIDE": ("A10BJ06", "Semaglutide", "GLP-1 receptor agonist"),
    "TIRZEPATIDE": ("A10BJ07", "Tirzepatide", "GIP/GLP-1 receptor agonist"),
    "LIRAGLUTIDE": ("A10BJ02", "Liraglutide", "GLP-1 receptor agonist"),
    "DULAGLUTIDE": ("A10BJ04", "Dulaglutide", "GLP-1 receptor agonist"),
    "EXENATIDE": ("A10BJ01", "Exenatide", "GLP-1 receptor agonist"),
    # SGLT2i
    "EMPAGLIFLOZIN": ("A10BK03", "Empagliflozin", "SGLT2 inhibitor"),
    "DAPAGLIFLOZIN": ("A10BK01", "Dapagliflozin", "SGLT2 inhibitor"),
    "CANAGLIFLOZIN": ("A10BK02", "Canagliflozin", "SGLT2 inhibitor"),
    "ERTUGLIFLOZIN": ("A10BK04", "Ertugliflozin", "SGLT2 inhibitor"),
    # Biguanides
    "METFORMIN": ("A10BA02", "Metformin", "Biguanide"),
    # DPP-4i
    "SITAGLIPTIN": ("A10BH01", "Sitagliptin", "DPP-4 inhibitor"),
    "LINAGLIPTIN": ("A10BH05", "Linagliptin", "DPP-4 inhibitor"),
    "SAXAGLIPTIN": ("A10BH03", "Saxagliptin", "DPP-4 inhibitor"),
    # TZDs
    "PIOGLITAZONE": ("A10BG03", "Pioglitazone", "Thiazolidinedione"),
    "ROSIGLITAZONE": ("A10BG02", "Rosiglitazone", "Thiazolidinedione"),
    # Sulfonylureas
    "GLIPIZIDE": ("A10BB07", "Glipizide", "Sulfonylurea"),
    "GLYBURIDE": ("A10BB01", "Glyburide", "Sulfonylurea"),
    "GLIMEPIRIDE": ("A10BB12", "Glimepiride", "Sulfonylurea"),
    # Insulins
    "INSULIN_GLARGINE": ("A10AE04", "Insulin glargine", "Long-acting insulin"),
    "INSULIN_LISPRO": ("A10AB04", "Insulin lispro", "Rapid-acting insulin"),
    "INSULIN_ASPART": ("A10AB05", "Insulin aspart", "Rapid-acting insulin"),
    "INSULIN_DETEmir": ("A10AE05", "Insulin detemir", "Long-acting insulin"),
    "INSULIN_DEGLUDEC": ("A10AE06", "Insulin degludec", "Ultra-long-acting insulin"),
    # Statins
    "ATORVASTATIN": ("C10AA05", "Atorvastatin", "HMG CoA reductase inhibitor"),
    "ROSUVASTATIN": ("C10AA07", "Rosuvastatin", "HMG CoA reductase inhibitor"),
    "SIMVASTATIN": ("C10AA01", "Simvastatin", "HMG CoA reductase inhibitor"),
    "PRAVASTATIN": ("C10AA03", "Pravastatin", "HMG CoA reductase inhibitor"),
    # Other lipid
    "EZETIMIBE": ("C10AX09", "Ezetimibe", "Cholesterol absorption inhibitor"),
    "FENOFIBRATE": ("C10AB05", "Fenofibrate", "Fibrate"),
    # ACEi
    "LISINOPRIL": ("C09AA03", "Lisinopril", "ACE inhibitor"),
    "ENALAPRIL": ("C09AA02", "Enalapril", "ACE inhibitor"),
    "RAMIPRIL": ("C09AA05", "Ramipril", "ACE inhibitor"),
    # ARBs
    "LOSARTAN": ("C09CA01", "Losartan", "ARB"),
    "VALSARTAN": ("C09CA03", "Valsartan", "ARB"),
    "IRBESARTAN": ("C09CA04", "Irbesartan", "ARB"),
    "TELMISARTAN": ("C09CA07", "Telmisartan", "ARB"),
    # Beta-blockers
    "METOPROLOL": ("C07AB02", "Metoprolol", "Beta-blocker (selective)"),
    "ATENOLOL": ("C07AB03", "Atenolol", "Beta-blocker (selective)"),
    "CARVEDILOL": ("C07AG02", "Carvedilol", "Beta-blocker (non-selective)"),
    # CCB
    "AMLODIPINE": ("C08CA01", "Amlodipine", "Calcium channel blocker"),
    "NIFEDIPINE": ("C08CA05", "Nifedipine", "Calcium channel blocker"),
    "DILTIAZEM": ("C08DB01", "Diltiazem", "Calcium channel blocker"),
    "VERAPAMIL": ("C08DA01", "Verapamil", "Calcium channel blocker"),
    # Diuretics
    "FUROSEMIDE": ("C03CA01", "Furosemide", "Loop diuretic"),
    "HYDROCHLOROTHIAZIDE": ("C03AA03", "Hydrochlorothiazide", "Thiazide"),
    "SPIRONOLACTONE": ("C03DA01", "Spironolactone", "Potassium-sparing diuretic"),
    # Anti-obesity
    "PHENTERMINE": ("A08AA01", "Phentermine", "Sympathomimetic"),
    "ORLISTAT": ("A08AB01", "Orlistat", "Lipase inhibitor"),
    # Thyroid
    "LEVOTHYROXINE": ("H03AA01", "Levothyroxine", "Thyroid hormone"),
    # Antipsychotics
    "OLANZAPINE": ("N05AH03", "Olanzapine", "Atypical antipsychotic"),
    "QUETIAPINE": ("N05AH04", "Quetiapine", "Atypical antipsychotic"),
    "RISPERIDONE": ("N05AX08", "Risperidone", "Atypical antipsychotic"),
    "CLOZAPINE": ("N05AH02", "Clozapine", "Atypical antipsychotic"),
    "ARIPRAZOLE": ("N05AX12", "Aripiprazole", "Atypical antipsychotic"),
    # Antidepressants
    "FLUOXETINE": ("N06AB03", "Fluoxetine", "SSRI"),
    "SERTRALINE": ("N06AB06", "Sertraline", "SSRI"),
    "CITALOPRAM": ("N06AB04", "Citalopram", "SSRI"),
    "ESCITALOPRAM": ("N06AB10", "Escitalopram", "SSRI"),
    "VENLAFAXINE": ("N06AX16", "Venlafaxine", "SNRI"),
    "DULOXETINE": ("N06AX21", "Duloxetine", "SNRI"),
    "BUPROPION": ("N06AX12", "Bupropion", "Atypical antidepressant"),
    "MIRTAZAPINE": ("N06AX11", "Mirtazapine", "Atypical antidepressant"),
    # Anticonvulsants
    "GABAPENTIN": ("N03AX12", "Gabapentin", "Gabapentinoid"),
    "PREGABALIN": ("N03AX16", "Pregabalin", "Gabapentinoid"),
    "VALPROATE": ("N03AG01", "Valproate", "Anticonvulsant"),
    "TOPRAMATE": ("N03AX11", "Topiramate", "Anticonvulsant"),
    "CARBAMAZEPINE": ("N03AF01", "Carbamazepine", "Anticonvulsant"),
    "LAMOTRIGINE": ("N03AX09", "Lamotrigine", "Anticonvulsant"),
    "LEVETIRACETAM": ("N03AX14", "Levetiracetam", "Anticonvulsant"),
    # Corticosteroids
    "PREDNISONE": ("H02AB07", "Prednisone", "Corticosteroid"),
    "DEXAMETHASONE": ("H02AB02", "Dexamethasone", "Corticosteroid"),
    # PPI
    "OMEPRAZOLE": ("A02BC01", "Omeprazole", "Proton pump inhibitor"),
    "PANTOPRAZOLE": ("A02BC02", "Pantoprazole", "Proton pump inhibitor"),
    # Antiplatelet
    "ASPIRIN": ("B01AC06", "Aspirin", "Antiplatelet"),
    "CLOPIDOGREL": ("B01AC04", "Clopidogrel", "Antiplatelet"),
    # Anticoagulant
    "APIXABAN": ("B01AF02", "Apixaban", "DOAC"),
    "RIVAROXABAN": ("B01AF01", "Rivaroxaban", "DOAC"),
    "WARFARIN": ("B01AA03", "Warfarin", "Vitamin K antagonist"),
}


def get_loinc_for_code(code: str) -> Optional[Tuple[str, str, str]]:
    """Get LOINC code, display name, and unit for an Integrum observation code."""
    return OBSERVATION_TO_LOINC.get(code)


def get_integrum_code_for_loinc(loinc: str) -> Optional[str]:
    """Get Integrum observation code for a LOINC code."""
    return LOINC_TO_OBSERVATION.get(loinc)


def get_snomed_for_icd10(icd10: str) -> Optional[Tuple[str, str]]:
    """Get SNOMED-CT code and display name for an ICD-10 condition code."""
    # Try exact match first
    if icd10 in CONDITION_TO_SNOMED:
        return CONDITION_TO_SNOMED[icd10]
    # Try prefix match (e.g., "E66.0" → "E66")
    base = icd10.split(".")[0]
    if base in CONDITION_TO_SNOMED:
        return CONDITION_TO_SNOMED[base]
    return None


def get_atc_for_medication(name: str) -> Optional[Tuple[str, str, str]]:
    """Get ATC code, display name, and class for a medication name."""
    name_upper = name.upper().replace(" ", "_")
    if name_upper in MEDICATION_TO_ATC:
        return MEDICATION_TO_ATC[name_upper]
    # Try partial match
    for key, value in MEDICATION_TO_ATC.items():
        if key in name_upper or name_upper in key:
            return value
    return None
