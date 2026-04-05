# Integrum V2 — Agent Context

**Project:** CDSS for Obesity and Cardiometabolic Health (SaMD Class B, IEC 62304)
**Version:** 3.0 (Sprint 6 completed)
**Last Updated:** 2026-04-04

---

## Architecture

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy async, Pydantic V2
- **Frontend:** Next.js 14, React 18, TailwindCSS, TypeScript
- **Database:** PostgreSQL 16 (Alpine)
- **Proxy:** Caddy 2 (automatic TLS)
- **Structure:** Monorepo (`apps/backend/`, `apps/frontend/`)

## Clinical Engines (43 files, 27 registered)

### Core (7)
- AcostaPhenotypeMotor, EOSSStagingMotor, SarcopeniaMonitorMotor
- BiologicalAgeMotor, MetabolicPrecisionMotor, DeepMetabolicProxyMotor, Lifestyle360Motor

### Specialty (9)
- AnthropometryMotor, EndocrineMotor, HypertensionMotor, InflammationMotor
- SleepApneaMotor, LaboratoryStewardshipMotor, FunctionalSarcopeniaMotor
- FLIMotor, VAIMotor

### Safety + Screening (5)
- GLP1MonitoringMotor, MetforminB12Motor, CancerScreeningMotor
- ApoBApoA1Motor, PulsePressureMotor

### Integration (5)
- ACEScoreEngine, SGLT2iBenefitMotor, FreeTestosteroneMotor
- VitaminDMotor, CharlsonMotor

### Risk (3)
- KFREMotor, FriedFrailtyMotor, TyGBMIMotor, CVDReclassifierMotor

### Gender-Specific (2)
- WomensHealthMotor, MensHealthMotor

### Gated (2)
- CVDHazardMotor, MarkovProgressionMotor

### Aggregators (2)
- ObesityMasterMotor, ClinicalGuidelinesMotor

## Key Paths

| Resource | Path |
|---|---|
| Engines | `apps/backend/src/engines/` (7 top-level + 36 specialty/) |
| Tests | `apps/backend/tests/unit/engines/` |
| Schemas | `apps/backend/src/schemas/encounter.py` |
| Domain | `apps/backend/src/domain/models.py` |
| Calculators | `apps/backend/src/engines/calculators.py` |
| Risk Mgmt | `docs/qms/risk_management_file.md` |
| QMS | `docs/qms/` |
| SBOM | `apps/backend/sbom_manifest.txt` |
| Frontend | `apps/frontend/src/` |
| Data Contracts | `data-contracts/` |

## Rules

1. **Clean Architecture:** Engines MUST be pure Python — no FastAPI, no SQLAlchemy, no network calls
2. **Determinism:** Same input → same output, verified by version hash
3. **100% Test Coverage:** Every registered motor MUST have dedicated tests
4. **Traceability:** Every engine MUST have a `REQUIREMENT_ID` linking to clinical evidence
5. **Risk Sync:** Engine math changes MUST update `docs/qms/risk_management_file.md`
6. **Biological Bounds:** All observation values MUST be validated against physiological limits
7. **Gender-Specific:** WomensHealthMotor runs only for female, MensHealthMotor only for male

## Skills

- `repo-structure-auditor` — Clean Architecture enforcement
- `iec62304-auditor` — IEC 62304 Class B compliance (VETO power)
- `iso13485-qms` — Change control and traceability
- `clinical-validity-engineer` — Clinical evidence (GRADE) to code
- `test-coverage-auditor` — 100% engine test coverage enforcement
- `clinical-safety-officer` — FDA 21 CFR Part 11, HIPAA, drug safety
- `data-contracts-auditor` — Frontend/backend contract enforcement

## Workflows

- `quality-gate-iec62304` — Pre-merge quality gate (5 steps)
- `workflow-change-control` — ISO 13485 change control (5 steps)
