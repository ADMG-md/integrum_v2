# INITIAL DRAFT — Risk Management File (Integrum V2.5)
# ISO 14971:2019 — Preliminary Hazard Analysis
# Revision: 2026.03.29.C | Status: INITIAL DRAFT — UNDER REVIEW

> [!CAUTION]
> **ESTADO DE MADUREZ:** Este documento es un borrador inicial en expansión. Los valores de Probabilidad (P) e Impacto (S) son estimaciones preliminares sujetas a validación por un comité clínico formal. No se considera un RMF completo para certificación Clase B.

---

## 1. Risk Evaluation Scales (Standard ISO 14971)

### 1.1 Probability Scale (P)
| Level | Label | Definition | Score |
|---|---|---|---|
| P1 | Improbable | <1 in 10,000 encounters | 1 |
| P2 | Remote | 1 in 1,000–10,000 | 2 |
| P3 | Occasional | 1 in 100–1,000 | 3 |
| P4 | Probable | 1 in 10–100 | 4 |
| P5 | Frequent | >1 in 10 | 5 |

### 1.2 Severity Scale (S)
| Level | Label | Definition | Score |
|---|---|---|---|
| S1 | Negligible | No injury or health impact | 1 |
| S2 | Minor | Reversible injury, no medical intervention | 2 |
| S3 | Serious | Severe injury requiring medical intervention | 3 |
| S4 | Critical | Permanent impairment | 4 |
| S5 | Catastrophic | Death | 5 |

### 1.3 Risk Acceptance Matrix (R)
- **ACC (Acceptable):** Risk is low. No further action needed.
- **ALARP (As Low As Reasonably Practicable):** Risk must be mitigated to its lowest point.
- **UNA (Unacceptable):** Risk is too high. Immediate mitigation required.

| P \ S | S1 (Negl) | S2 (Min) | S3 (Ser) | S4 (Crit) | S5 (Cat) |
|---|---|---|---|---|---|
| **P5 (Freq)** | ALARP | UNA | UNA | UNA | UNA |
| **P4 (Prob)** | ACC | ALARP | UNA | UNA | UNA |
| **P3 (Occas)**| ACC | ACC | ALARP | UNA | UNA |
| **P2 (Remot)**| ACC | ACC | ACC | ALARP | UNA |
| **P1 (Impro)**| ACC | ACC | ACC | ACC | ALARP |

---

## 2. Hazard Analysis Table (ISO 14971:2019)

