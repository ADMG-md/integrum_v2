# Integrum V2 - Clinical Decision Support System (CDSS)

## Project Overview

**Integrum V2** is a clinical decision support system (CDSS) designed for obesity and cardiometabolic health management. It is classified as a **SaMD (Software as a Medical Device)** under **IEC 62304 Class B** regulatory framework.

The system integrates 48+ clinical "motors" (specialized AI/algorithmic engines) that analyze patient data to provide:
- Phenotype classification (Acosta, EOSS staging)
- Risk assessment (cardiovascular, renal, metabolic)
- Drug interaction detection
- Laboratory suggestion recommendations
- Personalized treatment plans

---

## Technical Architecture

### Backend Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL 16 (Alpine)
- **ORM**: SQLAlchemy async
- **Validation**: Pydantic V2

### Frontend Stack
- **Framework**: Next.js 14, React 18
- **Styling**: TailwindCSS
- **Language**: TypeScript

### Infrastructure
- **Proxy**: Caddy 2 (automatic TLS)
- **Architecture**: Monorepo structure (`apps/backend/`, `apps/frontend/`)

---

## Clinical Motors (48 Total)

### Core Engines (7)
| Motor | Purpose | Evidence |
|-------|---------|----------|
| AcostaPhenotypeMotor | Obesity phenotype classification | Acosta et al., 2021 |
| EOSSStagingMotor | Edmonton Obesity Staging System | Sharma et al., 2009 |
| SarcopeniaMonitorMotor | Muscle mass evaluation | EWGSOP2 2019 |
| BiologicalAgeMotor | Epigenetic age calculation | Levine et al., 2018 |
| MetabolicPrecisionMotor | Insulin resistance indices | Multiple sources |
| DeepMetabolicProxyMotor | Metabolic signatures | Johnson 2019 |
| Lifestyle360Motor | Lifestyle assessment | WHO 2020 |

### Specialty Engines (41)
Specialty engines cover: anthropometry, endocrine, hypertension, inflammation, sleep apnea, lipid risk, NAFLD staging, frailty, drug interactions, cancer screening, and more.
*   **PrecisionNutritionMotor**: Generates phenotype-adapted dietary strategies (e.g., Hungry Brain, Hepatic IR).
*   **PharmaPrecisionMotor**: Orchestrates pharmacological safety (hard-stops) and efficacy (organ benefit).

---

## LaboratorySuggestionMotor (Featured)

The **LaboratorySuggestionMotor** is our most sophisticated engine for clinical laboratory optimization.

### Capabilities

1. **Context-Aware Suggestions**
   - Analyzes available lab data
   - Identifies clinical gaps
   - Recommends appropriate tests

2. **Condition-Based Recommendations**
   - Diabetes → HbA1c monitoring (ADA 2024)
   - Hypertension → Lipid panel (ACC/AHA 2018)
   - CKD → eGFR + albuminuria (KDIGO 2024)
   - NAFLD → Liver function + FIB-4

3. **Medication Monitoring**
   - Metformin → Renal function (FDA 2017)
   - Statins → Liver enzymes
   - SGLT2 inhibitors → Renal + electrolytes
   - GLP-1 agonists → Lipase/Amylase

4. **Age-Based Screening**
   - 18-40: Basic metabolic panel
   - 40-45: Lipid screening (USPSTF)
   - 45-50: Colorectal cancer screening
   - 50-60: Mammography, cervical cancer
   - 60-65: Bone densitometry (DXA)
   - 65+: Cognitive assessment

5. **Pediatric Support**
   - 0-2 years: Neonatal screening (AAP)
   - 2-10 years: Anemia screening
   - 10-18 years: Lipid screening (NCEP)

### Output Example

