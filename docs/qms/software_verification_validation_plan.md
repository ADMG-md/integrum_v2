# Software Verification & Validation (V&V) Plan
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Standard Reference:** IEC 62304 §5.6 & §5.7 / ISO 13485 Clause 7.3.6 & 7.3.7
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Purpose
This document establishes the formal framework for the verification and validation of **Integrum V2**. It defines the testing strategies, tools, acceptance criteria, and procedures required to prove the software functions safely, deterministically, and meets clinical specifications.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial Software Verification & Validation Plan. |

---

## 2. Verification Strategy (Tests Unitarios e Integración)

Verification confirms that the software items are built correctly and meet design specifications (inputs match outputs).

### 2.1 Testing Levels
1.  **Unit Verification (Clinical Engines):**
    *   **Scope:** All 48 clinical calculators under `src/engines/`.
    *   **Rule:** 100% code coverage. Every logic branch (e.g., Hungry Brain thresholds, EOSS staging conditions) must have corresponding test assertions in `tests/unit/engines/`.
    *   **Tool:** `pytest` + `pytest-cov`
2.  **Integration Verification (Interoperability & API):**
    *   **Scope:** API endpoints (FastAPI), database interactions (SQLAlchemy), and FHIR/OMOP mappings.
    *   **Rule:** Verify correct translation of database entries into FHIR R4 Bundles and OMOP inserts.
    *   **Tool:** `pytest-asyncio` + HAPI FHIR test containers.

### 2.2 Automated Quality Gates (CI/CD)
No pull request shall be merged into `main` unless:
*   All tests pass successfully.
*   Total coverage for engines remains at 100%.
*   Static code analysis (`ruff`) reports zero formatting or syntax compliance errors.

---

## 3. Validation Strategy (Validez Clínica y Usabilidad)

Validation confirms that the system meets user needs and is clinically safe for its intended clinical use.

### 3.1 Usability Validation (IEC 62366-1)
*   **Method:** Perform summative usability testing with 15 qualified clinicians.
*   **Scenario Testing:** Users will input demographic data, upload sample lab panels, review alerts (e.g., suicide risk Black Box warning), and export FHIR summaries.
*   **Goal:** 100% of participants must complete the tasks without critical use errors.

### 3.2 Clinical Accuracy Validation (Golden Dataset)
*   **Method:** Run a curated dataset of 200 dummy patient profiles with expert-reviewed expected outcomes.
*   **Metrics:** Compare Integrum V2 engine classifications (e.g., Acosta Phenotypes, KFRE scores) with manually adjudicated diagnosis.
*   **Acceptance Criteria:** 100% accuracy matching clinical reference equations (Acosta 2021, Tangri 2016, Sharma 2009).

---

## 4. Test Environment & Execution

### 4.1 Environments
*   **Development:** Isolated local virtual environment (`venv`) with sqlite/postgresql container.
*   **Staging:** Identical to production (Docker Compose orchestrated, Caddy reverse proxy) on a staging VPS, connected to dummy HAPI FHIR databases.
*   **Production:** Active clinical environment.

### 4.2 Execution Command
To run the verification suite and output the coverage report:
```bash
# Run backend engine tests with coverage
pytest --cov=src/engines tests/unit/engines/ --cov-report=term-missing
```