| H-ID | Hazard | Hazardous Situation | Harm | P | S | R | Risk Control | Verification Method | Residual R |
|---|---|---|---|---|---|---|---|---|---|
| **H-001** | Phenotype Miscalc (Acosta) | Physician prescribes based on wrong Acosta phenotype | Contraindicated drug prescription | P3 | S3 | ALARP | Confidence < 0.65 locks state; Mandatory physician audit. | **Unit Test**: `test_acosta_hungry_brain_male` (Verified) | P1 (ACC) |
| **H-002** | EOSS Under-staging | Missing CIE-10 code leading to lower stage | Delay in treatment; disease progression | P3 | S3 | ALARP | Pydantic validation (Encounter must have E66). | **Unit Test**: `test_eoss_validate_requires_e66` (Verified) | P2 (ACC) |
| **H-003** | Input Out-of-Bounds | Erroneous Glucose/Insulin values producing false results | Unnecessary titration/overdose | P4 | S3 | UNA | Pydantic constraint `ge=20, le=600` at API layer. | **Planned Unit Test**: `test_glucose_bounds_rejection` | P1 (ACC) |
| **H-004** | Race Condition (Runner) | Concurrent motor execution overwrites shared state | Inconsistent clinical insights | P2 | S3 | ALARP | Immutable `Encounter` domain object. | **Planned Unit Test**: `test_specialty_runner_determinism` | P1 (ACC) |
| **H-005** | Audit Log Corruption | DB transaction failure leaves partial audit trail | Regulatory non-compliance | P2 | S4 | ALARP | Atomic SQL transactions with `async with session.begin()`. | **Planned Unit Test**: `test_audit_integrity_post_failure` | P1 (ACC) |
| **H-006** | PHI Data Breach | Unencrypted field access in PostgreSQL | Privacy violation (HIPAA/PDPL) | P2 | S4 | ALARP | Field-Level Encryption via `vault_service`. | **Planned Security Test**: `test_vault_encryption_prevention` | P1 (ACC) |
| **H-007** | Silent Calculation Error | `safe_float()` swallows error without notifying UI | Results based on corrupt data | P4 | S2 | ALARP | `INDETERMINATE_LOCKED` state when data fails conversion. | **Planned Code Review**: Monitor `dato_faltante` population. | P2 (ACC) |
| **H-008** | CKD Protein Overload | Protein motor recommends dose > 0.8g/kg in CKD patient | Acute kidney injury | P2 | S4 | ALARP | Mandatory eGFR check; automatic dose cap. | **Planned Unit Test**: `test_protein_engine_ckd_lock` | P1 (ACC) |
| **H-009** | Sobre-optimización (Longevity obsession) | Patient over-interprets BioAge metrics | Anxiety/Orthorexia | P2 | S3 | ACC | Clinical Guardrail | Clinical Review | P1 (ACC) |
| H-010 | BioAge Anxiety | Patient perceives BioAge > ChronoAge as irreversible "terminal" sentence | Psychological distress | P2 | S2 | ALARP | 1) Disclaimer wording in UI. 2) Focus on modifiable biomarkers (MHO profile). | Clinical Evaluation Report (CER) Update | P1 (ACC) |
| H-011 | Shadow Clinical Logic | Motores clínicos no documentados o no verificados se ejecutan a través de SpecialtyRunner, generando salidas que parecen oficiales | Sugerencias clínicas basadas en lógica no validada, potencial de decisiones erróneas | P2 | S3 | ALARP | 1) Catálogo formal de motores con schema de entrada/salida y ClinicalRequirementID. 2) SpecialtyRunner limitado a FORMALIZED_MOTORS; DRAFT_MOTORS solo en desarrollo. 3) Revisión periódica del runner. | Unit Test: `test_specialty_runner_only_runs_formalized` + Code Review por release | P1 (ACC) |
| H-012 | Longevity Over-optimization | Paciente o clínico sobre-interpreta PhenoAge o métricas de "optimización" como patología aguda | Tratamientos innecesarios, polifarmacia, ansiedad clínica | P3 | S2 | ALARP | 1) Descargo de responsabilidad (Disclaimer) obligatorio en el reporte PhenoAge. 2) Separación visual clara entre rangos clínicos e indicadores de longevidad. | Verificación de UI (Disclaimer Check) + Clinical Review de Reportes | P1 (ACC) |
| H-013 | Hormonal Boundary Shift | Uso de rangos de "optimización" (longevidad) como si fueran rangos de referencia diagnósticos estándar | Diagnóstico erróneo de deficiencias, inicio de terapias hormonales injustificadamente | P2 | S3 | ALARP | 1) Marcado explícito de motores hormonales como "Optimization Layer" (DRAFT). 2) Validación obligatoria de comorbilidad antes de sugerencias de optimización. | Gating técnico en `specialty_runner.py` | P1 (ACC) |
| **H-014** | **ASMI Proxy Error** | Motor de Sarcopenia usa masa muscular total en vez de masa apendicular (ALM) | Infradiagnóstico de sarcopenia → catabolismo no detectado | P3 | S3 | ALARP | Proxy coeficiente 0.75 (Kim et al., 2014) aplicado a masa total. TODO: Reemplazar con ALM/DXA real. | **Unit Test**: `test_asmi_uses_appendicular_proxy_not_total_mm` (Verified) | P1 (ACC) |
| **H-015** | **Key Bricking** | VaultService genera nueva clave si falta `VAULT_MASTER_KEY`, haciendo irrecuperable la base de datos cifrada | Pérdida permanente de datos de pacientes | P2 | S5 | UNA | Fail-fast `RuntimeError` en startup. Dev-mode escape hatch via `ALLOW_DEV_VAULT_KEY=true`. | **Unit Test**: `test_vault_raises_if_key_missing` (Verified) | P1 (ACC) |

---

## 3. Risk Control Verification

- **Implemented:** H-001, H-002, H-007, H-014, H-015 (Golden Motors + V2.6 Remediation).
- **Planned (V2.7):** H-003 through H-008.

---

**Revision:** 2026.03.30.D | **Status:** ACTIVE — V2.6 REMEDIATION APPLIED