```json
{
  "calculated_value": "Panel Sugerido: 3 elementos",
  "estado_ui": "PROBABLE_WARNING",
  "action_checklist": [
    {
      "category": "diagnostic",
      "priority": "high",
      "task": "Solicitar: Perfil Metabólico Básico",
      "rationale": "Panel base requerido para evaluación cardiometabólica. Frecuencia: según necesidad."
    },
    {
      "category": "diagnostic",
      "priority": "medium",
      "task": "Solicitar: Monitoreo: Función renal (Creatinina + eGFR)",
      "rationale": "Metformina contraindicada si eGFR <30. Evaluar función renal antes de continuar. Frecuencia: semestral. FDA Label 2017, ADA 2024"
    },
    {
      "category": "diagnostic",
      "priority": "low",
      "task": "Screening: Perfil lipídico",
      "rationale": "USPSTF 2021: screening dislipidemia adulto. Iniciar a los 40 años. Frecuencia: anual. USPSTF 2021, Grade B"
    }
  ],
  "metadata": {
    "age": 50,
    "gender": "male",
    "suggestions": [...]
  }
}
```

---

## Validation & Quality Assurance

### Test Coverage
- **Total tests**: 540 unit tests
- **Coverage**: 100% pass rate
- **Framework**: pytest

### Regulatory Compliance
- **IEC 62304**: Class B software lifecycle
- **ISO 14971**: Risk management
- **FHIR R4**: Interoperability layer
- **LOINC/SNOMED**: Clinical coding standards

### Quality Documents
| Document | Status |
|----------|--------|
| Motor Evidence Registry | ✅ Updated (32/48 validated) |
| Traceability Matrix | ✅ Full coverage |
| Risk Management File | ✅ 51 hazards tracked |
| DHF Index | ✅ Complete |

---

## Key Features for Google AI Studio

### 1. Clinical Reasoning Engine
- 48 specialized motors with evidence-based logic
- Transparent decision-making with requirement IDs
- Confidence scoring and evidence traces

### 2. Laboratory Optimization
- Reduces unnecessary testing (Choosing Wisely guidelines)
- Prioritizes tests by clinical urgency (high/medium/low)
- Context-aware based on conditions, medications, age

### 3. Interoperability
- FHIR R4 export
- OMOP CDM 5.4 support
- LOINC/SNOMED/ATC mappings

### 4. Safety Features
- Drug interaction checking
- Pregnancy contraindication gates
- Pediatric age boundaries
- Gender-specific recommendations

---

## Demo Scenarios

### Scenario 1: Adult with Diabetes
- **Input**: Age 55, Type 2 Diabetes, on Metformin
- **Output**: HbA1c, renal function monitoring suggestions

### Scenario 2: Pediatric Patient
- **Input**: Age 8, no conditions
- **Output**: Anemia/iron deficiency screening recommendation

### Scenario 3: Geriatric Screening
- **Input**: Age 68, male, former smoker
- **Output**: Cognitive assessment, AAA ultrasound, lipid panel

---

## Technology Stack for AI Integration

```python
# Example: Using LaboratorySuggestionMotor
from src.engines.specialty.lab_suggestion import LaboratorySuggestionMotor
from src.engines.domain import Encounter
from src.schemas.encounter import DemographicsSchema, MetabolicPanelSchema

motor = LaboratorySuggestionMotor()
encounter = Encounter(
    id="patient-001",
    demographics=DemographicsSchema(age_years=50, gender="male"),
    metabolic_panel=MetabolicPanelSchema(glucose_mg_dl=110),
    ...
)

result = motor.compute(encounter)
# Returns action_checklist with prioritized suggestions
```

---

## Contact & Documentation

- **Repository**: Internal (Monorepo structure)
- **QMS Documents**: `/docs/qms/`
- **API Documentation**: FastAPI Swagger at `/docs`
- **Test Suite**: 540 tests in `apps/backend/tests/unit/engines/`

---

## Mission Statement

**To provide physicians with evidence-based, context-aware clinical recommendations that improve patient outcomes while reducing unnecessary testing and ensuring regulatory compliance.**

---

*Last updated: 2026-04-17*
*Version: 3.1 (Sprint 10 Completion)*
*Classification: SaMD IEC 62304 Class B*