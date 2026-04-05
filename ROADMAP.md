# Integrum V2: Estado del Proyecto y Roadmap

**Última actualización:** 2026-04-04
**Versión:** 4.0 (MVP Colombia-Ready)

---

## Estado Actual

### ✅ Completado

| Fase | Estado | Descripción |
|---|---|---|
| **Misiones 1-13** | ✅ | Backend, UI, SaMD, Security, CI/CD |
| **Sprint 1** | ✅ | 9 motores metabólicos + defect fixes |
| **Sprint 2** | ✅ | 7 motores clínicos (ACE, B12, Cancer, SGLT2i, etc.) |
| **Sprint 3** | ✅ | 4 motores de riesgo (KFRE, Charlson, Free T, Vit D) |
| **Sprint 4** | ✅ | Markov reactivado + limpieza redundancias |
| **Sprint 5** | ✅ | Body Composition Trend, AOM Eligibility, GLP-1 Titration |
| **Sprint 6** | ✅ | Women's Health, Men's Health, hormonal panels |
| **Sprint 7** | ✅ | Drug Interaction Motor + ProteinEngine |
| **Sprint 8** | ✅ | Drug DB expansion (142 meds, 163 interactions), ICD-10/11, Longevity |
| **Refactor God Class** | ✅ | Encounter 586→320 líneas (-45%) |
| **Agents Audit** | ✅ | 7 skills, 3 enforcement scripts, AGENTS.md, .cursorrules |

---

## Motores Clínicos Activos (32 total)

### Core (7)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| AcostaPhenotypeMotor | 4 fenotipos de obesidad | Acosta 2021 |
| EOSSStagingMotor | Estadiaje 0-4 de daño por obesidad | Sharma & Kuk 2009 |
| SarcopeniaMonitorMotor | ASMI + RPL (pérdida proteica) | EWGSOP2 2019 |
| BiologicalAgeMotor | PhenoAge + mortalidad 10a | Levine 2018 |
| MetabolicPrecisionMotor | HOMA-IR, TyG, FIB-4, clusters Ahlqvist | Múltiples |
| DeepMetabolicProxyMotor | GGT, Ferritina, Ácido úrico como proxies | Johnson Fat Switch |
| Lifestyle360Motor | Sueño, estrés, actividad física | WHO, AIS |

### Especialidad (9)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| AnthropometryMotor | WHtR, WHR, BRI | Múltiples |
| EndocrineMotor | TSH, FT4, FT3, rT3, ratio T3/rT3 | Endocrinología |
| HypertensionMotor | Aldosteronismo primario (ARR) | Endocrine Society 2016 |
| InflammationMotor | hs-CRP, NLR | Marcadores estándar |
| SleepApneaMotor | STOP-Bang | STOP-Bang validado |
| LaboratoryStewardshipMotor | Ordering inteligente | Estrategia LATAM |
| FunctionalSarcopeniaMotor | 5xSTS + Grip + Gait + SARC-F | EWGSOP2 2019 |
| FLIMotor | Fatty Liver Index (NAFLD) | Bedogni 2006 |
| VAIMotor | Visceral Adiposity Index | Amato 2010 |

### Seguridad + Screening (7)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| GLP1MonitoringMotor | Monitoreo GLP-1 (masa magra, plateau) | Seguridad clínica |
| MetforminB12Motor | Screening B12 en metformina | ADA 2024 |
| CancerScreeningMotor | Gaps screening 13+ cánceres | IARC 2016 |
| ApoBApoA1Motor | Ratio ApoB/ApoA1 (INTERHEART) | INTERHEART |
| PulsePressureMotor | Presión de pulso + MAP | Hemodinámica |
| NFSMotor | NAFLD Fibrosis Score | Angulo 2007 |
| DrugInteractionMotor | Interacciones, contraindicaciones, QT, renal | FDA, Lexicomp |

