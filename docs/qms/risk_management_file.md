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
| **H-016** | **Suicide Risk Missed** | Bupropion/naltrexone prescrito sin verificar PHQ-9 Item 9 | Aumento de riesgo suicida (FDA Black Box Warning) | P2 | S5 | UNA | Gate obligatorio: phq9_item_9_score > 0 → contraindicación. Verificado en ObesityPharmaEligibilityMotor y DrugInteractionMotor. | **Unit Test**: `test_bupropion_contraindicated_suicide_risk` (Verified) | P1 (ACC) |
| **H-017** | **GLP-1 TCM/MEN2** | GLP-1 prescrito en paciente con historia de carcinoma medular de tiroides o MEN2 | Cáncer de tiroides (causalidad en roedores, humano desconocido) | P1 | S5 | UNA | Gate obligatorio: has_history_medullary_thyroid_carcinoma o has_history_men2 → contraindicación absoluta. | **Unit Test**: `test_glp1_contraindicated_mtc`, `test_glp1_contraindicated_men2` (Verified) | P1 (ACC) |
| **H-018** | **Anthropometry Error** | Circunferencias mal interpretadas (waist/hip/arm/calf) | Cálculos erróneos de WHR, WHtR, sarcopenia screening | P2 | S2 | ALARP | Bounds biológicos en BiometricsSchema (waist 30-300cm, hip 30-300cm). | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-019** | **Endocrine Misclassification** | TSH/FT4 mal interpretados → diagnóstico erróneo de hipo/hipertiroidismo | Tratamiento hormonal injustificado o retraso en diagnóstico | P3 | S3 | ALARP | Bounds biológicos (TSH 0.01-100, FT4 0.1-10). Validación de rangos de referencia por laboratorio. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-020** | **Hypertension Secondary Missed** | Hipertensión secundaria no identificada (aldosterona/renina) | Tratamiento antihipertensivo inadecuado | P3 | S3 | ALARP | Motor evalúa ratio aldosterona/renina. Sugerencia de referencia a endocrinología si ratio elevado. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-021** | **Inflammation Over-interpretation** | hs-CRP elevado interpretado como inflamación cardiovascular sin descartar infección aguda | Sobre-tratamiento antiinflamatorio | P3 | S2 | ALARP | Motor verifica hs-CRP > 10 mg/L como posible infección aguda (no CV). | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-022** | **Sleep Apnea Under-screening** | STOP-Bang mal calculado → SAOS no detectado | Apnea no tratada → riesgo CV aumentado | P3 | S3 | ALARP | Motor calcula STOP-Bang con 8 items. Score >= 3 → referencia a polisomnografía. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-023** | **Lab Stewardship Over-testing** | Sugerencia de pruebas innecesarias | Costo innecesario, hallazgos incidentales | P3 | S1 | ACC | Motor prioriza pruebas por valor clínico. No sugiere pruebas sin indicación. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-024** | **Functional Sarcopenia Missed** | Grip strength/gait speed mal interpretados | Sarcopenia funcional no diagnosticada → caídas/fracturas | P3 | S3 | ALARP | Motor usa criterios EWGSOP2. Bounds: grip 5-80kg, gait 0.1-3.0 m/s. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-025** | **FLI Miscalculation** | Fatty Liver Index mal calculado (TG, BMI, GGT, waist) | NAFLD no detectado o sobrediagnosticado | P2 | S3 | ALARP | Fórmula validada contra Bedogni et al. 2006. FLI >= 60 → NAFLD probable. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-026** | **VAI Miscalculation** | Visceral Adiposity Index mal calculado (waist, BMI, TG, HDL) | Riesgo cardiometabólico subestimado | P2 | S3 | ALARP | Fórmula validada por Amato et al. 2010. Gender-specific thresholds. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-027** | **ApoB/ApoA1 Ratio Error** | Ratio mal interpretado → riesgo CV subestimado | Prevención cardiovascular inadecuada | P2 | S3 | ALARP | Ratio >= 0.9 (M) / >= 0.8 (F) → riesgo aumentado. Bounds: ApoB 20-500, ApoA1 no acotado. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-028** | **Pulse Pressure Misclassification** | PP ancha no identificada → riesgo CV subestimado | Prevención cardiovascular inadecuada | P2 | S3 | ALARP | PP >= 60 mmHg → riesgo CV aumentado. Bounds: SBP 60-300, DBP 30-200. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-029** | **NFS Miscalculation** | NAFLD Fibrosis Score mal calculado → fibrosis hepática no detectada | Cirrosis no diagnosticada | P2 | S4 | ALARP | Fórmula validada por Angulo et al. 2007. NFS > 0.676 → fibrosis avanzada probable. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-030** | **ACE Score Misinterpretation** | Puntaje ACE mal interpretado → trauma no reconocido | Intervención psicológica retrasada | P3 | S2 | ALARP | ACE >= 4 → referencia a salud mental. Bounds: 0-10. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-031** | **SGLT2i in Low eGFR** | SGLT2i iniciado con eGFR < 20 | Ineficacia glucémica, riesgo de cetoacidosis | P2 | S4 | UNA | Gate en validate: eGFR < 20 → no indicado. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-032** | **KFRE Miscalculation** | Kidney Failure Risk Equation mal calculado → referencia tardía a nefrología | Progresión a diálisis sin preparación | P2 | S4 | ALARP | Fórmula Tangri 2016 validada. Risk 5y > 25% → referencia urgente. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-033** | **Charlson Score Error** | Índice de comorbilidad mal calculado → pronóstico erróneo | Planificación de cuidado inadecuada | P2 | S3 | ALARP | Algoritmo validado por Charlson 1987. Score >= 6 → alta mortalidad. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-034** | **Free Testosterone Error** | Testosterona libre mal calculada (Vermeulen equation) | Hipogonadismo no diagnosticado o sobrediagnosticado | P2 | S2 | ALARP | Ecuación Vermeulen validada. Requiere TT, SHBG, albumina. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-035** | **Vitamin D Misclassification** | Vitamina D mal clasificada → suplementación inadecuada | Deficiencia no tratada o toxicidad por sobredosis | P3 | S2 | ALARP | Bounds: 5-150 ng/mL. < 20 deficiente, 20-30 insuficiente, > 30 suficiente. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-036** | **Fried Frailty Error** | Fenotipo de fragilidad mal calculado | Fragilidad no identificada → caídas/mortalidad | P2 | S3 | ALARP | 5 criterios Fried. >= 3 → frail. Bounds: grip 5-80kg, gait 0.1-3.0 m/s. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-037** | **TyG-BMI Miscalculation** | TyG-BMI mal calculado → resistencia a insulina subestimada | Prevención metabólica inadecuada | P2 | S2 | ALARP | Fórmula: ln(TG*fasting glucose/2) * BMI. Thresholds por población. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-038** | **CVD Reclassifier Error** | Recalificación de riesgo CV incorrecta → estatina no indicada | Evento CV prevenible | P2 | S4 | ALARP | Motor evalúa LDL + factores de riesgo. Statin indicated si LDL >= 70 + riesgo. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-039** | **WomensHealth Pregnancy Gate** | Medicamento teratogénico no bloqueado en embarazo | Malformación congénita | P1 | S5 | UNA | Gate obligatorio: pregnancy_status == "pregnant" → bloquear estatinas, SGLT2i, ACE/ARB. | **Unit Test**: `test_compute_with_pregnancy_alert` (Verified) | P1 (ACC) |
| **H-040** | **MensHealth PSA Error** | PSA mal interpretado → cáncer de próstata no detectado | Diagnóstico tardío de cáncer | P2 | S4 | ALARP | PSA >= 4.0 ng/mL → referencia a urología. Bounds: 0-100 ng/mL. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-041** | **BodyCompositionTrend Error** | Pérdida de masa magra no detectada durante pérdida de peso | Sarcopenia iatrogénica | P3 | S3 | ALARP | Threshold: > 5% lean mass loss → alerta. > 10% → crítica. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-042** | **GLP1Titration Over-escalation** | Dosis de GLP-1 escalada demasiado rápido | Efectos adversos GI severos | P2 | S3 | ALARP | Protocolo de titulación: mínimo 4 semanas por escalón. Dosis máxima definida. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-043** | **DrugInteraction DB Corruption** | SQLite de interacciones corrupta o desactualizada | Interacción no detectada → daño al paciente | P2 | S4 | ALARP | DB embebida con 53 meds, 56 interacciones, 32 contraindicaciones. Auto-rebuild from SQL. | **Unit Test**: `test_compute_with_critical_interaction` (Verified) | P1 (ACC) |
| **H-044** | **Metformin B12 Missed** | Deficiencia de B12 no detectada en metformina | Neuropatía, anemia, deterioro cognitivo | P3 | S3 | ALARP | Screening anual obligatorio. B12 < 200 → suplementación. 200-300 → MMA/homocisteína. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-045** | **CancerScreening Gap** | Screening de cáncer no sugerido cuando indicado | Diagnóstico tardío de cáncer | P3 | S4 | ALARP | Motor evalúa edad, sexo, factores de riesgo. Sugiere mamografía, colonoscopia, PAP, PSA. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-046** | **GLP1Monitoring Pancreatitis** | Pancreatitis no detectada en paciente con GLP-1 | Pancreatitis severa no tratada | P2 | S4 | UNA | Lipasa > 3x ULN → alerta de pancreatitis. Considerar suspensión de GLP-1. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-047** | **MetabolicPrecision Error** | Índices metabólicos mal calculados (HOMA-IR, TyG, METS-IR) | Clasificación errónea de resistencia a insulina | P2 | S2 | ALARP | Fórmulas delegadas a calculators.py (single source of truth). | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-048** | **DeepMetabolicProxy Error** | Proxies metabólicos mal calculados | Fenotipado metabólico incorrecto | P2 | S2 | ALARP | Proxies validados contra literatura. Confidence scoring. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-049** | **Lifestyle360 Error** | Recomendaciones de estilo de vida inadecuadas | Intervención inefectiva o contraproducente | P3 | S1 | ACC | Recomendaciones basadas en guías AHA/ACC. No farmacológicas. | **Unit Test**: `test_specialty_motors` (Verified) | P1 (ACC) |
| **H-050** | **FHIR Bundle Validation Gap** | Bundle FHIR exportado sin observaciones requeridas | Interoperabilidad incompleta con sistemas externos | P2 | S2 | ALARP | validate_fhir_bundle verifica 12 observaciones requeridas + 15 recomendadas. | **Unit Test**: `test_fhir_validator.py` (37 tests, Verified) | P1 (ACC) |
| **H-051** | **SOAP Text Generation Liability** | Nota SOAP autogenerada (ResultsViewer.tsx:120-173) copiada directamente al expediente médico legal con errores u omisiones | Responsabilidad médica directa por texto clínico generado algorítmicamente | P3 | S4 | UNA | 1) Disclaimer obligatorio "Nota preliminar — requiere revisión y firma del médico tratante". 2) Médico debe editar/confirmar antes de guardar. 3) TODO: auditoría de versionado de notas SOAP. | Sin test unitario — riesgo de proceso, no de cálculo. Requiere validación clínica. | P1 (ACC) |

---

## 3. Risk Control Verification

- **Implemented:** H-001, H-002, H-007, H-014, H-015 (Golden Motors + V2.6 Remediation).
- **Implemented:** H-016, H-017 (VETO-SAFETY-01/02 remediation, 2026-04-05).
- **Implemented:** H-018 through H-050 (Full motor hazard coverage, 2026-04-05).
- **SOUP:** H-043 — Drug interaction DB classified as SOUP (SQLite + clinical data).

---

**Revision:** 2026.04.05.E | **Status:** ACTIVE — VETO REMEDIATION APPLIED | 50 hazards covering all 38 motors
