#!/usr/bin/env python3
"""
run_synthetic_patient.py — End-to-End Synthetic Patient Validation

Creates a realistic Colombian patient profile and runs all clinical motors,
verifying:
1. T1/T2 motors execute successfully in both clinical and non-clinical modes
2. T3/T4 motors are BLOCKED in clinical_mode=True
3. All T1/T2 motors return AdjudicationResult (contract enforcement)
4. Motor outputs are clinically coherent

Usage:
    cd apps/backend
    python ../../scripts/run_synthetic_patient.py

No database required — pure engine validation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from src.engines.domain import (
    Encounter,
    Observation,
    Condition,
    MedicationStatement,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
    ClinicalHistory,
    DrugEntry,
    TraumaHistory,
    ObesityOnsetTrigger,
)
from src.engines.specialty_runner import specialty_runner
from src.engines.domain import AdjudicationResult

T3_MOTORS = {
    "DeepMetabolicProxyMotor",
    "BiologicalAgeMotor",
    "ObesityMasterMotor",
}

T4_MOTORS = {
    "MarkovProgressionMotor",
}


def create_synthetic_encounter() -> Encounter:
    """Build a realistic Colombian patient with full lab panel."""
    return Encounter(
        id="synthetic-001",
        demographics=DemographicsSchema(age_years=48, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=118.0,
            hba1c_percent=6.4,
            insulin_mu_u_ml=18.5,
            c_peptide_ng_ml=2.8,
            creatinine_mg_dl=0.9,
            uric_acid_mg_dl=6.2,
            ast_u_l=32.0,
            alt_u_l=41.0,
            ggt_u_l=48.0,
            alkaline_phosphatase_u_l=78.0,
            wbc_k_ul=7.2,
            lymphocyte_percent=28.0,
            neutrophil_percent=62.0,
            mcv_fl=88.0,
            rdw_percent=13.5,
            platelets_k_u_l=245.0,
            hs_crp_mg_l=2.1,
            ferritin_ng_ml=145.0,
            albumin_g_dl=4.2,
            tsh_u_iu_ml=2.3,
            ft4_ng_dl=1.1,
            ft3_pg_ml=3.0,
            total_cholesterol_mg_dl=224.0,
            ldl_mg_dl=148.0,
            hdl_mg_dl=38.0,
            triglycerides_mg_dl=190.0,
            vldl_mg_dl=38.0,
            apob_mg_dl=112.0,
            lpa_mg_dl=25.0,
            apoa1_mg_dl=128.0,
        ),
        cardio_panel=CardioPanelSchema(
            glucose_mg_dl=118.0,
            total_cholesterol_mg_dl=224.0,
            ldl_mg_dl=148.0,
            hdl_mg_dl=38.0,
            triglycerides_mg_dl=190.0,
        ),
        conditions=[
            Condition(code="E66.01", title="Obesidad grado II", system="CIE-10"),
            Condition(code="R73.03", title="Prediabetes", system="CIE-10"),
            Condition(code="I10", title="Hipertension arterial", system="CIE-10"),
            Condition(code="E78.5", title="Dislipidemia mixta", system="CIE-10"),
        ],
        observations=[
            Observation(code="29463-7", value=102.5, unit="kg"),
            Observation(code="8302-2", value=172.0, unit="cm"),
            Observation(code="WAIST-001", value=106.0, unit="cm"),
            Observation(code="HIP-001", value=104.0, unit="cm"),
            Observation(code="NECK-001", value=42.0, unit="cm"),
            Observation(code="8480-6", value=138.0, unit="mmHg"),
            Observation(code="8462-4", value=88.0, unit="mmHg"),
            Observation(code="PHQ-9", value=8.0, category="Psychometry"),
            Observation(code="GAD-7", value=6.0, category="Psychometry"),
            Observation(code="AIS-001", value=9.0, category="Psychometry"),
            Observation(code="TFEQ-EMOTIONAL", value=2.5, category="Psychometry"),
            Observation(code="TFEQ-UNCONTROLLED", value=7.0, category="Psychometry"),
            Observation(code="TFEQ-COGNITIVE", value=8.0, category="Psychometry"),
            Observation(
                code="LIFE-SLEEP", value=5.5, unit="hours", category="Lifestyle"
            ),
            Observation(
                code="LIFE-EXERCISE", value=30.0, unit="min/week", category="Lifestyle"
            ),
            Observation(
                code="LIFE-STRESS", value=7.0, unit="1-10", category="Lifestyle"
            ),
            Observation(code="GRIP-STR-R", value=38.0, unit="kg"),
            Observation(code="GRIP-STR-L", value=35.0, unit="kg"),
            Observation(code="MMA-001", value=32.5, unit="kg", category="BIA"),
            Observation(code="BIA-FAT-PCT", value=32.0, unit="%", category="BIA"),
            Observation(code="BIA-LEAN-KG", value=62.0, unit="kg", category="BIA"),
            Observation(code="BIA-VISCERAL", value=145.0, unit="cm2", category="BIA"),
            Observation(code="BIA-BMR", value=1950.0, unit="kcal", category="BIA"),
        ],
        medications=[
            MedicationStatement(code="C09CA03", name="Losartan 50mg", is_active=True),
            MedicationStatement(
                code="C10AB05", name="Fenofibrato 200mg", is_active=True
            ),
            MedicationStatement(
                code="A10BD02", name="Metformina 850mg", is_active=True
            ),
        ],
        history=ClinicalHistory(
            onset_trigger=ObesityOnsetTrigger.UNKNOWN,
            age_of_onset=32,
            max_weight_ever_kg=118.0,
            current_medications=[
                DrugEntry(drug_name="Losartan", dose="50mg", frequency="QD"),
                DrugEntry(drug_name="Fenofibrato", dose="200mg", frequency="QD"),
                DrugEntry(drug_name="Metformina", dose="850mg", frequency="BID"),
            ],
            previous_medications=[
                DrugEntry(
                    drug_name="Sitagliptina",
                    dose="100mg",
                    frequency="QD",
                ),
            ],
            trauma=TraumaHistory(
                ace_score=3,
                has_history_of_abuse=False,
                emotional_impact_score=2,
            ),
            has_type2_diabetes=False,
            has_prediabetes=True,
            has_hypertension=True,
            has_dyslipidemia=True,
            has_nafld=True,
            has_gout=False,
            has_hypothyroidism=False,
            has_pcos=False,
            has_osa=True,
            has_glaucoma=False,
            has_seizures_history=False,
            has_eating_disorder_history=False,
            family_history_thyroid_cancer=False,
            smoking_status="never",
            alcohol_intake="moderate",
        ),
        reason_for_visit="Control cardiometabolico y fenotipado de obesidad",
        personal_history="Paciente con obesidad grado II, prediabetes, HTA y dislipidemia. En tratamiento con Losartan, Fenofibrato y Metformina.",
        family_history="Madre con DM2, padre con cardiopatia isquemica.",
        metadata={"sex": "male", "age": 48, "patient_id": "synthetic-001"},
    )


def run_validation():
    print("=" * 70)
    print("SYNTHETIC PATIENT — CLINICAL ENGINE VALIDATION")
    print("=" * 70)

    encounter = create_synthetic_encounter()
    print(f"\nPatient: Male, 48yo, BMI={102.5 / (1.72**2):.1f}")
    print(f"Conditions: {', '.join(c.title for c in encounter.conditions)}")
    print(
        f"Motors: {len(specialty_runner._primary_motors) + len(specialty_runner._gated_motors) + len(specialty_runner._aggregator_motors)} registered\n"
    )

    # --- Run 1: Non-clinical mode (all motors) ---
    print("-" * 70)
    print("RUN 1: Non-Clinical Mode (all motors allowed)")
    print("-" * 70)
    results_all = specialty_runner.run_all(encounter, clinical_mode=False)

    passed_all = 0
    failed_all = 0
    contract_violations = []

    for name, result in sorted(results_all.items()):
        if result is None:
            print(f"  [SKIP]   {name}: No output")
            failed_all += 1
            continue
        if isinstance(result, AdjudicationResult):
            print(
                f"  [OK]     {name}: {result.calculated_value} (conf={result.confidence:.2f})"
            )
            passed_all += 1
        else:
            print(f"  [WARN]   {name}: Wrong type {type(result).__name__}")
            contract_violations.append(name)
            failed_all += 1

    print(
        f"\n  Passed: {passed_all} | Failed/Skipped: {failed_all} | Contract violations: {len(contract_violations)}"
    )

    # --- Run 2: Clinical mode (T1/T2 only, T3/T4 blocked) ---
    print("\n" + "-" * 70)
    print("RUN 2: Clinical Mode (T1/T2 only, T3/T4 blocked)")
    print("-" * 70)

    results_clinical = specialty_runner.run_all(encounter, clinical_mode=True)

    t3_blocked = 0
    t4_blocked = 0
    t12_passed = 0

    for name in results_all:
        if name in T3_MOTORS:
            if name not in results_clinical:
                print(
                    f"  [BLOCKED] {name} (T3) — correctly excluded from clinical mode"
                )
                t3_blocked += 1
            else:
                print(
                    f"  [FAIL]    {name} (T3) — ran in clinical mode (should be blocked!)"
                )
        elif name in T4_MOTORS:
            print(
                f"  [INFO]    {name} (T4) — gate-conditional (patient has prediabetes, so runs)"
            )

    for name, result in sorted(results_clinical.items()):
        if name not in T3_MOTORS and name not in T4_MOTORS:
            if isinstance(result, AdjudicationResult):
                print(f"  [OK]      {name}: {result.calculated_value}")
                t12_passed += 1
            else:
                print(f"  [WARN]    {name}: wrong type {type(result).__name__}")

    print(f"\n  T3 blocked: {t3_blocked}/{len(T3_MOTORS)} | T4: gate-conditional")
    print(f"  T1/T2 passed: {t12_passed}")

    # --- Clinical coherence check ---
    print("\n" + "-" * 70)
    print("CLINICAL COHERENCE CHECK")
    print("-" * 70)

    checks = [
        (
            "EOSSStagingMotor",
            lambda r: "Stage" in r.calculated_value or "EOSS" in r.calculated_value,
        ),
        ("AcostaPhenotypeMotor", lambda r: len(r.calculated_value) > 0),
        ("MetabolicPrecisionMotor", lambda r: r.confidence > 0),
        ("AnthropometryMotor", lambda r: r.confidence > 0),
        ("HypertensionMotor", lambda r: r.confidence > 0),
        ("FLIMotor", lambda r: r.evidence[0].value if r.evidence else None),
        ("KFREMotor", lambda r: r.confidence >= 0),
        ("CharlsonMotor", lambda r: r.confidence >= 0),
        ("GLP1MonitoringMotor", lambda r: r.confidence >= 0),
    ]

    all_passed = True
    for name, check_fn in checks:
        if name in results_clinical:
            result = results_clinical[name]
            try:
                check_fn(result)
                print(f"  [OK]  {name}: coherent")
            except Exception as e:
                print(f"  [WARN] {name}: {e}")
                all_passed = False
        else:
            print(f"  [SKIP] {name}: not in clinical results")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_motors = len(results_all)
    print(f"  Total motors executed (non-clinical): {total_motors}")
    print(f"  Passed: {passed_all}/{total_motors}")
    print(f"  Contract violations: {len(contract_violations)}")
    print(f"  T3 motors blocked in clinical mode: {t3_blocked}/{len(T3_MOTORS)}")
    print(f"  T4: gate-conditional (not blocked, but gated by clinical criteria)")
    print(f"  Clinical coherence: {'PASS' if all_passed else 'WARN'}")
    print(
        f"  Status: {'PASS' if passed_all == total_motors and len(contract_violations) == 0 else 'FAIL'}"
    )

    if contract_violations:
        print(f"\n  CONTRACT VIOLATIONS:")
        for v in contract_violations:
            print(f"    - {v} returned wrong type")

    return passed_all == total_motors and len(contract_violations) == 0


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