### Integración Clínica (5)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| ACEScoreEngine | Trauma como modificador de riesgo | Felitti 1998 |
| SGLT2iBenefitMotor | Beneficio cardio-renal SGLT2i | EMPA-REG, DAPA |
| FreeTestosteroneMotor | Testosterona libre (Vermeulen) | Vermeulen 1999 |
| VitaminDMotor | Estado Vitamina D + acción | Endocrine Society 2011 |
| CharlsonMotor | Comorbilidad → mortalidad 10a | Charlson 1987 |

### Género (2)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| WomensHealthMotor | SOP, embarazo, menopausia, obstetricia | Rotterdam 2003 |
| MensHealthMotor | Hipogonadismo, próstata, DE, fertilidad | Endocrinología |

### Terapia + Optimización (4)
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| BodyCompositionTrendMotor | Tasa de pérdida de masa magra | STEP 1, SURMOUNT-1 |
| ObesityPharmaEligibilityMotor | Elegibilidad FDA para AOMs | FDA 2024, SELECT |
| GLP1TitrationMotor | Protocolo de titulación de dosis | Clinical protocols |
| ProteinEngineMotor | Dosis proteica con Nephro-Shield | KDIGO 2024 |

### Riesgo (3)
| Motor | Qué evalúa | Estado |
|---|---|---|
| CVDHazardMotor | ASCVD 10y (PCE, ACC/AHA) | Activo |
| MarkovProgressionMotor | Progresión diabetes (UKPDS+DPP) | Calibrado |
| KFREMotor | Riesgo de falla renal a 2/5 años | Tangri 2016 |

### Agregadores (2)
| Motor | Qué hace |
|---|---|
| ObesityMasterMotor | Síntesis: Acosta + EOSS + Sarcopenia + CVD + proxies |
| ClinicalGuidelinesMotor | Auditoría de inercia clínica |

---

## Drug Interaction Database (SQLite embebida)

| Tabla | Registros | Descripción |
|---|---|---|
| `medications` | **142** | Medicamentos con peso, QT, CYP, teratogenicidad |
| `drug_interactions` | **163** | Interacciones (84 major, 68 moderate, 11 contraindicated) |
| `contraindications` | **35** | Contraindicaciones por condición (ICD-10) |
| `renal_dosing` | **18** | Ajustes de dosis por eGFR |
| `medication_side_effects` | **47** | Efectos adversos relevantes |
| `icd_crosswalk` | **56** | Mapeo ICD-10 → ICD-11 (44 exactos, 12 aproximados) |
| `longevity_interventions` | **32** | Intervenciones de longevidad y rendimiento |

### Medicamentos por clase (top)
| Clase | Cantidad |
|---|---|
| Atypical Antipsychotic | 7 |
| ARB | 5 |
| Anticonvulsant | 5 |
| Corticosteroid | 5 |
| SSRI | 5 |
| GLP-1 RA | 4 |
| Opioid | 4 |
| SGLT2i | 4 |
| Statin | 4 |

### Intervenciones de Longevidad
| Categoría | Evidencia | Cantidad |
|---|---|---|
| **Lifestyle** (strong) | Zone 2, VO2 Max, Resistance Training, Sleep | 4 |
| **Supplement** (strong) | Omega-3, Vitamin D, Creatine | 3 |
| **Pharmacological** (strong) | GLP-1, SGLT2i | 2 |
| **Supplement** (moderate) | NAD+, Magnesium, GlyNAC, Taurine, etc. | 7 |
| **Pharmacological** (moderate) | Metformin, Rapamycin, Acarbose | 3 |
| **Lifestyle** (moderate) | TRE, Sauna | 2 |
| **Experimental** | Senolytics, Plasma exchange, HBOT | 3 |

---

## ICD-10 → ICD-11 Crosswalk

**56 mapeos** listos para migración futura:
- **44 exactos**: E66→5B81 (Obesity), E11→5A11 (T2DM), I10→BA00 (HTN), etc.
- **12 aproximados**: E78→5C80 (Hyperlipidaemia), G47→7A00 (Sleep disorders), etc.

