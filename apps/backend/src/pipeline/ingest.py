"""
Data Ingestion — CSV → PostgreSQL

Reads clinical data from CSV files and inserts into the Integrum database.
Bypasses the API layer for bulk ingestion. Uses the quality layer to validate.

Usage:
    python -m src.pipeline.ingest --csv data/patients.csv --env .env
"""

import csv
import json
import uuid
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.quality import validate_record, QualityReport


# Column mapping: CSV header → observation code
COLUMN_MAP = {
    "weight_kg": "29463-7",
    "height_cm": "8302-2",
    "waist_cm": "WAIST-001",
    "hip_cm": "HIP-001",
    "neck_cm": "NECK-001",
    "systolic_bp": "8480-6",
    "diastolic_bp": "8462-4",
    "glucose_mg_dl": "2339-0",
    "hba1c_percent": "4548-4",
    "insulin_mu_u_ml": "20448-7",
    "creatinine_mg_dl": "2160-0",
    "uric_acid_mg_dl": "UA-001",
    "ast_u_l": "29230-0",
    "alt_u_l": "22538-3",
    "ggt_u_l": "GGT-001",
    "wbc_k_ul": "WBC-001",
    "lymphocyte_pct": "26474-7",
    "neutrophil_pct": "26499-4",
    "mcv_fl": "MCV-001",
    "rdw_pct": "RDW-001",
    "platelets_k_ul": "PLT-001",
    "hs_crp_mg_l": "30522-7",
    "ferritin_ng_ml": "FER-001",
    "albumin_g_dl": "ALB-001",
    "tsh_uiu_ml": "11579-0",
    "ft4_ng_dl": "FT4-001",
    "ft3_pg_ml": "FT3-001",
    "total_chol_mg_dl": "2093-3",
    "ldl_mg_dl": "13457-7",
    "hdl_mg_dl": "2085-9",
    "triglycerides_mg_dl": "2571-8",
    "apob_mg_dl": "APOB-001",
    "lpa_mg_dl": "LPA-001",
    "apoa1_mg_dl": "APOA1-001",
    "phq9_score": "PHQ-9",
    "gad7_score": "GAD-7",
    "ais_score": "AIS-001",
    "tfeq_emotional": "TFEQ-EMOTIONAL",
    "tfeq_uncontrolled": "TFEQ-UNCONTROLLED",
    "sleep_hours": "LIFE-SLEEP",
    "exercise_min_week": "LIFE-EXERCISE",
    "stress_vas": "LIFE-STRESS",
    "grip_right_kg": "GRIP-STR-R",
    "grip_left_kg": "GRIP-STR-L",
    "gait_speed_ms": "GAIT-SPEED",
    "five_x_sts_sec": "5XSTS-SEC",
    "sarcf_score": "SARCF-SCORE",
    "muscle_mass_kg": "MMA-001",
    "body_fat_pct": "BIA-FAT-PCT",
    "uacr_mg_g": "UACR-001",
    "vitb12_pg_ml": "VITB12-001",
    "vitd_ng_ml": "VITD-001",
    "age_years": "AGE-001",
    "aldosterone_ng_dl": "ALDO-001",
    "renin_ng_ml_h": "RENIN-001",
    "cortisol_am_mcg_dl": "CORT-AM",
    "shbg_nmol_l": "SHBG-001",
    "rt3_ng_dl": "RT3-001",
    "c_peptide_ng_ml": "C-PEP-001",
    "alk_phos_u_l": "ALKPHOS-001",
    "vldl_mg_dl": "VLDL-001",
}

# Column mapping: CSV header → clinical history field
HISTORY_MAP = {
    "has_t2dm": "has_type2_diabetes",
    "has_htn": "has_hypertension",
    "has_dyslipidemia": "has_dyslipidemia",
    "has_nafld": "has_nafld",
    "has_osa": "has_osa",
    "has_ckd": "has_ckd",
    "pregnancy_status": "pregnancy_status",
    "smoking_status": "smoking_status",
    "gender": "gender",
}

# Condition codes
CONDITION_MAP = {
    "icd_e66": ("E66.01", "Obesidad", "CIE-10"),
    "icd_e11": ("E11.9", "Diabetes tipo 2", "CIE-10"),
    "icd_i10": ("I10", "Hipertension", "CIE-10"),
    "icd_e78": ("E78.5", "Dislipidemia", "CIE-10"),
    "icd_k76": ("K76.0", "Higado graso", "CIE-10"),
    "icd_g47": ("G47.33", "Apnea del sueno", "CIE-10"),
}


