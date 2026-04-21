#!/usr/usr/bin/env python3
"""
Stress Test Script - Integrum V2
Extreme Case: Severe Heart Failure + Sarcopenia + Advanced CKD

This script creates an extreme clinical scenario to validate that the CDSS accurately
prioritizes patient safety (hard stops, organ protection, and functional preservation)
over standard weight loss protocols.
"""

import sys
import os
from datetime import datetime

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


def build_extreme_patient():
    return Encounter(
        id="STRESS-001",
        demographics=DemographicsSchema(
            age_years=72,
            gender="male",
            weight_kg=115.0,
            height_cm=165.0,
        ),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=165.0,
            creatinine_mg_dl=2.8,  # Advanced CKD (approx Stage 4)
            hba1c_percent=8.2,
            fasting_insulin_uIU_ml=22.0,
            bun_mg_dl=40.0,
            albumin_g_dl=3.0,
            sodium_meq_l=135.0,
            potassium_meq_l=5.1,
            chlorine_meq_l=101.0,
            calcium_mg_dl=8.8,
            phosphorus_mg_dl=4.5,
            mcv_fl=90.0,
            rdw_percent=15.0,
            wbc_k_ul=6.5,
            lymphocyte_percent=20.0,
            neutrophil_percent=70.0,
            ferritin_ng_ml=300.0,
            hs_crp_mg_l=12.5,  # High inflammation
            tsh_uIU_ml=4.2,
            uric_acid_mg_dl=8.5,
            ast_u_l=40.0,
            alt_u_l=45.0,
            ggt_u_l=60.0,
            vitamin_d_ng_ml=12.0,  # Deficiency
        ),
        cardio_panel=CardioPanelSchema(
            total_cholesterol_mg_dl=180.0,
            ldl_mg_dl=110.0,
            hdl_mg_dl=30.0,
            triglycerides_mg_dl=200.0,
        ),
        conditions=[
            Condition(code="I50.9", title="Insuficiencia cardíaca severa", system="CIE-10"),
            Condition(code="N18.4", title="Enfermedad renal crónica estadio 4", system="CIE-10"),
            Condition(code="E66.01", title="Obesidad mórbida", system="CIE-10"),
            Condition(code="E11.9", title="Diabetes mellitus tipo 2", system="CIE-10"),
            Condition(code="I10", title="Hipertensión resistente", system="CIE-10"),
            Condition(code="M62.84", title="Sarcopenia", system="CIE-10"),
        ],
        observations=[
            Observation(code="29463-7", value=115.0, unit="kg"),
            Observation(code="8302-2", value=165.0, unit="cm"),
            Observation(code="8480-6", value=160.0, unit="mmHg"),
            Observation(code="8462-4", value=95.0, unit="mmHg"),
            Observation(code="WAIST-001", value=125.0, unit="cm"),
            Observation(code="BIA-MUSCLE-KG", value=35.0, unit="kg"), # Severe muscle loss
            Observation(code="BIA-FAT-PCT", value=45.0, unit="%"),
            Observation(code="GRIP-STR-R", value=18.0, unit="kg"),    # Severe frailty
            Observation(code="GAIT-SPEED", value=0.6, unit="m/s"),     # Very slow gait
            Observation(code="SARCF-SCORE", value=8),                  # High risk
            Observation(code="UACR-001", value=450.0, unit="mg/g"),    # Macroalbuminuria
        ],
        medications=[
            MedicationStatement(code="METFORMIN", name="Metformina 1000mg", is_active=True),
            MedicationStatement(code="FUROSEMIDE", name="Furosemida 40mg", is_active=True),
            MedicationStatement(code="LISINOPRIL", name="Lisinopril 20mg", is_active=True),
        ],
        history=ClinicalHistory(
            onset_trigger="unknown",
            has_type2_diabetes=True,
            has_hypertension=True,
            has_dyslipidemia=True,
            has_ckd=True,
            has_heart_failure=True,
            has_coronary_disease=True,
            smoking_status="former",
            pregnancy_status="not_applicable",
            menopausal_status="not_applicable",
        ),
        metadata={
            "sex": "male",
        },
        reason_for_visit="Evaluación de riesgo cardiovascular y ajuste de medicación por insuficiencia cardíaca."
    )


def print_separator(char="=", width=80):
    print(char * width)


def main():
    print_separator("=")
    print("  STRESS TEST: EXTREME CLINICAL SCENARIO")
    print("  Heart Failure + Sarcopenia + Chronic Kidney Disease Stage 4")
    print_separator("=")

    enc = build_extreme_patient()
    runner = SpecialtyRunner()
    results = runner.run_all(enc)

    critical_motors = ["PharmaPrecisionMotor", "PrecisionNutritionMotor", "ObesityMasterMotor", "ClinicalGuidelinesMotor", "DrugInteractionMotor"]

    for name in critical_motors:
        result = results.get(name)
        if result:
            print(f"\n  MOTOR: {name}")
            print(f"  VEREDICTO: {result.calculated_value}")
            if result.explanation:
                print(f"  ANALISIS: {result.explanation}")
            if result.critical_omissions:
                print("  OMISIONES CRÍTICAS:")
                for o in result.critical_omissions:
                    print(f"    - [{o.severity}] {o.drug_class}: {o.clinical_rationale}")
            if result.action_checklist:
                print("  PLAN DE ACCIÓN:")
                for a in result.action_checklist:
                    print(f"    - [{a.priority}] {a.task} ({a.rationale})")

    print_separator("=")
    print("  STRESS TEST COMPLETE")
    print_separator("=")


if __name__ == "__main__":
    main()
