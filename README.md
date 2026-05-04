# Integrum V2 — Clinical Decision Support System for Obesity & Cardiometabolic Health

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/Pydantic-V2-orange.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-613%20passing-brightgreen.svg)](https://github.com/anomalyco/integrum_v2)
[![IEC 62304](https://img.shields.io/badge/IEC%2062304-Class%20B-yellow.svg)](https://webstore.iec.ch/publication/60601)

> **SaMD Class B** — Software as a Medical Device for obesity and cardiometabolic health risk stratification.
> Built with Clean Architecture, clinical evidence traceability, and IEC 62304 Class B compliance patterns.

## Architecture Overview

```
apps/
├── backend/
│   ├── src/
│   │   ├── domain/          # Pure Pydantic models (Encounter, Observation)
│   │   ├── engines/         # Clinical motors (47 engines, 5 evidence tiers)
│   │   │   ├── confidence_standards.py  # GRADE-aligned confidence rubric
│   │   │   ├── calculators.py           # SSOT for clinical math
│   │   │   └── specialty/   # 41 specialty motors
│   │   ├── schemas/         # API schemas
│   │   └── services/        # Application services
│   └── tests/
│       └── unit/engines/    # 613 tests (100% engine coverage)
└── frontend/                # Next.js 14 clinical dashboard
```

## Clinical Engines (47)

### Evidence-Based Confidence Scoring
All engines use a **5-tier GRADE-aligned confidence rubric** (`confidence_standards.py`):

| Tier | Confidence | Evidence Type | Example Engines |
|---|---|---|---|
| ESTABLISHED_GUIDELINE | 0.95 | Major society guidelines | Cancer screening, GLP-1 monitoring, KDIGO protein |
| VALIDATED_BIOMARKER | 0.90 | Well-validated biomarkers | Sarcopenia (EWGSOP2), Free testosterone (Vermeulen) |
| PEER_REVIEWED | 0.85 | Multiple peer-reviewed studies | TyG-BMI, Cardiometabolic indices |
| INDIRECT_EVIDENCE | 0.75 | Biological plausibility | Biological age, Psychometabolic axis |
| PROXY_MARKER | 0.60 | Single studies, mechanistic | Pharmacogenomics, Drug interactions |

### Engine Categories
- **Core (7):** Acosta phenotype, EOSS staging, Sarcopenia monitor, Biological age, Metabolic precision, Deep metabolic proxy, Lifestyle 360
- **Specialty (10+):** Anthropometry, Endocrine, Hypertension, Inflammation, Sleep apnea, Lab stewardship, Fatty liver, VAI, Free testosterone, Vitamin D
- **Safety (5+):** GLP-1 monitoring, Metformin B12, Cancer screening, ApoB/ApoA1, Pulse pressure
- **Risk (4+):** PCE ASCVD risk, KFRE, Fried frailty, TyG-BMI, CVD reclassifier
- **Gender-Specific (2):** Women's health (PCOS, HRT safety), Men's health (TRT safety gates)

## Clinical Correctness

### Verified Against Standards
22 clinical correctness tests verify actual computed values within 2% tolerance:

| Calculator | Standard | Tolerance |
|---|---|---|
| HOMA-IR | Matthews et al., 1985 | ±2% |
| TyG Index | Vasques et al., 2011 | ±2% |
| eGFR (CKD-EPI) | KDIGO 2021 | ±2% |
| MAP | AHA/ACC | ±2% |
| BRI | Thomas et al., 2010 | ±2% |
| FIB-4 | Sterling et al., 2006 | ±2% |

### Key Clinical Thresholds (Cited)
All thresholds trace to peer-reviewed evidence:
- **hs-CRP >3.0 mg/L** → Pearson et al., 2003 (AHA/CDC)
- **NLR >2.5** → Zahorec R, 2001
- **HbA1c ≥6.5%** → ADA Standards of Care, 2024
- **FIB-4 >1.30** → Sterling et al., 2006
- **ARR >30 + Aldo >15** → Funder et al., 2016 (Endocrine Society)

## Safety Features

- **Immutable Observations:** `Observation` model uses `frozen=True` to prevent clinical data mutation (IEC 62304 §5.1.2)
- **Cryptographic Key Separation:** Encryption key and Blind Index HMAC key derived independently via HKDF-SHA256
- **Fail-Fast Security:** Application crashes unless `SECRET_KEY` is set (except `ENVIRONMENT=development`)
- **Physiological Bounds:** All observation values validated against biological limits
- **Gender-Specific Guards:** Women's health runs only for female, Men's health only for male

## Running Tests

```bash
cd apps/backend
python3 -m pytest tests/unit/engines/ -v --tb=short
```

**Result:** 613 tests passing, 0 failures

## Technical Debt Audit Status

| ID | Category | Status | Description |
|---|---|---|---|
| C-01 | Architecture | ✅ Fixed | Circular dependencies eliminated |
| C-02 | Architecture | ✅ Fixed | Singleton replaced with stateless factory |
| C-03 | Architecture | ✅ Fixed | Motors return explicit ERROR states |
| H-01 | High | ✅ Fixed | Stale data-contracts/ removed |
| H-03 | High | ✅ Fixed | Clinical correctness verified |
| H-04 | High | ✅ Fixed | All confidence values use GRADE rubric |
| H-05 | High | ✅ Fixed | Dependencies pinned to exact versions |
| M-02 | Medium | ✅ Fixed | Duplicate safe_float consolidated |
| M-03 | Medium | ✅ Fixed | Observations immutable (frozen=True) |
| M-04 | Medium | ✅ Fixed | Unused structlog removed from domain |

## Compliance Frameworks

- **IEC 62304 Class B:** Software lifecycle processes for medical device software
- **ISO 13485:** Quality management systems for medical devices
- **FDA 21 CFR Part 11:** Electronic records and signatures
- **HIPAA:** Protected health information handling

## License

This project is provided for academic and portfolio purposes. Not intended for clinical use without proper regulatory clearance.