---

## Bugs Corregidos

| Bug | Impacto | Estado |
|---|---|---|
| `egfr_ckd_epi` no definido | RuntimeError en 3 motores | ✅ |
| `uacr` no definido | Referencia muerta | ✅ |
| `uric_acid` no definido | Referencia muerta | ✅ |
| `remnant_cholesterol` no definido | Referencia muerta | ✅ |
| `fat_free_mass` no definido | Referencia muerta | ✅ |
| `ideal_body_weight` no definido | Referencia muerta | ✅ |
| LAP units (mg/dL vs mmol/L) | Falsos positivos universales | ✅ |
| FLI/NFS asumían observaciones | AttributeError en compute | ✅ |
| Free T fórmula incorrecta | Valores 100x mayores | ✅ |
| Markov bloqueado | Sin predicción de progresión | ✅ |
| ClinicalHistory sin campos | CKD, HF, CAD faltaban | ✅ |
| God Class Encounter | 586 líneas, SRP violado | ✅ Refactorizado |
| ProteinEngineMotor no registrado | Pacientes ERC sin ajuste proteico | ✅ |
| CVDHazard defaults inventados | Riesgo ASCVD con datos falsos | ✅ |
| Markov HbA1c ≥ 8 = complicaciones | Sobreestimación de riesgo | ✅ |
| FreeTestosterone unreachable | TESTO-001 no disponible | ✅ |
| SCORE2 irrelevante LATAM | Motor inútil | ✅ Eliminado |

---

## Infraestructura de Agentes

| Componente | Estado |
|---|---|
| **AGENTS.md** | ✅ Entry point con contexto completo |
| **7 Skills** | ✅ iec62304, iso13485, clinical-validity, repo-structure, test-coverage, clinical-safety, data-contracts |
| **3 Enforcement Scripts** | ✅ check_pure_python.sh, check_test_coverage.py, check_risk_sync.py |
| **2 Workflows** | ✅ quality-gate, change-control |
| **.cursorrules** | ✅ Configuración para Cursor IDE |

---

## Métricas del Proyecto

| Métrica | Valor |
|---|---|
| Motores registrados | **32** |
| Tests passing | **208** |
| Coverage | **100%** de motores con tests |
| Líneas Encounter | **320** (de 586, -45%) |
| Calculators | **7** value objects |
| Medicamentos en DB | **142** |
| Interacciones | **163** |
| Contraindicaciones | **35** |
| Ajustes renales | **18** |
| Efectos adversos | **47** |
| Mapeos ICD-10→11 | **56** |
| Intervenciones longevidad | **32** |

---

## Próximos Pasos

### Sprint 9: Frontend + VPS
- [ ] **Frontend para 32 motores** — ResultsViewer con tabs por categoría
- [ ] **Formulario de medicamentos expandido** — con autocompletado desde DB
- [ ] **Formulario Women's/Men's Health** — condicional por género
- [ ] **Migración a VPS** — Docker compose, PostgreSQL, Caddy TLS

### Sprint 10: Longevidad + Genómica
- [ ] **GrimAge** — Superior a PhenoAge para mortalidad
- [ ] **DunedinPACE** — Pace of aging epigenético
- [ ] **Nutritional Genomics** — MTHFR, FTO, APOE, TCF7L2
- [ ] **Pharmacogenomics** — CYP2C9, CYP2D6 para metabolismo de drogas

### Sprint 11: Modelo de Datos + Misc
- [ ] Campos hormonales: IGF-1, DHEA-S, Estradiol, LH, FSH, Prolactina
- [ ] OrganicAcidsMotor — Intermediarios metabólicos
- [ ] GutHealthMotor — Calprotectina, zonulina, microbioma
- [ ] **Migración definitiva a ICD-11** — usando crosswalk existente

---

**Comando de Inicio:** "Continuamos con Sprint 9."
