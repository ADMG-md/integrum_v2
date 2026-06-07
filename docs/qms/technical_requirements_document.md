# Technical Requirements Document (TRD)
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Scope
This document details the software architectural design, technical stacks, interface specifications, database schemas, and safety-critical system patterns for **Integrum V2**. It acts as the **Software Architectural Design** and **Software Design Specification (SDS)** under IEC 62304 §5.3 and §5.4.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial architecture and technical requirements baseline. |

---

## 2. System Architecture & Component Topology

Integrum V2 is structured as a monorepo consisting of a Next.js frontend, a FastAPI backend, a PostgreSQL relational database, and a Caddy 2 reverse proxy.

```
┌────────────────────────────────────────────────────────┐
│                      Client Browser                    │
│   ┌────────────────────────────────────────────────┐   │
│   │           Next.js 14 Web Application           │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ HTTPS (TLS 1.3)
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Caddy 2 Proxy                      │
└───────────────────────────┬────────────────────────────┘
                            │ Reverse Proxy (HTTP)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend Server               │
│                                                        │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │   API Layer (v1)      │   │   Interoperability   │  │
│  │   Endpoints & Auth    │   │   (FHIR R4 / OMOP)   │  │
│  └───────────┬───────────┘   └───────────┬──────────┘  │
│              │                           │             │
│              └─────────────┬─────────────┘             │
│                            │                           │
│              ┌─────────────▼─────────────┐             │
│              │  Pure Clinical Engines    │             │
│              │  (Acosta, EOSS, 48 Motors)│             │
│              └─────────────┬─────────────┘             │
└────────────────────────────┼───────────────────────────┘
                            │ asyncpg / SQLAlchemy
                            ▼
┌────────────────────────────────────────────────────────┐
│                   PostgreSQL 16 (DB)                   │
│   ┌───────────────────────┐   ┌──────────────────────┐   │
│   │   Application Schema  │   │  OMOP CDM 5.4 Schema │   │
│   └───────────────────────┘   └──────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### 2.1 Backend Stack
*   **Language:** Python 3.11+
*   **API Framework:** FastAPI (Asynchronous ASGI server using Uvicorn)
*   **Database Client:** SQLAlchemy 2.0 (asyncio extension) + `asyncpg` driver
*   **Data Serialization/Validation:** Pydantic V2
*   **Database Migrations:** Alembic

### 2.2 Frontend Stack
*   **Framework:** Next.js 14, React 18, TypeScript
*   **Styling:** TailwindCSS (Strictly scoped custom variables for premium UI)
*   **State Management:** React Context API or lightweight state libraries

### 2.3 Database Layer
*   **Engine:** PostgreSQL 16 (running on Alpine Linux within a Docker container)
*   **Schemas:** Separate relational schema for standard application metadata and clinical data. An independent relational schema contains the **OMOP CDM 5.4** PostgreSQL tables for analytical research.

---

## 3. Clinical Engines Specification (IEC 62304 §5.3)

To ensure clinical safety, determinism, and testability, all calculations must be executed in a dedicated sandbox layer.

### 3.1 Clean Architecture Isolation Rule
*   Clinical engines (`apps/backend/src/engines/`) must be **pure Python modules**.
*   **Strict Restrictions:** Engines are prohibited from accessing the network, making direct database queries, or importing any framework-specific dependency (e.g., FastAPI/SQLAlchemy).
*   **Inputs/Outputs:** Every engine accepts an immutable `Encounter` domain object and outputs a typed schema defined via Pydantic V2.

### 3.2 Determinism & Reproducibility
*   For any given set of patient inputs, the mathematical evaluation of the engine must return the exact same output.
*   The execution logic must verify compliance using version hashing of the source code.

### 3.3 Physiological Bounds Validation
*   Inputs must pass through a strict physiological validation layer (defined in `apps/backend/src/schemas/encounter.py`).
*   **Example Boundaries:**
    *   Age: $0 \le \text{Age} \le 125$ years
    *   Heart Rate: $30 \le \text{HR} \le 220$ bpm
    *   eGFR: $0 \le \text{eGFR} \le 200$ mL/min/1.73m²
    *   Body Mass Index (BMI): $10 \le \text{BMI} \le 100$ kg/m²

---

## 4. Interoperability & Terminology Specifications

### 4.1 HL7 FHIR R4 Mapping Specification
*   **Concept Mappings:** Local data structures are translated to FHIR standards using `src/fhir/concept_map.py`.
*   **Terminology Coverage:**
    *   **LOINC (56 Codes):** Standardizes clinical observations (Anthropometry, Vital Signs, Lipids, Psychometrics, etc.).
    *   **SNOMED-CT (42 Codes):** Maps conditions and comorbidities (Obesity E66, Diabetes E11, Hypertension I10, etc.).
    *   **ATC (78 Codes):** Maps pharmaceutical classes and active substances (GLP-1 RA, SGLT2i, Statins, Antidepressants).

### 4.2 OMOP CDM 5.4 Integration
*   **ETL SQL Engine:** Converts patient encounters in real-time into OMOP-compatible `INSERT` scripts.
*   **Research Cohorts:** Provides OHDSI/HADES compatible SQL scripts for federated cohorts:
    *   `obesity_bmi`: Adults with BMI $\ge 30$ kg/m²
    *   `t2dm`: Type 2 Diabetes Mellitus
    *   `glp1_eligible`: FDA-qualified GLP-1 cohort
    *   `mace`: Major Adverse Cardiovascular Events tracking

---

## 5. Security, Auditing & Privacy (HIPAA / 21 CFR Part 11)

### 5.1 Authentication & Authorization
*   OAuth2 protocol with JWT (JSON Web Tokens) generated using `python-jose` and secured with HMAC-SHA256 signatures.
*   Short-lived tokens (15-minute expiration) with cryptographically secure refresh tokens stored as HttpOnly, Secure cookies.

### 5.2 Protection of PHI (Protected Health Information)
*   **Encryption at Rest:** Patient demographic identifiers (Name, Email, Document ID) must be encrypted using AES-256-GCM.
*   **Encryption in Transit:** Caddy 2 automatically enforces TLS 1.3 with high-strength cipher suites.

### 5.3 Audit Trail Requirements
*   All read/write operations containing PHI must generate an immutable log entry in a dedicated audit table.
*   Logs must contain: Timestamp, User ID, Action Type, IP Address, Resource Accessed, and Hash of the record before/after modification.

---

## 6. Software Verification Specification (V&V)

*   **Framework:** pytest with asynchronous test runners (`pytest-asyncio`).
*   **Target Coverage:** 100% code coverage across the entire `apps/backend/src/engines/` registry.
*   **Continuous Compliance Gate:** A pre-commit hook or automated CI pipeline script must run the validation checks (`make vv_golden_motors` or equivalent) to confirm 100% test passing before code changes can be merged.
