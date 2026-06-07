# MISSION 4: DYNAMIC CLINICAL INTAKE & T0 FLOW

Este documento define el protocolo de ejecución para la Misión 4. El objetivo es construir la interfaz de usuario que interactúa con la arquitectura de "Condiciones Estructuradas" y "Observaciones" de V2.

---

## 🎖️ Objetivo Estratégico
Pasar de un formulario de "80 switches" (carnaval visual) a una **Interfaz de Entrada Clínica Dinámica** basada en búsqueda. El doctor ya no busca una casilla; busca una patología en el catálogo CIE-11.

## 📐 Estándares de UI/UX (Premium Standards)

### 1. El Componente "Condition Searcher" (CIE-11)
- **UI:** Un campo de búsqueda con autocompletado (Command Palette style).
- **Lógica:** Al buscar "Diab", el sistema filtra el catálogo maestro de condiciones (`v2_core_types.ts`).
- **Comportamiento:** Al seleccionar una enfermedad, se añade como una "Tag" o "Badge" a la lista de `conditions` del `Encounter`.
- **Atributos:** Cada condición añadida debe permitir marcar su `clinicalStatus` (Activa/Remisión) y su `severity`.

### 2. Formulario de "Observations" Agrupado (Smart Tiers)
- **Core Tiers:** Inputs siempre visibles (Peso, TA, Glucosa, Perfil Lipídico).
- **Smart Labs Drawer:** Una sección expandible para marcadores especiales (SHBG, Cortisol, Aldosterona, etc.). 
- **Trigger UI:** Si el motor de especialidad detecta una sospecha (ej. HTA resistente), el sistema resaltará visualmente este drawer.

### 3. El "Advanced Omics Vault" (Genética & Nutrigenómica)
- **UI:** Apartado colapsado por defecto. Se activa solo si el clínico confirma la disposición de estudios genéticos (FTO, MC4R, etc.).

### 4. Feedback Instantáneo (The Adjudication Preview)
- **UI:** Panel lateral "AI Clinical Insights & Omics Fusion".
- **Comportamiento:** Muestra el Fenotipo Acosta y Estadio EOSS en vivo.
- **Transparencia:** Listado de evidencias (LOINC/CIE-11) que sustentan el hallazgo.

## 🏗️ Fases de Ejecución

### Fase 4.1: Setup de Formulario Maestro (React Hook Form + Zod)
Definir el esquema Zod que mapee exactamente al `ClinicalEncounter` de V2. Configurar la persistencia local para no perder datos por refresh.

### Fase 4.2: Construcción del "Diagnosis Multi-Select" (CIE-11)
Implementar el componente de selección de patologías. Usar un catálogo local (o mock API) de los diagnósticos más comunes para Obesity/Metabolic Health.

### Fase 4.3: Integración E2E (Frontend -> Backend)
Conectar el envío del formulario con el endpoint de creación de V2, asegurando que el JSON enviado sea 100% conforme a FHIR.

---

## 🚨 Control de Calidad
1. **Zero Flattening:** No se permiten inputs que no mapeen a los arreglos de `conditions` u `observations`.
2. **Premium Look:** Uso estricto de `shadcn/ui`, Dark Mode impecable y micro-interacciones (hovers, transiciones).
3. **Validación de Tipos:** El `package.json` debe pasar un check de TypeScript sin errores de mapeo contra el SSOT.
