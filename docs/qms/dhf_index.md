# Design History File (DHF) Index
**Project:** Integrum V2
**Standard:** ISO 13485 Clause 7.3.10 / 21 CFR 820.30(j)

## 1. Design Planning & Lifecycle
- [ROADMAP.md](../../ROADMAP.md): Tactical development missions.
- [Software Development Plan (SDP)](./software_development_plan.md): Agile SDLC clinical gates, Git branching strategy, and software configuration management.
- **Archived Blueprints:** Completed technical specifications located in [docs/archive/](../archive/).

## 2. Design Inputs & Product Specifications
- [Product Requirements Document (PRD)](./product_requirements_document.md): Intended use, primary user personas, regulatory boundaries, and product features.
- [Technical Requirements Document (TRD)](./technical_requirements_document.md): Software architecture design, component topology, clean architecture guidelines, and performance metrics.
- [UI/UX & Usability Specification](./ui_ux_usability_specification.md): Conformity to IEC 62366-1 usability engineering, visual semantic system, and use error mitigation rules.
- [Backend Schema & Domain Specification](./backend_schema_specification.md): Pydantic V2 models, biological limit validators, and cross-field coherence checks.
- [Traceability Matrix](./traceability_matrix.md): Traceability mapping clinical DOIs $\rightarrow$ Software Requirement IDs $\rightarrow$ Verification Tests (100% motor coverage).

## 3. Risk Management
- [Risk Management File](./risk_management_file.md): Hazard analysis and mitigation mapping under ISO 14971 (51 hazards, all 48 engines covered).

## 4. Software Specifics & Third-Party Code (IEC 62304)
- [SOUP Manifest](./soup_manifest.md): External software (SOUP) provenance registry and risk mitigations (IEC 62304 §8.1.2).

## 5. Verification & Validation (V&V)
- [Software Verification & Validation (V&V) Plan](./software_verification_validation_plan.md): Verification testing levels, quality gates, automated metrics, and clinical dataset validation protocols.
- **Verification Suite:** Python test runner configurations in `apps/backend/tests/`.
- **Status:** **606 test cases passing successfully** with 100% statement coverage on registered motors.

## 6. Implementation & Deployment
- [Software Implementation & Deployment Plan](./software_implementation_deployment_plan.md): Host environments, container topology, installation scripts, backup policies, and clinical trial integration flows.

## 7. Interoperability Layer (Sprint 9 — FHIR R4 + OMOP CDM 5.4)
- **FHIR R4:** `apps/backend/src/fhir/` — 56 LOINC + 42 SNOMED + 78 ATC mappings, Bundle generator, profile validation (37 tests).
- **OMOP CDM 5.4:** `apps/backend/src/omop/` — 50+40+63 concept_id mappings, ETL SQL generator, 6 cohort definitions, bidirectional FHIR↔OMOP.
- **DDL Scripts:** `apps/backend/src/omop/ddl/omop_cdm_5.4_postgresql.sql` — 24 tables + indexes.
- **API Endpoints:** `apps/backend/src/api/v1/endpoints/fhir.py` (3 endpoints), `omop.py` (4 endpoints).
- **HAPI FHIR Server:** Docker compose configuration with PostgreSQL backend.

---
*Este índice constituye el registro maestro del proceso de diseño de Integrum V2.*
*Última actualización: 2026-06-07 — Sprint 10 validation + 606 tests*

