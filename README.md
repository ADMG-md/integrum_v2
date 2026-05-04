# Integrum V2 — Clinical Decision Support System for Obesity & Cardiometabolic Health

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/Pydantic-V2.12.0-orange.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-652%20passing-brightgreen.svg)](https://github.com/anomalyco/integrum_v2)
[![IEC 62304](https://img.shields.io/badge/IEC%2062304-Class%20B-yellow.svg)](https://webstore.iec.ch/publication/60601)

> **SaMD Class B** — Software as a Medical Device for obesity and cardiometabolic health risk stratification.
> Engineered with **Clean Architecture**, clinical evidence traceability, and **IEC 62304 Class B** compliance patterns.

## 🚀 Showcase: Staff Engineer Competencies

This repository demonstrates advanced architectural and operational engineering:
- **Clean Architecture:** Strict boundary enforcement between Domain, Engines, and API layers.
- **V&V Rigor (IEC 62304):** 100% unit test coverage for clinical motors with dedicated V&V documentation headers.
- **SSOT Clinical Mathematics:** Centralized, auditable calculators for all clinical indices (HOMA, TyG, FIB-4, etc.).
- **Security Hardening:** AES-256-GCM encryption with HMAC-SHA256 blind indexing and fail-fast environment validation.
- **Operational Excellence:** Modern dependency management via `pyproject.toml` and automated technical debt remediation.

## 🏗️ Architecture Overview

```
apps/
├── backend/
│   ├── src/
│   │   ├── domain/          # Aggregate Roots & SSOT Calculators
│   │   ├── engines/         # Deterministic Clinical Motors (53 registered)
│   │   │   ├── base.py      # Base Clinical Engine Interface
│   │   │   └── specialty/   # 46 Specialty Micro-Engines
│   │   ├── schemas/         # API & Data Contract Schemas
│   │   └── services/        # Orchestrators & Clinical Intelligence Bridge
│   └── tests/
│       └── unit/engines/    # 652 tests (100% motor coverage)
└── frontend/                # Next.js 14 Clinical Dashboard
```

## 🔬 Clinical Engines (53)

### Evidence-Based Confidence Scoring (GRADE)
All adjudication results include a confidence score aligned with medical evidence tiers:

| Tier | Confidence | Evidence Type |
|---|---|---|
| **ESTABLISHED_GUIDELINE** | 0.95 | Major society guidelines (ADA, ACC/AHA, KDIGO) |
| **VALIDATED_BIOMARKER** | 0.90 | Extensively validated markers (EWGSOP2, BIA) |
| **PEER_REVIEWED** | 0.85 | Multiple peer-reviewed validation studies |
| **INDIRECT_EVIDENCE** | 0.75 | Biological plausibility & mechanistic markers |
| **PROXY_MARKER** | 0.60 | Emerging evidence or clinical proxies |

### Precision Engine Clusters
- **Metabolic Suite:** HOMA-IR, HOMA-B, TyG Index, METS-IR, Ahlqvist Diabetes Clusters.
- **Body Comp & Sarcopenia:** SMI (BIA), Grip Strength, Obesity Phenotyping (Acosta).
- **Hepatometabolic:** Fatty Liver Index (FLI), NAFLD Fibrosis Score (NFS), FIB-4.
- **Pharmacotherapy Gates:** GLP-1/GIP Titration, AOM Eligibility, Metformin-B12.
- **Cardiorenal Risk:** KFRE (Kidney Failure), PCE ASCVD, Pulse Pressure, VAIMotor.

## 🛡️ Safety & Compliance

- **Stateless Engines:** Zero-state clinical micro-engines prevent patient data leakage.
- **Immutable Observations:** `Observation` models are frozen at instantiation to prevent runtime mutation.
- **Clinical Soft-Stops:** Real-time contraindication detection for high-cost or high-risk therapies (e.g., MTC/MEN2 for GLP-1).
- **Audit Trails:** Structured logging (`structlog`) for all critical clinical adjudication paths.

## 🛠️ Testing & V&V

### Clinical Correctness Verification
All indices are verified against gold-standard publications with a ±2% tolerance:

| Index | Clinical Evidence | Status |
|---|---|---|
| **NFS** | Angulo et al., 2007 | ✅ Verified |
| **PhenoAge** | Levine et al., 2018 | ✅ Verified |
| **CKD-EPI** | KDIGO 2021 | ✅ Verified |
| **VAI** | Amato et al., 2010 | ✅ Verified |

### Running the V&V Suite

```bash
cd apps/backend
python3 -m pytest tests/unit/engines/ -v --tb=short
```

**Metrics:** 652 tests passing | 0 failures | 100% Engine Registration Coverage.

## 📋 Technical Debt Remediation Status

| Issue | Category | Status | Action |
|---|---|---|---|
| **C-01** | Configuration | ✅ Resolved | Unified `pyproject.toml` SSOT; Removed `requirements.txt`. |
| **C-02** | Safety | ✅ Resolved | Remediated silenced exceptions in Pediatric Nutrition. |
| **C-03** | Compliance | ✅ Resolved | 100% V&V test coverage for all 53 registered motors. |
| **H-01** | Architecture | ✅ Resolved | Eliminated God Class in `Encounter`; Stateless `SpecialtyRunner`. |
| **H-02** | Security | ✅ Resolved | Fail-fast validation for all cryptographic secrets. |

## ⚖️ License

This project is provided for academic and portfolio purposes. Not intended for clinical use without proper medical device regulatory clearance (SaMD).
