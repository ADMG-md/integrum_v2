# Product Requirements Document (PRD)
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Status:** DRAFT (TRL 4 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Purpose

### 1.1 Purpose
This document defines the product, functional, regulatory, and system requirements for **Integrum V2**, an evidence-based Clinical Decision Support System (CDSS) for clinicians managing patients with obesity and associated cardiometabolic risks. It serves as the primary **Design Input** document required under ISO 13485 Clause 7.3.3 and FDA 21 CFR 820.30(c).

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial PRD draft consolidation based on TRL 4 specifications. |

---

## 2. Product Overview & Clinical Scope

### 2.1 Intended Use (Indicaciones de Uso)
Integrum V2 is intended to assist qualified healthcare professionals (physicians, endocrinologists, nutritionists) by processing patient physiological parameters, laboratory results, medical history, and psychometric screening to:
1. Classify patients into obesity phenotypes (e.g., Acosta Phenotypes, EOSS Staging).
2. Screen for secondary hypertension, sarcopenia, and cardiovascular/renal risks.
3. Provide evidence-based diagnostic suggestions and pharmacological safety gates.
4. Support laboratory testing stewardship to avoid over-testing.

**Contraindications/Gating:** It does not replace clinical judgment. It does not output direct therapeutic actions without clinician review.

### 2.2 User Personas
*   **Primary Clinician (Endocrinologist / GP):** Main user who inputs patient data (or retrieves it from EHR) and reviews clinical recommendations.
*   **Medical Director / Compliance Officer:** Oversees clinical safety, regulatory compliance, and QMS metrics.

---

## 3. Regulatory Compliance Requirements (SaMD Class B)

### 3.1 Standards Applied
*   **IEC 62304:** Software life-cycle processes (Class B requirements).
*   **ISO 14971:** Application of risk management to medical devices (mitigations mapped to code).
*   **ISO 13485:** Quality Management System for medical devices.
*   **FDA 21 CFR Part 11 / HIPAA:** Electronic records, digital signatures, and audit trails.

### 3.2 Product Traceability Rule
Every clinical engine algorithm MUST trace back to a specific medical citation (DOI) and trace forward to a dedicated verification test (see [traceability_matrix.md](file:///Users/antonymolinagarrido/Projects/integrum_v2/docs/qms/traceability_matrix.md)).

---

## 4. Functional Requirements

### 4.1 Intake & Demographics (T0 Flow)
*   **FR-INT-01:** The system shall capture demographics (age, biological sex, pregnancy status).
*   **FR-INT-02 (Gender Gate):** Gender-specific clinical engines (e.g., `WomensHealthMotor` or `MensHealthMotor`) must execute exclusively based on the user's biological sex.
*   **FR-INT-03:** The system must validate inputs against physiological limits (e.g., heart rate between 30 and 220 bpm, BMI between 10 and 100 kg/m²).

### 4.2 Clinical Calculation & Phenotyping (The 48 Motors)
*   **FR-ENG-01 (Acosta Phenotypes):** The system shall classify obesity into four phenotypes (Hungry Brain, Hungry Gut, Emotional Eating, Slow Burn) based on the Acosta et al. 2021 criteria.
*   **FR-ENG-02 (EOSS Staging):** The system shall stage obesity (0 to 4) using the Edmonton Obesity Staging System based on comorbidities.
*   **FR-ENG-03 (Risk Calculators):** The system shall compute cardiometabolic risks (e.g., KFRE for kidney failure, TyG-BMI for insulin resistance, CVDReclassifier for lipids).

### 4.3 Laboratory Optimization & Stewardship
*   **FR-LAB-01:** The system shall suggest clinical laboratory tests grouped by priority (High, Medium, Low) based on current ADA/AHA/KDIGO guidelines, patient age, comorbidities, and medications.
*   **FR-LAB-02:** If a high-risk medication is active (e.g., Metformin), the system must flag missing renal function tests (eGFR) as a warning.

### 4.4 Clinical Decision Support & Hard-Stops (Safety Gates)
*   **FR-SAF-01:** The system must flag contraindications for GLP-1 receptor agonists (e.g., history of Medullary Thyroid Carcinoma or MEN2).
*   **FR-SAF-02 (Suicide Risk Gating):** If a psychometric test (PHQ-9) indicates positive for suicidal ideation (Item 9 > 0), the system must trigger an immediate safety warning.

### 4.5 Interoperability Layer
*   **FR-INT-01 (FHIR R4):** The system shall support exporting patient clinical data as a FHIR R4 Bundle with standard LOINC, SNOMED, and ATC code mappings.
*   **FR-INT-02 (OMOP CDM 5.4):** The system shall support translating clinical inputs to the OMOP Common Data Model for observational research.

---

## 5. Non-Functional Requirements

### 5.1 Architecture & Performance
*   **NFR-ARC-01 (Pure Engine Logic):** To ensure testability and safety, clinical engines (`src/engines/`) must remain pure Python functions with zero database, network, or framework (FastAPI) dependencies.
*   **NFR-ARC-02 (Determinism):** Given the same patient inputs, clinical calculations must return identical outputs, verified by version hashing.
*   **NFR-PER-01 (Latency):** Calculations for all active engines on a single patient record must execute in under 200ms.

### 5.2 Security & Data Privacy
*   **NFR-SEC-01 (HIPAA Audit Log):** All interactions containing Protected Health Information (PHI) must be logged in a read-only audit database.
*   **NFR-SEC-02 (Data at Rest):** All patient identifiers must be encrypted using AES-256.

---

## 6. Verification and Validation (V&V)

*   **VV-01:** 100% of registered clinical engines must achieve 100% statement coverage via unit tests.
*   **VV-02:** Real-time compliance dashboards must monitor test runs pre-merge.
