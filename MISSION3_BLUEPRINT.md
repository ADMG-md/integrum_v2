# MISSION 3: MILITARY-GRADE CLINICAL ENGINE REFACTORING

Este documento define el protocolo de ejecución para la Misión 3. Debe ser inyectado como instrucción de sistema antes de tocar una sola línea de lógica algorítmica.

---

## 🎖️ Objetivo Estratégico
Trasplantar los cerebros de **Acosta (Metabolic Phenotypes)** y **EOSS (Edmonton Staging)** desde el caos de V1 hacia una arquitectura de **"Motores Puros"** en V2, garantizando determinismo absoluto, trazabilidad regulatoria y paridad total con los nuevos contratos de datos FHIR/CIE-11.

## 📐 Estándares de Ingeniería (The Iron Rules)

### 1. Entrada de Datos Inmaculada (FHIR Accessor)
Queda prohibido el acceso directo a diccionarios o `data.get()`. Los motores deben recibir un objeto `Encounter` y usar métodos de extracción estandarizados:
- **Incorrecto:** `if data['has_diabetes_type2']: ...` 
- **Correcto:** `if encounter.has_condition("5A11"): ...` (CIE-11 para DM2).
- **Correcto:** `weight = encounter.get_observation("29463-7").value` (LOINC para Peso).

### 2. Pureza Funcional y Determinismo
Los motores deben ser **funciones puras**:
- **Input:** `Encounter` snapshot.
- **Output:** `AdjudicationResult` (Calculated Value + Confidence + Evidence Array).
- **Regla:** No se permiten llamadas a DB, ni uso de variables globales, ni efectos secundarios dentro de la lógica de cálculo.

### 3. Evidencias Auditables (Safe Harbor / Explainability)
Cada resultado entregado por el motor debe ir acompañado de su **Justificación Clínica**:
```json
{
  "calculated_value": "Phenotype C - Hedonic",
  "evidence": [
    { "type": "Observation", "code": "TFEQ-HEDONIC", "value": 18, "threshold": ">15" },
    { "type": "Condition", "code": "F50.81", "display": "Binge Eating Disorder" }
  ]
}
```

## 🏗️ Fases de Ejecución

### Fase 3.1: Scaffolding de Motores Base
Definir la clase `BaseClinicalMotor` de la cual heredarán todos los demás. Debe implementar:
- `validate()`: Verifica si el `Encounter` tiene los datos mínimos para correr.
- `compute()`: El algoritmo puro.
- `explain()`: Genera la narrativa técnica de soporte.

### Fase 3.2: Migración de Lógica Acosta (The Core)
Reescribir el clasificador de fenotipos basándose en los metadatos de las observaciones (Laboratorios y Psicometría).
- **Prioridad:** Calibración de umbrales para el Fenotipo D (Músculo/Sarcopenia) y C (Hambre Hedónica).

### Fase 3.3: Migración de Lógica EOSS (The Staging)
Refactorizar el sistema de estadiaje para que filtre por los códigos de sistemas biológicos (Cardiovascular, Renal, Psicológico) definidos en el nuevo Mapa de Mediciones.

---

## 🚨 Control de Calidad y Veto
Un motor NO se considera terminado hasta que:
1. Pasa un test de **Determinismo:** 100 ejecuciones con los mismos datos = 100 respuestas idénticas bit-a-bit.
2. Posee **Zero Dead Code:** Se elimina toda la lógica de V1 que dependía de variables booleanas antiguas.
3. El **Reporting Service** puede leer su `AdjudicationResult` y generar una frase perfecta.
