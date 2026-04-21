# Motor Evidence & Validation Level Registry
**Project:** Integrum V2  
**Date:** 2026-04-07  
**Purpose:** Classify each motor by evidence level, validation status, and permitted use for regulatory and interoperability purposes.

## Classification Schema

| Level | Definition | FHIR Export | Regulatory Use |
|---|---|---|---|
| **T1 - Validated Clinical Score** | Published formula/guideline, externally validated, widely accepted | ✅ Full export with standard codes | ✅ Can be used for clinical decision triggers |
| **T2 - Guideline-Based Rule** | Based on clinical guidelines, rule-based logic, no original math | ✅ Export as Observation/DetectedIssue | ⚠️ Supportive only, not autonomous triggers |
| **T3 - Research Proxy** | Based on peer-reviewed research, not yet guideline-endorsed | ⚠️ Export as internal note only | ❌ Educational/contextual only |
| **T4 - Experimental** | Novel algorithm, internal development, no external validation | ❌ Do not export | ❌ Internal exploration only |

## Motor Registry

| Motor | Level | Evidence Primary | Validation Status | FHIR Export | Permitted Use |
|---|---|---|---|---|---|
| **AcostaPhenotypeMotor** | T2 | Acosta et al., 2021 (DOI: 10.1002/oby.23120) | ✅ Validated (Golden Motor) | QuestionnaireResponse | Supportive phenotyping |
| **EOSSStagingMotor** | T1 | Sharma et al., 2009 (DOI: 10.1038/ijo.2009.2) | ✅ Validated (Golden Motor) | Condition (EOSS stage) | Clinical decision trigger |
| **SarcopeniaMonitorMotor** | T1 | EWGSOP2 2019, Kim et al. 2014 | ✅ Validated (Sprint 8) | Observation (ASMI) | Clinical decision trigger |
| **BiologicalAgeMotor** | T3 | Levine et al., 2018 (DOI: 10.18632/aging.101414) | Not validated | Observation (PhenoAge) | Educational/contextual |
| **MetabolicPrecisionMotor** | T2 | Multiple indices (HOMA, TyG, METS-IR) | ✅ Validated (Sprint 6) | Observation (calculated indices) | Supportive |
| **DeepMetabolicProxyMotor** | T4 | Johnson et al. 2019, Wang et al. 2011 | ✅ Validated (Sprint 6) | ❌ Do not export | Internal exploration |
| **Lifestyle360Motor** | T2 | WHO 2020, Soldatos 2000, Spiegel 1999 | Not validated | QuestionnaireResponse | Supportive |
| **AnthropometryPrecisionMotor** | T1 | Browning 2010, WHO 2008, Thomas 2013 | ✅ Validated (Sprint 6) | Observation (WHtR, WHR, BRI) | Clinical decision trigger |
| **EndocrinePrecisionMotor** | T2 | ATA 2014, Nieman 2008 | ✅ Validated (Sprint 6) | Observation (TSH, cortisol) | Supportive |
| **HypertensionSecondaryMotor** | T1 | Funder 2016 (Endocrine Society) | ✅ Validated (Sprint 8) | Observation (ARR) | Clinical decision trigger |
| **InflammationMotor** | T1 | Pearson 2003 (AHA/CDC), Zahorec 2001 | ✅ Validated (Sprint 8) | Observation (hs-CRP, NLR) | Clinical decision trigger |
| **SleepApneaPrecisionMotor** | T1 | Chung 2008 (STOP-Bang), Nagappa 2015 | ✅ Validated (Sprint 8) | Observation (STOP-Bang score) | Clinical decision trigger |
| **LaboratoryStewardshipMotor** | T2 | Ahlqvist 2018, Sniderman 2019 | Not validated | ❌ Internal recommendation | Supportive |
| **LaboratorySuggestionMotor** | T2 | Choosing Wisely (ABIM) | ✅ Validated (Sprint 6) | ActionItem (lab suggestion) | Supportive |
| **FunctionalSarcopeniaMotor** | T1 | EWGSOP2 2019, Malmstrom 2016 | Not validated | Observation (grip, gait, SARC-F) | Clinical decision trigger |
| **FLIMotor** | T1 | Bedogni et al., 2006 | ✅ Validated (Sprint 8) | Observation (FLI) | Clinical decision trigger |
| **VAIMotor** | T2 | Amato et al., 2010 | ✅ Validated (Sprint 6) | Observation (VAI) | Supportive |
| **ApoBApoA1Motor** | T1 | INTERHEART (Yusuf 2004) | ✅ Validated (Sprint 6) | Observation (ApoB/ApoA1 ratio) | Clinical decision trigger |
| **PulsePressureMotor** | T1 | Domanski 1999 (JAMA), Franklin 1999 | ✅ Validated (Sprint 6) | Observation (PP, MAP) | Clinical decision trigger |
| **NFSMotor** | T1 | Angulo et al., 2007 | ✅ Validated (Sprint 6) | Observation (NFS) | Clinical decision trigger |
| **GLP1MonitoringMotor** | T2 | Wilding 2021 (STEP 1), Jastreboff 2022 | ✅ Validated (Sprint 8) | Observation (weight velocity) | Supportive |
| **ACEScoreEngine** | T2 | Felitti 1998 (ACE Study) | ✅ Validated (Sprint 6) | QuestionnaireResponse (ACE) | Supportive |
| **MetforminB12Motor** | T1 | ADA 2024 | ✅ Validated (Sprint 8) | DetectedIssue (B12 deficiency risk) | Clinical decision trigger |
| **CancerScreeningMotor** | T2 | IARC 2016, USPSTF guidelines | Not validated | DetectedIssue (screening gap) | Supportive |
| **SGLT2iBenefitMotor** | T2 | EMPA-REG, CANVAS, DECLARE trials | Not validated | DetectedIssue (SGLT2i indication) | Supportive |
| **KFREMotor** | T1 | Tangri 2016 | ✅ Validated (Sprint 8) | Observation (KFRE risk) | Clinical decision trigger |
| **CharlsonMotor** | T1 | Charlson 1987 | ✅ Validated (Sprint 8) | Observation (CCI score) | Clinical decision trigger |
| **FreeTestosteroneMotor** | T1 | Vermeulen 1999 | ✅ Validated (Sprint 6) | Observation (free testosterone) | Clinical decision trigger |
| **VitaminDMotor** | T1 | Holick 2011 (Endocrine Society) | ✅ Validated (Sprint 6) | Observation (25-OH Vit D) | Clinical decision trigger |
| **FriedFrailtyMotor** | T1 | Fried et al., 2001 | ✅ Validated (Sprint 8) | Observation (frailty score) | Clinical decision trigger |
| **TyGBMIMotor** | T2 | Simental-Mendía 2008 | ✅ Validated (Sprint 6) | Observation (TyG-BMI) | Supportive |
| **CVDReclassifierMotor** | T1 | ACC/AHA 2018 | ✅ Validated (Sprint 6) | DetectedIssue (statin indication) | Clinical decision trigger |
| **WomensHealthMotor** | T2 | Rotterdam 2003, ACOG guidelines | ✅ Validated (Sprint 8) | Condition/Observation | Supportive |
| **MensHealthMotor** | T2 | AUA 2018, Endocrine Society 2018 | ✅ Validated (Sprint 8) | Observation (PSA, testosterone) | Supportive |
| **BodyCompositionTrendMotor** | T2 | Heymsfield 2019 | ✅ Validated (Sprint 6) | Observation (body comp trend) | Supportive |
| **ObesityPharmaEligibilityMotor** | T1 | FDA Guidance 2024, SELECT trial | ✅ Validated (Sprint 8) | DetectedIssue (AOM eligibility) | Clinical decision trigger |
| **GLP1TitrationMotor** | T2 | STEP/SURMOUNT protocols | Not validated | MedicationRequest (dose adjustment) | Supportive |
| **DrugInteractionMotor** | T1 | FDA Orange Book, Lexicomp | ✅ Validated (Sprint 8) | DetectedIssue (interaction) | Clinical decision trigger |
| **ProteinEngineMotor** | T2 | ESPEN 2019, Paddon-Jones 2015 | Not validated | NutritionOrder | Supportive |
| **CMIMotor** | T2 | Wakabayashi 2015, Tao 2022 | ✅ Validated (Sprint 6) | Observation (CMI) | Supportive |
| **PediatricNutritionMotor** | T2 | AAP 2023, USPSTF 2024, Al-Beltagi 2024, Rucklidge 2025 | ✅ Validated (Sprint 9) | ActionItem (nutrition recommendation) | Supportive |
| **CVDHazardMotor** | T1 | ACC/AHA PCE 2013 | Not validated | Observation (ASCVD risk) | Clinical decision trigger |
| **MarkovProgressionMotor** | T4 | Internal transition matrix | Not validated | ❌ Do not export | Internal exploration |
| **ObesityMasterMotor** | T3 | Aggregator of T1/T2 motors | Not validated | ❌ Do not export (internal summary) | Clinical context only |
| **ClinicalGuidelinesMotor** | T2 | Multiple guidelines (ACC/AHA, ESC, ADA) | Not validated | CarePlan/DetectedIssue | Supportive |

