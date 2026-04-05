# Cortex Remediation Audit Trail (V2.5 → V2.6)
# IEC 62304 / ISO 14971 Compliance
# Date: 2026-03-30

## Summary
6 critical/high findings from the Deep SaMD Audit were remediated with code changes, 
new tests, and RMF/traceability updates. **41/41 tests pass with zero regressions.**

---

## Remediation Actions

### R-01: Acosta CODES Overwrite Fix (CRITICAL)
- **Files**: `src/engines/acosta.py`
- **Changes**: Merged two conflicting `CODES` dictionaries into one unified catalog. Updated `REQUIREMENT_ID` from `ACOSTA-2015` to `ACOSTA-2021`.
- **Tests**: `test_acosta_codes_contains_all_required_keys`, `test_acosta_requirement_id_is_2021`
- **RMF**: H-001 mitigation confirmed active.
- **Status**: ✅ Implemented

### R-02: Sarcopenia ASMI Proxy Fix (CRITICAL, H-014)
- **Files**: `src/engines/sarcopenia.py`
- **Changes**: Added `APPENDICULAR_PROXY_COEFF = 0.75` and applied it to the ASMI calculation. Previously used total muscle mass, causing systematic false negatives.
- **Tests**: `test_asmi_uses_appendicular_proxy_not_total_mm`, `test_sarcopenia_risk_in_obese_patient_not_underestimated`
- **RMF**: New hazard H-014 added.
- **Status**: ✅ Implemented

### R-03: VaultService Fail-Fast Security Gate (HIGH, H-015)
- **Files**: `src/services/vault_service.py`
- **Changes**: `VaultService.__init__()` now raises `RuntimeError` if `VAULT_MASTER_KEY` is missing. Dev-mode escape hatch via `ALLOW_DEV_VAULT_KEY=true`.
- **Tests**: `test_vault_raises_if_key_missing`, `test_vault_allows_dev_mode_with_explicit_flag`
- **RMF**: New hazard H-015 added.
- **Status**: ✅ Implemented

### R-04: EOSS Biometric Trigger (HIGH)
- **Files**: `src/engines/eoss.py`
- **Changes**: `validate()` now accepts `BMI >= 30` as a clinical trigger in addition to the administrative `E66` ICD-10 code.
- **Tests**: `test_eoss_triggers_with_bmi_without_e66`, `test_eoss_does_not_trigger_when_no_obesity`
- **RMF**: H-002 mitigation updated.
- **Status**: ✅ Implemented

### R-05: BioAge Silent Fallback Removal (HIGH, H-007)
- **Files**: `src/engines/specialty/bio_age.py`, `AdjudicationViewer.tsx`
- **Changes**: `PhenoAgeLevineOutput` now has `status: Literal["ok", "error"]`. Silent fallback to chronological age removed. Frontend shows "Indeterminate" warning on error. Engine version bumped to `0.2.0`.
- **Tests**: `test_bioage_error_does_not_fall_back_to_chrono`, `test_bioage_error_sets_status_error_for_invalid_crp`, `test_bioage_normal_input_returns_ok`
- **RMF**: H-007 marked as mitigated.
- **Status**: ✅ Implemented

### R-06: SpecialtyRunner CVD Gateway (MODERATE)
- **Files**: `src/engines/specialty_runner.py`
- **Changes**: Fixed missing `Dict`/`Any` imports. Added CVD gated motor attempt (catches `NotImplementedError`). Passes `cvd_risk_category` to `ObesityMasterMotor`. Fixed EOSS stage extraction from string. Fixed Sarcopenia risk level mapping.
- **Tests**: `test_mho_with_high_cvd_triggers_discordance`, `test_no_discordance_without_cvd`
- **RMF**: Discordance logic (H-001) now fully active.
- **Status**: ✅ Implemented

---

## Test Results
```
41 passed in 0.24s
```

## Additional Fixes (Bonus)
- Modernized all legacy test fixtures (`test_acosta.py`, `test_eoss.py`, `test_longevity_precision.py`) to use proper `Encounter` constructors with required schema fields.
- Fixed `SpecialtyRunner.__new__()` variable shadowing bug (`cls` was being reused for both the class and dict iteration variable).
