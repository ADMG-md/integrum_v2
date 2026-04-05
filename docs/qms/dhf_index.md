# Design History File (DHF) Index
**Project:** Integrum V2
**Standard:** ISO 13485 Clause 7.3.10 / 21 CFR 820.30(j)

## 1. Design Planning
- [ROADMAP.md](../../ROADMAP.md): Tactical development missions.
- [MISSION3_BLUEPRINT.md](../../MISSION3_BLUEPRINT.md): Clinical Engine Refactoring.
- [MISSION3.5_BLUEPRINT.md](../../MISSION3.5_BLUEPRINT.md): Specialty Micro-Engines.
- [MISSION4_BLUEPRINT.md](../../MISSION4_BLUEPRINT.md): Dynamic Intake & T0 Flow.

## 2. Design Input & Output
- Requirements and Implementation logic are traced in the [Traceability Matrix](./traceability_matrix.md).

## 3. Risk Management
- [Risk Management File](./risk_management_file.md): Hazard analysis and mitigation (50 hazards, all 38 motors covered).

## 4. Software Specifics (IEC 62304)
- [SOUP Manifest](./soup_manifest.md): External software provenance and risk assessment.

## 5. Verification & Validation
- Verification scripts are located in `apps/backend/tests/`.
- Automated test logs serve as verification evidence.
- 278 tests passing (100% motor coverage).

## 6. Interoperability Layer (Sprint 9 — FHIR R4 + OMOP CDM 5.4)
- **FHIR R4:** `apps/backend/src/fhir/` — 56 LOINC + 42 SNOMED + 78 ATC mappings, Bundle generator, profile validation (37 tests).
- **OMOP CDM 5.4:** `apps/backend/src/omop/` — 50+40+63 concept_id mappings, ETL SQL generator, 6 cohort definitions, bidirectional FHIR↔OMOP.
- **DDL Scripts:** `apps/backend/src/omop/ddl/omop_cdm_5.4_postgresql.sql` — 24 tables + indexes.
- **API Endpoints:** `apps/backend/src/api/v1/endpoints/fhir.py` (3 endpoints), `omop.py` (4 endpoints).
- **HAPI FHIR Server:** Docker compose configuration with PostgreSQL backend.

---
*Este índice constituye el registro maestro del proceso de diseño de Integrum V2.*
*Última actualización: 2026-04-05 — Sprint 9 FHIR/OMOP + VETO remediation.*
