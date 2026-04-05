## Segmento 25: Activación Científica PhenoAge (Levine) [x]
- [x] Implementar Coeficientes de Regresión Levine 2018 en `bio_age.py`.
- [x] Implementar Transformación de Gompertz (Mortality -> BioAge).
- [x] Validar Benchmarks contra Paper Original (test_longevity_precision.py).
- [x] Extender RMF con Riesgos H-012 y H-013 (Longevity Optimization).
- [x] Publicar README_LONGEVITY.md (Gobernanza y Limitaciones).

## Segmento 26: Master de Obesidad y Saneamiento de Lógica Oculta [x]
- [x] Relocalizar Lógica de 'Legacy Motors' (Kleiber -> metabolic.py, Cox/Markov -> risk.py).
- [x] Implementar 'Honest Gating' (NotImplementedError) en motores de riesgo no verificados.
- [x] Desarrollar 'ObesityMasterMotor' (Agregador de Acosta, EOSS, Sarcopenia).
- [x] Refactorizar 'SpecialtyRunner' para ejecución en DOS FASES (Primaria -> Agregación).
- [x] Eliminar 'legacy_motors.py' y verificar Gating Estricto.
- [x] Implementar Suite de V&V 'Obesity Clinical Story'.

## Segmento 27: Frontend Reboot (Visibilidad TRL 5) [x]
- [x] Eliminar 'TheGate.tsx' y refactorizar ruteo inicial en 'page.tsx'.
- [x] Implementar Widget de 'Longevity Clock' (PhenoAge vs Edad Cronológica).
- [x] Implementar Banner de 'Clinical Story' (Headline del ObesityMaster).
- [x] Refactorizar 'AdjudicationViewer' para mapeo dinámico de motores (Quitar pilares estáticos).
- [x] Aplicar Estética Premium (Glassmorphism & Outfit Font) en todos los widgets.
- [x] Smoke Test de navegación y renderizado de DTOs.

## Segmento 28: Remediación Post-Auditoría (V2.6 Hardening) [x]
- [x] Ejecutar Auditoría Profunda (IEC 62304 / ISO 14971).
- [x] Corregir bug de sobreescritura de 'CODES' en Acosta Motor. (R-01)
- [x] Corregir lógica de ASMI (Appendicular Proxy) en Sarcopenia. (R-02)
- [x] Implementar Fail-Fast en VaultService (Seguridad de Llaves). (R-03)
- [x] Añadir disparador biométrico (BMI) a EOSS Staging. (R-04)
- [x] Eliminar silent fallback en BioAge (H-007 compliance). (R-05)
- [x] Mapear 'cvd_risk_category' al Obesity Master. (R-06)
- [x] Sincronizar Traceability Matrix y RMF con hallazgos H-014/H-015.
- [x] Actualizar tests legacy (Encounter constructors modernizados).
- [x] Crear audit trail: docs/qms/audit_20260330_cortex_remediation.md

## Segmento 29: End-To-End Clinical Flow (Route C) [x]
- [x] Backend: Arreglar `EncounterCreate` schemas duplicados.
- [x] Backend: Construir `Encounter` con esquemas requeridos en el endpoint POST (Fix crash).
- [x] Frontend: Añadir inputs faltantes de PhenoAge (Albumin, ALP, MCV, etc.) y tab "Longevity".
- [x] Frontend: Aplicar diseño Glassmorphism premium a la página de consulta.
- [x] Integración E2E: Validar procesamiento exitoso desde la UI hasta el AdjudicationViewer.

## Segmento 30: Route B "Depth" - Motores Predictivos (CVD/Markov) [x]
- [x] Implementar **CVDHazardMotor** usando Pooled Cohort Equations (ACC/AHA 2013).
- [x] Limitar ejecución de CVD matemática al rango validado de 40 a 79 años (ACC/AHA 2019).
- [x] Definir estructura estocástica para **MarkovProgressionMotor** pero bloquear cálculo con estado `experimental_blocked`.
- [x] Alinear salidas DTO con campos `estado_ui="EXPERIMENTAL_CALCULATION"` para CDS Compliance (FDA 2026).
- [x] Implementar V&V `test_sanitized_risk_motors.py` (SR-CVD-01, SR-MKV-01).

## Segmento 31: Deep Audit & Remediation (Route B) [x]
- [x] **ObesityMasterMotor:** Removida la dependencia automática de MHO sobre `cvd_risk_category` (evitando derivar diagnósticos "hard" desde motores experimentales para cumplir FDA 2026).
- [x] **SpecialtyRunner:** Corregida la extracción de metadatos `patient_age` y `sex` desde el frontend, evitando que pacientes sin edad cayeran en el fallback "40" saltando el gate de seguridad.
- [x] **CVDHazardMotor:** Integración de la nota documental para ESC 2021 SCORE2 en la explicación del DTO.
- [x] **Smoke Test Scrappy:** Validada resiliencia y "Honest Gating" para pacientes sin laboratorios (Fixed bugs in Acosta, BioAge and Risk imports).