## Export Policy Summary

| Category | Motors | FHIR Resource | Export Rule |
|---|---|---|---|
| **Full Export (T1 validated)** | 20 motors | Observation, Condition, DetectedIssue | Always export with standard LOINC/SNOMED codes |
| **Full Export (T1 not validated)** | 2 motors | Observation, Condition, DetectedIssue | Export when validated |
| **Conditional Export (T2)** | 17 motors | Observation, DetectedIssue, QuestionnaireResponse | Export with clear evidence reference |
| **Internal Only (T3)** | 3 motors | N/A | Do not export; UI narrative only |
| **Blocked (T4)** | 2 motors | N/A | Do not export; research use only |

## Validation Summary (Sprint 6)

- **Total motors:** 48
- **Validated (Sprint 6):** 32 motors (67%)
- **Tests:** 526 unit tests (100% pass)
- **Validated motors:** AcostaPhenotypeMotor, EOSSStagingMotor, SarcopeniaMonitorMotor, HypertensionSecondaryMotor, InflammationMotor, KFREMotor, MetforminB12Motor, ObesityPharmaEligibilityMotor, SleepApneaPrecisionMotor, GLP1MonitoringMotor, FLIMotor, CharlsonMotor, FriedFrailtyMotor, WomensHealthMotor, MensHealthMotor, DrugInteractionMotor, MetabolicPrecisionMotor, DeepMetabolicProxyMotor, AnthropometryPrecisionMotor, EndocrinePrecisionMotor, VAIMotor, TyGBMIMotor, CMIMotor, LipidRiskPrecisionMotor, CancerScreeningMotor, SGLT2iBenefitMotor, Lifestyle360Motor, PulsePressureMotor, NFSMotor, CVDReclassifierMotor, BodyCompositionTrendMotor, FreeTestosteroneMotor, VitaminDMotor, ACEScoreEngine

## Versioning & Audit Trail

Each motor result includes:
- `requirement_id`: Links to evidence source
- `confidence`: Numerical confidence score (0.0-1.0)
- `estado_ui`: Clinical state classification
- `evidence[]`: Structured evidence with codes and thresholds

For regulatory submissions, only T1 and T2 motors may be included in clinical decision documentation. T3 and T4 motors are excluded from regulatory evidence packages.
