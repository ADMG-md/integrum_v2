# MISSION 3.5: SPECIALTY MICRO-ENGINES (THE PRECISION LAYER)

Este documento define el protocolo para trasplantar la inteligencia clínica de especialidades (HTA, Diabetes, Endocrino) a Integrum V2.

---

## 🎖️ Objetivo Estratégico
Convertir a Integrum V2 en un detective clínico. No solo evaluamos obesidad, sino que buscamos **Causas Secundarias** y riesgos metabólicos profundos usando los micro-motores específicos de V1 pero con arquitectura pura de V2.

## 📐 El Catálogo de Especialidades a Refactorizar

### 1. Motor de Hipertensión (HTA) Secundaria
- **ARR Screening:** Evaluar el ratio Aldosterona/Renina usando códigos LOINC.
- **Hemodynamics:** Análisis de flujo y volumen (`DuarteVolumeMotor`).
- **Trigger:** Se activa si existe la condición `I10` (HTA) o mediciones de presión elevadas.

### 2. Motor de Diabetes y Resistencia (Metabolic)
- **Mets-IR & TyG Index:** Evaluación de resistencia a la insulina sin necesidad de clamp, usando Triglicéridos y Glucosa.
- **Disposition Index:** Evaluación de la función de la célula beta (C-Peptide + Glucose).

### 3. Motor de Salud Hormonal y Eje Gonadal (NEW)
- **PCOS Engine (SOP):** Evaluación de Criterios de Rotterdam. Requiere: Testosterona Total, SHBG (para FAI - Index de Andrógenos Libres), DHEA-S y clínica de hirsutismo/irregularidad.
- **Male Hypogonadism Filter:** Cálculo de Testosterona Bioavailable (usando Albúmina + SHBG). Vital para pacientes con obesidad central marcada.

### 4. Motor Endocrino y Adrenal (Precision Endocrine)
- **Thyroid Engine:** Clasificar hipotiroidismo (Subclínico vs Clínico) usando TSH y T4 Libre.
- **Cushing's Screening:** Análisis de Cortisol libre urinario o salival si hay sospecha clínica (Adiposidad central + Estrías purpúreas + Giba dorsal).

### 5. Motor de Inflamación y Riesgo Residual (NEW)
- **Meta-Inflammation Score:** Cálculo basado en PCR ultra-sensible (hs-CRP), Ferritina y NLR (Neutrophil-to-Lymphocyte Ratio). Predice resistencia al tratamiento.

### 6. Auditoría Farmacológica (Medication-Induced Weight Gain)
- **Obese-Safe Audit:** Escaneo de `MedicationStatement` para detectar Betabloqueadores antiguos, INS, Antipsicóticos o Corticoides que pueden estar saboteando el peso.

### 7. Capa de Ómicas y Genética (Future-Proofing) [NEW]
- **Nutrigenomic Risk:** Sección para variantes comunes (FTO, MC4R, PPARG). Permite alertar sobre resistencia a la pérdida de peso o saciedad alterada.
- **Genetic Red Flags:** Alertas automáticas para derivación a genética si el paciente presenta obesidad sindrómica (PWS, Bardet-Biedl).
- **Proteomic Exploratory:** Estructura preparada para marcadores de nueva generación (ej. GDF15) si llegaran a estar disponibles.

## 📐 El Concepto de "Laboratorios Especiales" y Triggers

### ¿Dónde vive este dato?
- **T0 (Baseline):** Si el paciente trae laboratorios previos (SHBG, Insulina, Cortisol) o pruebas genéticas, se capturan aquí.
- **Tn (Follow-up):** Si el motor T0 detecta una "Alerta de Sospecha", el sistema generará una **Recomendación de Orden Médica**.

### UI Strategy (Smart Labs Drawer & Omics Vault)
Para no saturar la pantalla de T0:
1. **Inputs Core:** Siempre visibles.
2. **Specialty Drawer:** Expandible para laboratorios de profundización (SHBG, Cortisol, etc.).
3. **Advanced Omics Vault:** Un apartado opcional y "colapsado" por defecto para información genética y nutrigenómica. Solo se activa si el médico marca explícitamente "Dispone de pruebas genéticas".

## 📐 Estándares de Implementación V2

1. **Protocolo "Plug-and-Play":** Cada motor debe ser una clase independiente que herede de `BaseClinicalMotor`.
2. **Validación Automática:** Cada motor debe declarar qué `Observations` (LOINC) necesita. Si el dato no existe, el motor se "apaga" silenciosamente sin romper el reporte.
3. **Internal Flags:** Los resultados deben alimentar el campo `specialty_findings` del reporte final, permitiendo alertas cruzadas.

---

## 🏗️ Instrucción de Acción
"Ejecuta la Misión 3.5: Refactorización de Micro-Motores de Especialidad. Comienza implementando el Singleton del SpecialtyRunner que orquestará estos motores bajo el nuevo patrón de acceso a datos."