def parse_csv_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Parse a single CSV row into patient data structure."""
    observations = []
    history = {}
    conditions = []
    medications = []

    # Parse observations
    for csv_col, obs_code in COLUMN_MAP.items():
        if csv_col in row and row[csv_col].strip():
            try:
                value = float(row[csv_col].strip())
                observations.append({"code": obs_code, "value": value})
            except ValueError:
                pass  # Skip non-numeric values

    # Parse history
    for csv_col, hist_key in HISTORY_MAP.items():
        if csv_col in row and row[csv_col].strip():
            val = row[csv_col].strip()
            if val.lower() in ("true", "1", "yes", "si"):
                history[hist_key] = True
            elif val.lower() in ("false", "0", "no"):
                history[hist_key] = False
            else:
                history[hist_key] = val

    # Parse conditions
    for csv_col, (code, title, system) in CONDITION_MAP.items():
        if csv_col in row and row[csv_col].strip().lower() in (
            "true",
            "1",
            "yes",
            "si",
        ):
            conditions.append({"code": code, "title": title, "system": system})

    # Parse medications (semicolon-separated)
    if "medications" in row and row["medications"].strip():
        for med in row["medications"].split(";"):
            med = med.strip()
            if med:
                medications.append({"name": med, "is_active": True})

    return {
        "external_id": row.get("patient_id", ""),
        "full_name": row.get("full_name", ""),
        "gender": row.get("gender", "unknown"),
        "date_of_birth": row.get("date_of_birth", ""),
        "observations": observations,
        "history": history,
        "conditions": conditions,
        "medications": medications,
        "reason_for_visit": row.get("reason_for_visit", ""),
    }


def ingest_csv(
    csv_path: str, db_session, vault_service, tenant_id: str = "default-clinic"
) -> Dict[str, Any]:
    """
    Ingest a CSV file into the Integrum database.

    Args:
        csv_path: Path to CSV file
        db_session: Async SQLAlchemy session
        vault_service: VaultService instance for encryption
        tenant_id: Tenant identifier

    Returns:
        Summary dict with counts of ingested/rejected records
    """
    from src.models.encounter import (
        Patient,
        EncounterModel,
        ObservationModel,
        EncounterConditionModel,
    )

    total = 0
    ingested = 0
    rejected = 0
    quality_reports = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            patient_id = row.get("patient_id", f"unknown-{total}")

            # Parse row
            parsed = parse_csv_row(row)
            observations = parsed["observations"]

            # Quality check
            report = validate_record(patient_id, observations)
            quality_reports.append(report)

            if not report.is_valid:
                rejected += 1
                print(f"  REJECTED {patient_id}: {'; '.join(report.rejection_reasons)}")
                continue

            # Create patient (or find existing)
            from sqlalchemy import select

            search_hash = vault_service.generate_blind_index(parsed["external_id"])
            stmt = select(Patient).where(Patient.external_id_hash == search_hash)
            result = await db_session.execute(stmt)
            patient = result.scalar_one_or_none()

            if not patient:
                patient = Patient(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    external_id=parsed["external_id"],
                    full_name=parsed["full_name"],
                    gender=parsed["gender"],
                    date_of_birth=parsed["date_of_birth"],
                )
                db_session.add(patient)
                await db_session.flush()

            # Create encounter
            encounter_id = str(uuid.uuid4())
            encounter = EncounterModel(
                id=encounter_id,
                patient_id=patient.id,
                tenant_id=tenant_id,
                status="ANALYZED",
                reason_for_visit=parsed["reason_for_visit"],
            )
            db_session.add(encounter)
            await db_session.flush()

            # Insert observations
            for obs in observations:
                obs_model = ObservationModel(
                    id=str(uuid.uuid4()),
                    encounter_id=encounter_id,
                    code=obs["code"],
                    value=str(obs["value"]),
                )
                db_session.add(obs_model)

            # Insert conditions
            for cond in parsed["conditions"]:
                cond_model = EncounterConditionModel(
                    id=str(uuid.uuid4()),
                    encounter_id=encounter_id,
                    code=cond["code"],
                    title=cond["title"],
                    system=cond["system"],
                )
                db_session.add(cond_model)

            ingested += 1

    await db_session.commit()

    return {
        "total": total,
        "ingested": ingested,
        "rejected": rejected,
        "quality_reports": quality_reports,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest CSV data into Integrum")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    args = parser.parse_args()

    print(f"Ingesting {args.csv}...")
    # This would need async setup to actually run
    # For now, it's a module to be called from the API or a script
    print("Use: from src.pipeline.ingest import ingest_csv")
