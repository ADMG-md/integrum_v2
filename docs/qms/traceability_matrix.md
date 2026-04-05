# DRAFT / PoC — Traceability Matrix (Integrum V2.5)
# IEC 62304 §5.1.1 — Software Traceability
# Revision: 2026.03.30.D | Status: V2.6 REMEDIATION APPLIED

> [!IMPORTANT]
> **ALCANCE LIMITADO (PoC):** Actualmente, solo los motores **AcostaPhenotypeMotor** y **EOSSStagingMotor** cuentan con una cadena de trazabilidad completa desde el Clinical Requirement hasta el Test ID.

---

## 1. Golden Motor Traceability: Acosta Phenotype

| Clinical Req ID | Source DOI | Requirement Description | Hazard ID | Software Item | Verification Test | Test ID | Status |
|---|---|---|---|---|---|---|---|
| **SR-ACO-01** | 10.1038/oby.2014.248 | Hungry Brain: Buffet > 1376 (M) / 894 (F) kcal | H-001 | `AcostaPhenotypeMotor` | `test_acosta_threshold_male_boundary`, `test_acosta_threshold_female_boundary` | T-ACO-01 | ✅ Verified |
| **SR-ACO-02** | 10.1038/oby.2014.248 | Emotional Hunger: GAD-7 score >= 10 | H-001 | `AcostaPhenotypeMotor` | `test_acosta_emotional_hunger_anxiety_boundary` | T-ACO-02 | ✅ Verified |
| **SR-ACO-03** | 10.1038/oby.2014.248 | Intestino Hambriento: Gastric Emptying T1/2 < 85 min | H-001 | `AcostaPhenotypeMotor` | `test_acosta_gastric_emptying_boundary` | T-ACO-03 | ✅ Verified |
| **SR-ACO-04** | 10.1038/oby.2014.248 | Emotional Hunger: Confid. 0.85 if confirmed by Psych | H-001 | `AcostaPhenotypeMotor` | `test_acosta_emotional_hunger_with_psych` | T-ACO-04 | ✅ Verified |

---

## 2. Golden Motor Traceability: EOSS Staging

| Clinical Req ID | Source DOI | Requirement Description | Hazard ID | Software Item | Verification Test | Test ID | Status |
|---|---|---|---|---|---|---|---|
| **SR-EOS-01** | 10.1038/ijo.2009.2 | Obesity Diagnosis (E66) required as precondition | H-002 | `EOSSStagingMotor` | `test_eoss_validate_requires_e66` | T-EOS-01 | ✅ Verified |
| **SR-EOS-02** | 10.1038/ijo.2009.2 | Stage 2 Criteria: HTN (I10) or DM2 (E11) | H-002 | `EOSSStagingMotor` | `test_eoss_stage_2_dm2`, `test_eoss_stage_2_htn` | T-EOS-02 | ✅ Verified |
| **SR-EOS-03** | 10.1038/ijo.2009.2 | Stage 3 Criteria: Myocardial Infarct (I21) | H-002 | `EOSSStagingMotor` | `test_eoss_stage_3_mi` | T-EOS-03 | ✅ Verified |
| **SR-EOS-04** | 10.1038/ijo.2009.2 | Stage 4 Criteria: Disabling Stroke (I63.9) | H-002 | `EOSSStagingMotor` | `test_eoss_stage_4_terminal` | T-EOS-04 | ✅ Verified |
| **SR-EOS-05** | 10.1038/ijo.2009.2 | Biometric Trigger: BMI >= 30 (R-04 Fix) | H-002 | `EOSSStagingMotor` | `test_eoss_triggers_with_bmi_without_e66` | T-EOS-05 | ✅ Verified |

---

## 3. Precision & Longevity Traceability: Biological Age

| Clinical Req ID | Source DOI | Requirement Description | Hazard ID | Software Item | Verification Test | Test ID | Status |
|---|---|---|---|---|---|---|---|
| **SR-LON-01** | 10.18632/aging.101414 | PhenoAge (Levine) BioAge Acceleration | H-009, H-010 | `BiologicalAgeMotor` | `test_phenoage_matches_reference_example`, `test_bioage_normal_input_returns_ok` | T-LON-01 | ✅ Verified |
| **SR-LON-02** | R-05 (H-007 Remediation) | BioAge MUST NOT silently fall back to chronological age | H-007 | `BiologicalAgeMotor` | `test_bioage_error_does_not_fall_back_to_chrono`, `test_bioage_error_sets_status_error` | T-LON-02 | ✅ Verified |

---

## 4. Sarcopenia Traceability: ASMI Proxy

| Clinical Req ID | Source DOI | Requirement Description | Hazard ID | Software Item | Verification Test | Test ID | Status |
|---|---|---|---|---|---|---|---|
| **SR-SAR-01** | EWGSOP-2019 / Kim 2014 | ASMI uses appendicular proxy (0.75 coeff) | H-014 | `SarcopeniaMonitorMotor` | `test_asmi_uses_appendicular_proxy_not_total_mm` | T-SAR-01 | ✅ Verified |

---

---

## 5. Clinical Decision Support (Layer 6) — Action Motor

| Clinical Req ID | Source DOI | Requirement Description | Hazard ID | Software Item | Verification Test | Status |
|---|---|---|---|---|---|---|
| **SR-GUI-01** | 10.1161/HYP.0000000000000065 | Detect HTN Stage 2 Omission if BP >= 140/90 and no ACEi/ARB | H-017 | `ClinicalGuidelinesMotor` | `test_guidelines_htn_omission_sr_gui_01` | ✅ Verified |
| **SR-GUI-02** | 10.1093/eurheartj/ehab484 | Detect Lipidic Inertia Omission if LDL > meta and no Statin | H-017 | `ClinicalGuidelinesMotor` | `test_guidelines_lipidic_omission_sr_gui_02` | ✅ Verified |
| **SR-GUI-03** | 10.2337/dc24-Sint | Suggest GLP-1 for beta-cell preservation if HOMA-B < 50% | H-017 | `ClinicalGuidelinesMotor` | `test_guidelines_homa_b_preservation_sr_gui_03` | ✅ Verified |
| **SR-RES-01** | Mission 12 | Smoke Test Scrappy: Honest Gating (Risk motors block if labs missing) | H-018 | `CVDHazardMotor` | `smoke_test_scrappy.py` | ✅ Verified |
| **SR-RES-02** | 10.1002/oby.23120 | Behavioral Visibility: Phenotyping active via Psychometry without labs | H-018 | `AcostaPhenotypeMotor` | `smoke_test_scrappy.py` | ✅ Verified |

## 6. Coverage Analysis

- **Motores Golden (Acosta, EOSS):** Trazabilidad completa.
- **Motores de Longevidad (BioAge):** Trazabilidad completa (R-05 applied).
- **Sarcopenia:** Trazabilidad parcial (R-02 proxy, pending ALM/DXA).
- **Resiliencia (Paciente Scrappy):** Verificada vía `/tmp/smoke_test_scrappy.py`. Gating funcional.
- **Riesgo:** Hazards H-003 a H-008 marcados como "Planned" en el RMF.

---

**Revision:** 2026.03.30.D | **Status:** V2.6 REMEDIATION APPLIED
