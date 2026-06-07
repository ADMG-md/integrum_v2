# Backend Schema & Clinical Domain Specification
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Purpose
This document specifies the backend data schemas, clinical domain models, and physiological guardrails used in **Integrum V2** for HTTP serialization and engine validation. It serves as the **Software Data Design Specification** under IEC 62304 §5.4.3.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial backend schema specification baseline. |

---

## 2. Core Clinical Data Contracts (Pydantic V2)

The backend exposes a highly structured Pydantic schema hierarchy defined in [encounter.py](file:///Users/antonymolinagarrido/Projects/integrum_v2/apps/backend/src/schemas/encounter.py) to manage the patient lifecycle and clinical audits.

```
┌────────────────────────────────────────────────────────┐
│                   EncounterCreate Schema               │
├────────────────────────────────────────────────────────┤
│  • patient_id: str                                     │
│  • reason_for_visit: str                               │
│  • status: str ("DRAFT" | "FINAL")                     │
├───────────────────────┬────────────────────────────────┤
│                       │                                │
│  ┌────────────────────▼───┐    ┌───────────────────────▼──┐
│  │    BiometricsSchema    │    │  MetabolicPanelSchema    │
│  │ (Weight, SBP/DBP, Grip)│    │ (HbA1c, Lipids, eGFR)    │
│  └────────────────────────┘    └──────────────────────────┘
│  ┌────────────────────────┐    ┌──────────────────────────┐
│  │   PsychometricsSchema  │    │      LifestyleSchema     │
│  │  (PHQ-9, GAD-7, ACE)   │    │  (Sleep hrs, Activity)   │
│  └────────────────────────┘    └──────────────────────────┘
│  ┌────────────────────────┐    ┌──────────────────────────┐
│  │   List[Condition]      │    │     List[Medication]     │
│  │  (ICD-10 / SNOMED-CT)  │    │  (ATC, Obesity-inducing) │
│  └────────────────────────┘    └──────────────────────────┘
└────────────────────────────────────────────────────────┘
```

---

## 3. Physiological Validation Limits (Biological Guardrails)

All observations must pass the `validate_biological_limits` validator to prevent corrupted, impossible, or unsafe clinical values from reaching the decision support logic.

| Observation Code | Parameter | Lower Limit | Upper Limit | Units |
|---|---|---|---|---|
| `AGE-001` | Chronological Age | 0 | 125 | Years |
| `29463-7` | Body Weight | 2 | 400 | kg |
| `8302-2` | Body Height | 30 | 250 | cm |
| `WAIST-001` | Waist Circumference | 30 | 300 | cm |
| `8480-6` | Systolic Blood Pressure | 60 | 250 | mmHg |
| `2339-0` | Blood Glucose | 20 | 600 | mg/dL |
| `TSH-001` | Thyroid Stimulating Hormone | 0.01 | 100 | uIU/mL |
| `FT4-001` | Free Thyroxine (T4) | 0.1 | 10 | ng/dL |
| `HS-CRP-001` | High-Sensitivity CRP | 0.01 | 100 | mg/L |
| `FER-001` | Ferritin | 1 | 10000 | ng/mL |
| `UACR-001` | Urine Albumin-to-Creatinine | 0.0 | 3000 | mg/g |
| `LIPASE-001` | Serum Lipase | 0.0 | 5000 | U/L |
| `GRIP-STR-R/L`| Grip Strength (R/L) | 5.0 | 80.0 | kg |
| `5XSTS-SEC` | 5-Times Sit-to-Stand Test | 3.0 | 120.0 | Seconds |

**Universal Guardrail:** Any unmapped numeric observation must fall strictly between `-50` and `1000` to be accepted.

---

## 4. Cross-Field Coherence Validation Rules

To prevent user entry typos, the system implements multi-variable coherence validations:

### 4.1 Blood Pressure Coherence Rule
*   **Formula:** $\text{Systolic BP} > \text{Diastolic BP}$
*   **Logic:** A pulse pressure of $\le 0$ is physiologically impossible. If systolic blood pressure is less than or equal to diastolic blood pressure, a validation error is thrown.

### 4.2 Body Mass Index (BMI) Coherence Rule
*   **Formula:** $\text{BMI} = \frac{\text{Weight (kg)}}{\left(\frac{\text{Height (cm)}}{100}\right)^2}$
*   **Logic:** Prevents the common error of entering height in meters (e.g., `1.75`) instead of centimeters (`175`), which leads to artificially high BMI computations. The system rejects any inputs yielding a calculated $\text{BMI} < 10$.

---

## 5. Output Schema & Evidence Traceability

Calculations processed by the clinical engines must return a structured response adhering to the `AdjudicationResultSchema` format, ensuring regulatory auditability.

```json
{
  "calculated_value": "Stage 2 Obesity",
  "confidence": 1.0,
  "requirement_id": "SR-EOS-02",
  "evidence": [
    {
      "parameter": "HTN-Diagnosis",
      "value": "Confirmed active (I10)",
      "source": "Encounter Conditions"
    }
  ],
  "estado_ui": "PROBABLE_WARNING",
  "action_checklist": [
    {
      "priority": "high",
      "task": "Review secondary hypertension screening panel",
      "rationale": "Patient has Stage 2 hypertension criteria active."
    }
  ],
  "integrity_hash": "a1f8c6aa6d53488cb094c61c93526582"
}
```

*   **requirement_id:** Direct mapping to the clinical requirements matrix (IEC 62304 traceability link).
*   **integrity_hash:** Cryptographic proof that the computation matches the registered engine code version.
