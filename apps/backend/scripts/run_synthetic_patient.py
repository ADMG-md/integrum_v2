#!/usr/bin/env python3
"""
Synthetic Patient Validation Script — Integrum V2

Creates a realistic obese patient case with complete labs and runs ALL 38 motors.
Prints raw results to stdout for external review.

Usage:
    cd apps/backend && python3 scripts/run_synthetic_patient.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engines.domain import (
    Encounter,
    Observation,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
    Condition,
    MedicationStatement,
)
from src.domain.models import ClinicalHistory, TraumaHistory
from src.engines.specialty_runner import SpecialtyRunner
from src.engines.obesity_master import ObesityMasterMotor, ObesityClinicalStoryInput
from datetime import datetime


def build_synthetic_patient():
    """
    Caso clínico sintético: Mujer de 48 años, Barranquilla.
    Obesidad clase II, síndrome metabólico, HTN, DM2, dislipidemia.
    En tratamiento con metformina, enalapril, atorvastatina.
    Perfil realista para validación clínica.
    """
    return Encounter(
        id="SYNTH-001",
        demographics=DemographicsSchema(age_years=48.0, gender="female"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=145.0,
            creatinine_mg_dl=0.85,
            hba1c_percent=7.8,
            insulin_mu_u_ml=22.0,
            albumin_g_dl=4.1,
            alkaline_phosphatase_u_l=78.0,
            mcv_fl=89.0,
            rdw_percent=13.8,
            wbc_k_ul=7.2,
            lymphocyte_percent=26.0,
            neutrophil_percent=64.0,
            ferritin_ng_ml=185.0,
            hs_crp_mg_l=5.8,
            tsh_uIU_ml=3.8,
            ft4_ng_dl=1.1,
            ft3_pg_ml=3.1,
            uric_acid_mg_dl=6.8,
            platelets_k_u_l=245.0,
            ast_u_l=32.0,
            alt_u_l=48.0,
            ggt_u_l=55.0,
            vitamin_d_ng_ml=18.0,
            vitamin_b12_pg_ml=280.0,
            testosterone_total_ng_dl=25.0,
            psa_ng_ml=None,
        ),
        cardio_panel=CardioPanelSchema(
            total_cholesterol_mg_dl=258.0,
            ldl_mg_dl=168.0,
            hdl_mg_dl=34.0,
            triglycerides_mg_dl=285.0,
            apob_mg_dl=135.0,
            lpa_mg_dl=45.0,
            apoa1_mg_dl=105.0,
        ),
        conditions=[
            Condition(code="E66.01", title="Obesidad clase II", system="CIE-10"),
            Condition(code="E11.9", title="Diabetes mellitus tipo 2", system="CIE-10"),
            Condition(code="I10", title="Hipertension esencial", system="CIE-10"),
            Condition(code="E78.5", title="Dislipidemia mixta", system="CIE-10"),
            Condition(
                code="K76.0", title="Higado graso no alcoholico", system="CIE-10"
            ),
            Condition(
                code="G47.33", title="Apnea obstructiva del sueno", system="CIE-10"
            ),
        ],
        observations=[
            Observation(code="29463-7", value=98.0, unit="kg"),
            Observation(code="8302-2", value=160.0, unit="cm"),
            Observation(code="8480-6", value=148.0, unit="mmHg"),
            Observation(code="8462-4", value=94.0, unit="mmHg"),
            Observation(code="WAIST-001", value=112.0, unit="cm"),
            Observation(code="HIP-001", value=118.0, unit="cm"),
            Observation(code="AGE-001", value=48.0),
            Observation(code="NECK-001", value=42.0, unit="cm"),
            Observation(code="BIA-MUSCLE-KG", value=48.0, unit="kg"),
            Observation(code="BIA-FAT-PCT", value=42.0, unit="%"),
            Observation(code="GRIP-STR-R", value=22.0, unit="kg"),
            Observation(code="GRIP-STR-L", value=20.0, unit="kg"),
            Observation(code="GAIT-SPEED", value=0.95, unit="m/s"),
            Observation(code="5XSTS-SEC", value=17.5, unit="s"),
            Observation(code="SARCF-SCORE", value=5),
            Observation(code="GGT-001", value=55.0, unit="U/L"),
            Observation(code="FER-001", value=185.0, unit="ng/mL"),
            Observation(code="UA-001", value=6.8, unit="mg/dL"),
            Observation(code="LIFE-SNORING", value=1),
            Observation(code="LIFE-TIRED", value=1),
            Observation(code="LIFE-APNEA", value=1),
            Observation(code="LIFE-SLEEP", value=5.5),
            Observation(code="LIFE-STRESS", value=7),
            Observation(code="LIFE-EXERCISE", value=60),
            Observation(code="AIS-001", value=8),
            Observation(code="TFEQ-EMOTIONAL", value=3.2),
            Observation(code="TFEQ-UNCONTROLLED", value=2.8),
            Observation(code="UACR-001", value=85.0, unit="mg/g"),
            Observation(code="VITB12-001", value=280.0, unit="pg/mL"),
            Observation(code="LIFE-QUALITY-VAS", value=5),
            Observation(code="PHQ9-SCORE", value=12),
            Observation(code="GAD7-SCORE", value=9),
        ],
        medications=[
            MedicationStatement(
                code="METFORMIN", name="Metformina 1000mg", is_active=True
            ),
            MedicationStatement(
                code="ENALAPRIL", name="Enalapril 10mg", is_active=True
            ),
            MedicationStatement(
                code="ATORVASTATIN", name="Atorvastatina 40mg", is_active=True
            ),
        ],
        history=ClinicalHistory(
            onset_trigger="pregnancy",
            age_of_onset=32,
            max_weight_ever_kg=105.0,
            has_type2_diabetes=True,
            has_hypertension=True,
            has_dyslipidemia=True,
            has_nafld=True,
            has_osa=True,
            has_ckd=False,
            pregnancy_status="unknown",
            menopausal_status="perimenopausal",
            has_history_medullary_thyroid_carcinoma=False,
            has_history_men2=False,
            has_history_pancreatitis=False,
            has_gastroparesis=False,
            has_seizures_history=False,
            has_eating_disorder_history=False,
            phq9_item_9_score=0,
            trauma=TraumaHistory(ace_score=4),
            current_medications=[],
        ),
        metadata={
            "sex": "female",
            "ethnicity": "mestiza",
            "city": "Barranquilla",
            "prev_weight_kg": 102.0,
            "prev_muscle_mass_kg": 52.0,
            "glp1_weeks": 0,
        },
        reason_for_visit="Control de obesidad y diabetes. Dificultad para bajar de peso.",
    )


def print_separator(char="=", width=80):
    print(char * width)


def print_header(text):
    print()
    print_separator("=")
    print(f"  {text}")
    print_separator("=")


def print_motor(name, result):
    print()
    print_separator("-", 60)
    print(f"  MOTOR: {name}")
    print_separator("-", 60)
    print(f"  calculated_value : {result.calculated_value}")
    print(f"  estado_ui        : {result.estado_ui}")
    print(f"  confidence       : {result.confidence}")
    if result.requirement_id:
        print(f"  requirement_id   : {result.requirement_id}")
    if result.explanation:
        print(f"  explanation      : {result.explanation}")
    if result.evidence:
        print(f"  evidence ({len(result.evidence)}):")
        for ev in result.evidence:
            print(
                f"    - [{ev.type}] {ev.code}: {ev.value} (threshold: {ev.threshold})"
            )
    if result.action_checklist:
        print(f"  action_checklist ({len(result.action_checklist)}):")
        for a in result.action_checklist:
            print(f"    - [{a.priority}] {a.task}")
            print(f"      rationale: {a.rationale}")
    if result.critical_omissions:
        print(f"  critical_omissions ({len(result.critical_omissions)}):")
        for o in result.critical_omissions:
            print(f"    - [{o.severity}] {o.gap_type}: {o.drug_class}")
            print(f"      rationale: {o.clinical_rationale}")
    if result.metadata:
        print(f"  metadata:")
        for k, v in result.metadata.items():
            print(f"    {k}: {v}")


def print_calculated_values(enc):
    print()
    print_separator("-", 60)
    print("  CALCULATED VALUES (Encounter properties)")
    print_separator("-", 60)
    calcs = {
        "BMI": enc.bmi,
        "eGFR (CKD-EPI)": enc.egfr_ckd_epi,
        "HOMA-IR": enc.homa_ir,
        "HOMA-B": enc.homa_b,
        "TyG Index": enc.tyg_index,
        "METS-IR": enc.mets_ir,
        "TyG-BMI": enc.tyg_bmi,
        "Waist/Height": enc.waist_to_height,
        "Waist/Hip": enc.waist_to_hip,
        "BRI": enc.body_roundness_index,
        "Pulse Pressure": enc.pulse_pressure,
        "MAP": enc.mean_arterial_pressure,
        "Fat Free Mass": enc.fat_free_mass,
        "Ideal Body Weight": enc.ideal_body_weight,
        "Remnant Cholesterol": enc.remnant_cholesterol,
        "AIP": enc.aip,
        "Castelli I": enc.castelli_index_i,
        "Castelli II": enc.castelli_index_ii,
        "ApoB/ApoA1": enc.apob_apoa1_ratio,
        "Non-HDL": enc.non_hdl_cholesterol,
        "UACR": enc.uacr,
        "ACE Score": enc.ace_score,
        "Glucose": enc.glucose_mg_dl,
        "Creatinine": enc.creatinine_mg_dl,
        "HbA1c": enc.hba1c,
        "Uric Acid": enc.uric_acid,
    }
    for name, val in calcs.items():
        print(f"  {name:25s}: {val}")


def main():
    print_header("INTEGRUM V2 — SYNTHETIC PATIENT VALIDATION")
    print()
    print("  Patient ID : SYNTH-001")
    print("  Demographics: 48yo female, Barranquilla, mestiza")
    print("  Conditions  : E66.01 (Obesity II), E11.9 (DM2), I10 (HTN),")
    print("                E78.5 (Dyslipidemia), K76.0 (NAFLD), G47.33 (OSA)")
    print("  Medications : Metformina 1000mg, Enalapril 10mg, Atorvastatina 40mg")
    print("  Visit reason: Control de obesidad y diabetes")
    print()

    enc = build_synthetic_patient()

    print_calculated_values(enc)

    print_header("SPECIALTY RUNNER — ALL 38 MOTORS")

    runner = SpecialtyRunner()
    results = runner.run_all(enc)

    activated = 0
    skipped = 0

    for name, result in results.items():
        if result is None:
            skipped += 1
            print()
            print(f"  [SKIPPED] {name} — returned None")
            continue
        if hasattr(result, "calculated_value"):
            activated += 1
            print_motor(name, result)
        else:
            print()
            print(f"  [UNKNOWN] {name} — unexpected result type: {type(result)}")

    print()
    print_header("SUMMARY")
    print(f"  Total motors executed : {len(results)}")
    print(f"  Activated (produced result): {activated}")
    print(f"  Skipped (returned None)    : {skipped}")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print()
    print_separator("=")
    print("  END OF REPORT")
    print_separator("=")


if __name__ == "__main__":
    main()
