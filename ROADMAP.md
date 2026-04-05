# Integrum V2: Estado del Proyecto y Roadmap

**Última actualización:** 2026-04-05
**Versión:** 4.1 (TRL 4 — Prototipo de laboratorio)

> **Nota de honestidad técnica:** Integrum V2 es un CDSS prototipo avanzado con capa de exportación FHIR R4 y OMOP CDM 5.4 en estado inicial. No es una "interoperability layer completa". Los motores T3/T4 (DeepMetabolicProxy, Markov, BiologicalAge) son experimentales y no deben usarse para decisiones clínicas autónomas. Ver `docs/qms/motor_evidence_registry.md` para clasificación T1-T4.

---

## Estado Actual

### ✅ Completado

| Fase | Estado | Descripción |
|---|---|---|
| **Misiones 1-13** | ✅ | Backend, UI, SaMD, Security, CI/CD |
| **Sprint 1-8** | ✅ | 38 motores clínicos con evidencia documentada |
| **Sprint 9** | ✅ | FHIR R4 export + OMOP CDM 5.4 ETL prototype |
| **Audit Remediation** | ✅ | 3 VETOs resueltos (Safety x2, QMS x1) |
| **Clinical Mode** | ✅ | Gate T3/T4 para uso regulable |
| **Contract Enforcement** | ✅ | Todos los motores devuelven AdjudicationResult |

---

## Motores Clínicos por Nivel de Evidencia (T1-T4)

### T1 — Validated Clinical Scores (18 motores) — ✅ Export FHIR completo
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| EOSSStagingMotor | Estadiaje de daño por obesidad | Sharma & Kuk 2009 |
| SarcopeniaMonitorMotor | ASMI + masa muscular | EWGSOP2 2019 |
| AnthropometryMotor | WHtR, WHR, BRI | Browning 2010, WHO 2008 |
| HypertensionMotor | Aldosteronismo primario (ARR) | Funder 2016 |
| InflammationMotor | hs-CRP, NLR | Pearson 2003 (AHA/CDC) |
| SleepApneaMotor | STOP-Bang | Chung 2008 |
| FunctionalSarcopeniaMotor | 5xSTS, Grip, Gait, SARC-F | EWGSOP2 2019 |
| FLIMotor | Fatty Liver Index | Bedogni 2006 |
| ApoBApoA1Motor | Ratio ApoB/ApoA1 | INTERHEART (Yusuf 2004) |
| PulsePressureMotor | PP + MAP | Domanski 1999 (JAMA) |
| NFSMotor | NAFLD Fibrosis Score | Angulo 2007 |
| MetforminB12Motor | Screening B12 en metformina | ADA 2024 |
| KFREMotor | Riesgo falla renal | Tangri 2016 |
| CharlsonMotor | Comorbilidad → mortalidad | Charlson 1987 |
| FreeTestosteroneMotor | Testosterona libre | Vermeulen 1999 |
| VitaminDMotor | Estado Vitamina D | Holick 2011 |
| FriedFrailtyMotor | Fenotipo de fragilidad | Fried 2001 |
| CVDHazardMotor | ASCVD 10y (PCE) | ACC/AHA 2013 |

### T2 — Guideline-Based Rules (17 motores) — ⚠️ Export condicional
| Motor | Qué evalúa | Evidencia |
|---|---|---|
| AcostaPhenotypeMotor | Fenotipos de obesidad | Acosta 2021 |
| MetabolicPrecisionMotor | HOMA-IR, TyG, METS-IR | Múltiples fórmulas publicadas |
| Lifestyle360Motor | Sueño, estrés, AF | WHO 2020, AIS |
| EndocrineMotor | TSH, FT4, cortisol | ATA 2014 |
| LaboratoryStewardshipMotor | Ordering inteligente | Ahlqvist 2018, Sniderman 2019 |
| GLP1MonitoringMotor | Monitoreo GLP-1 | STEP 1, SURMOUNT-1 |
| ACEScoreEngine | Trauma como modificador | Felitti 1998 |
| CancerScreeningMotor | Gaps screening | IARC 2016 |
| SGLT2iBenefitMotor | Beneficio cardio-renal | EMPA-REG, CANVAS, DECLARE |
| TyGBMIMotor | Resistencia insulina | Simental-Mendía 2008 |
| CVDReclassifierMotor | Reclassificación CV | ACC/AHA 2018 |
| WomensHealthMotor | SOP, embarazo, menopausia | Rotterdam 2003 |
| MensHealthMotor | Hipogonadismo, próstata | AUA 2018 |
| BodyCompositionTrendMotor | Pérdida masa magra | Heymsfield 2019 |
| ObesityPharmaEligibilityMotor | Elegibilidad AOM | FDA 2024 |
| GLP1TitrationMotor | Titulación GLP-1 | Clinical protocols |
| DrugInteractionMotor | Interacciones, QT, renal | FDA Orange Book |
| ProteinEngineMotor | Dosis proteica | ESPEN 2019 |
| VAIMotor | Visceral Adiposity Index | Amato 2010 |
| CMI Motor | Cardiometabolic Index | Wakabayashi 2015 |
| ClinicalGuidelinesMotor | Inercia clínica | Múltiples guidelines |

### T3 — Research Proxies (3 motores) — ❌ No exportar
| Motor | Qué evalúa | Estado |
|---|---|---|
| BiologicalAgeMotor | PhenoAge (Levine) | Validación retrospectiva, no prospectiva |
| ObesityMasterMotor | Agregador de fenotipo | Internal summary only |

### T4 — Experimental (2 motores) — ❌ No exportar, research only
| Motor | Qué evalúa | Estado |
|---|---|---|
| DeepMetabolicProxyMotor | Proxies metabólicos (GGT, UA, ferritina) | Sin validación externa |
| MarkovProgressionMotor | Progresión diabetes | Matriz de transición interna |

---

## Métricas Reales del Proyecto

| Métrica | Valor |
|---|---|
| Motores registrados | **38** (26 T1/T2 primary + 2 gated + 2 aggregator + 8 specialty) |
| T1 (validated) | **18** |
| T2 (guideline-based) | **17** |
| T3 (research) | **3** |
| T4 (experimental) | **2** |
| Tests passing | **278** |
| Hazards en RMF | **50** |
| Clinical mode | ✅ Implementado (skips T3/T4) |
| Contract enforcement | ✅ Todos devuelven AdjudicationResult |

---

## Próximos Pasos (Priorizados)

### P0 — Validación clínica real (TRL 4→5)
- [ ] Ejecutar paciente sintético con médico real para validación
- [ ] Validar 5 motores T1 contra datos reales de Coecaribe
- [ ] Documentar concordancia motor vs juicio clínico

### P1 — Interoperabilidad formal
- [ ] StructureDefinition FHIR formal + IG empaquetado
- [ ] Validar Bundle contra HAPI FHIR server real
- [ ] ETL OMOP ejecutado contra DB real + DQD + Achilles

### P2 — Cumplimiento regulatorio Colombia
- [ ] Matriz Res. 866/2021
- [ ] Registro RDA ante MinSalud
- [ ] Clasificación SaMD ante INVIMA

### P3 — Frontend + Despliegue
- [ ] ResultsViewer con tabs por categoría
- [ ] Modo clínico (T1/T2 only) vs modo research (todos)
- [ ] Docker compose production-ready

---

**Comando de Inicio:** "Continuamos con validación clínica (P0)."
