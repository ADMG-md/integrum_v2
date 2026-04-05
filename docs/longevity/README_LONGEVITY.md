# Integrum Longevity Module: Governance & Clinical Scope

The Integrum Longevity Module is a specialized clinical extension designed for high-precision metabolic and biological age tracking. This document outlines its scope, limitations, and regulatory standing to ensure safe and transparent usage in SaMD environments.

## 1. Clinical Scope & Intention

### 1.1 Informative Nature
The primary goal of the Longevity Module, specifically the **Biological Age Motor (PhenoAge)**, is to provide an estimated physiological age based on standard blood biomarkers. It is intended to be used as an **educational and prognostic tracking tool**, not as a primary diagnostic instrument.

### 1.2 "Optimal" vs "Normal" Ranges
In various motors (e.g., Lipidomics, Hormonal), Integrum utilizes "Optimization Ranges" alongside standard clinical reference ranges. 
- **Standard (Normal)**: Based on laboratory reference values for disease diagnosis.
- **Optimization (Longevity)**: Based on epidemiological evidence (e.g., Levine 2018, Longo) for healthspan extension.

> [!WARNING]
> Optimization ranges should never supersede standard clinical diagnosis. Patients within "Normal" but outside "Optimal" ranges are not necessarily pathological.

## 2. Scientific Basis: PhenoAge (Levine 2018)

The core estimation uses the **Levine (2018) regression model** trained on NHANES III data. 
- **Methodology**: Elastic-net Gompertz regression using 10 variables (Age + 9 Biomarkers).
- **Transformation**: Uses the corrected Gompertz constants (0.00553 and 0.09165) as specified in the peer-reviewed methodology.
- **Validation**: Verified against reference benchmarks in `test_longevity_precision.py`.

## 3. Regulatory Limitations

### 3.1 SaMD Classification
As of V2.5, the Longevity Module is a **Non-Certified Draft Module** (TRL 5). Its outputs are labeled as "Investigative/Experimental" in the Design History File (DHF).

### 3.2 Risk Management
Integrated under ISO 14971 with specific mitigations for:
- **H-009**: Over-interpretation of BioAge metrics.
- **H-012**: Over-optimization leading to unnecessary medicalization.
- **H-013**: Misunderstanding of hormonal optimization boundaries.

## 4. User Guidance for Clinicians
- Always correlate PhenoAge with the patient's full clinical history.
- Use the "Age Delta" as a trend indicator over multiple consultations rather than a single-point truth.
- Ensure patients understand that BioAge is modifiable through lifestyle and targeted intervention.
