# IN CONSTRUCTION — SOUP Manifest (Integrum V2.5)
# IEC 62304 §8.1.2 — Software of Unknown Provenance
# Revision: 2026.03.29.C | Status: IN CONSTRUCTION — COVERAGE PARCIAL

> [!WARNING]
> **COBERTURA PARCIAL:** Este manifiesto se encuentra en construcción. Se han inventariado las dependencias críticas iniciales, pero se requiere un SBOM completo y una revisión sistemática de CVEs para alcanzar conformidad con IEC 62304.

---

## 1. Backend SOUP Inventory (Python/FastAPI Stack)

| Name | Version | Supplier | Category | Known Issues (CVE) | Impact on Risk (Hazard) |
|---|---|---|---|---|---|
| **PostgreSQL** | 15.x | PostgreSQL Group | Infraestructura | None identified (no systematic CVE review completed) | H-005 (Audit Trail Integrity), H-006 (PHI Privacy) |
| **SQLAlchemy** | 2.0.48 | SQLAlchemy Authors | Infraestructura | None identified (no systematic CVE review completed) | H-005 (Audit Trail) |
| **FastAPI** | 0.115.8 | Tiangolo | API Gateway | None identified (no systematic CVE review completed) | H-003 (Input Validation) |
| **Pydantic** | 2.12.15 | Pydantic Authors | Lógica Clínica | None identified (no systematic CVE review completed) | H-003 (Guardrails), H-007 (Calculation Errors) |
| **cryptography** | 46.0.5 | PyCA | Seguridad | None identified (no systematic CVE review completed) | H-006 (PHI Encryption) |
| **python-jose** | 3.5.0 | Michael Hart | Seguridad | None identified (no systematic CVE review completed) | H-004 (Concurrency/Auth) |
| **safety** | 3.7.0 | pyUp.io | Auditoría | Dev dependency – no direct runtime impact | N/A |
| **alembic** | 1.15.5 | SQLAlchemy Authors | Infraestructura | None identified (no systematic CVE review completed) | H-005 (Schema Migration) |
| **asyncpg** | 0.31.0 | asyncpg Authors | Infraestructura | None identified (no systematic CVE review completed) | H-005 (Data Integrity) |

---

## 2. Frontend SOUP Inventory (Next.js/React Stack)

| Name | Version | Supplier | Category | Known Issues (CVE) | Impact on Risk (Hazard) |
|---|---|---|---|---|---|
| **Next.js** | 14.1.0 | Vercel | Presentación | None identified (no systematic CVE review completed) | N/A |
| **React** | 18.2.0 | Meta | Presentación | None identified (no systematic CVE review completed) | N/A |
| **Zod** | 3.22.x | Colin McDonnell | Lógica (Draft) | None identified (no systematic CVE review completed) | H-003 (Schema Guardrail) |
| **ESLint** | 8.57.0 | OpenJS Foundation | Auditoría | Dev dependency – no direct runtime impact | N/A |
| **Tailwind CSS** | 3.4.1 | Tailwind Labs | Presentación | None identified (no systematic CVE review completed) | N/A |

---

## 3. Gap Analysis & SBOM Strategy

- **Gap 1:** Falta auditoría sistemática de dependencias transitivas.
- **Gap 2:** No se han vinculado todos los hazards secundarios de ciberseguridad.
- **Estrategia V2.6:** Implementar `cyclonedx-python` para generar SBOM automáticos en cada build.

---

**Revision:** 2026.03.29.C | **Status:** IN CONSTRUCTION — COVERAGE PARCIAL
