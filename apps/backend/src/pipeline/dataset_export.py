"""
Dataset Export — PostgreSQL → ML-Ready CSV/Parquet

Queries finalized encounters from the Integrum database and exports a
flattened, ML-ready dataset for downstream analytics and model training.

Schema:
    - encounter_id, patient_id, age, gender, encounter_date, status
    - All observation columns (LOINC-coded): weight, height, BP, labs, etc.
    - Motor output columns: {motor}_value, {motor}_confidence, {motor}_risk_level
    - Label columns: phenotype_class, cvd_risk, eoss_stage

Usage:
    from src.pipeline.dataset_export import export_dataset
    export_dataset(session, output_path="data/dataset.csv")

    # CLI
    python -m src.pipeline.dataset_export --output data/dataset.csv --format csv
"""

from __future__ import annotations

import sys
import csv
import json
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from src.models.encounter import EncounterModel, ObservationModel, Patient


# --- Observation code → ML column name ---
OBS_COLUMNS = {
    "29463-7": "weight_kg",
    "8302-2": "height_cm",
    "WAIST-001": "waist_cm",
    "HIP-001": "hip_cm",
    "NECK-001": "neck_cm",
    "8480-6": "systolic_bp",
    "8462-4": "diastolic_bp",
    "2339-0": "glucose_mg_dl",
    "4548-4": "hba1c_percent",
    "20448-7": "insulin_mu_u_ml",
    "2160-0": "creatinine_mg_dl",
    "UA-001": "uric_acid_mg_dl",
    "29230-0": "ast_u_l",
    "22538-3": "alt_u_l",
    "GGT-001": "ggt_u_l",
    "ALKPHOS-001": "alkaline_phosphatase_u_l",
    "WBC-001": "wbc_k_ul",
    "26474-7": "lymphocyte_pct",
    "26499-4": "neutrophil_pct",
    "MCV-001": "mcv_fl",
    "RDW-001": "rdw_pct",
    "PLT-001": "platelets_k_ul",
    "30522-7": "hs_crp_mg_l",
    "FER-001": "ferritin_ng_ml",
    "ALB-001": "albumin_g_dl",
    "11579-0": "tsh_uiu_ml",
    "FT4-001": "ft4_ng_dl",
    "FT3-001": "ft3_pg_ml",
    "2093-3": "total_cholesterol_mg_dl",
    "13457-7": "ldl_mg_dl",
    "2085-9": "hdl_mg_dl",
    "2571-8": "triglycerides_mg_dl",
    "VLDL-001": "vldl_mg_dl",
    "APOB-001": "apob_mg_dl",
    "LPA-001": "lpa_mg_dl",
    "APOA1-001": "apoa1_mg_dl",
    "PHQ-9": "phq9_score",
    "GAD-7": "gad7_score",
    "AIS-001": "atenas_insomnia_score",
    "TFEQ-EMOTIONAL": "tfeq_emotional_eating",
    "TFEQ-UNCONTROLLED": "tfeq_uncontrolled_eating",
    "TFEQ-COGNITIVE": "tfeq_cognitive_restraint",
    "LIFE-SLEEP": "sleep_hours",
    "LIFE-EXERCISE": "physical_activity_min_week",
    "LIFE-STRESS": "stress_level_vas",
    "GRIP-STR-R": "grip_right_kg",
    "GRIP-STR-L": "grip_left_kg",
    "GAIT-SPEED": "gait_speed_ms",
    "5XSTS-SEC": "five_x_sts_sec",
    "SARCF-SCORE": "sarcf_score",
    "MMA-001": "muscle_mass_kg",
    "BIA-FAT-PCT": "body_fat_pct",
    "BIA-LEAN-KG": "lean_mass_kg",
    "BIA-VISCERAL": "visceral_fat_area_cm2",
    "BIA-BMR": "basal_metabolic_rate_kcal",
    "UACR-001": "uacr_mg_g",
    "VITB12-001": "vitb12_pg_ml",
    "VITD-001": "vitd_ng_ml",
    "C-PEP-001": "c_peptide_ng_ml",
    "SHBG-001": "shbg_nmol_l",
    "ALDO-001": "aldosterone_ng_dl",
    "RENIN-001": "renin_ng_ml_h",
    "CORT-AM": "cortisol_am_mcg_dl",
    "RT3-001": "rt3_ng_dl",
    "AGE-001": "age_years",
}

# --- Motor name → output column prefix ---
MOTOR_VALUE_COLS = {
    "AcostaPhenotypeMotor": "acosta_phenotype",
    "EOSSStagingMotor": "eoss_stage",
    "SarcopeniaMotor": "sarcopenia_risk",
    "BiologicalAgeMotor": "biological_age",
    "MetabolicPrecisionMotor": "metabolic_precision",
    "DeepMetabolicProxyMotor": "deep_metabolic_proxy",
    "Lifestyle360Motor": "lifestyle_score",
    "AnthropometryMotor": "anthropometry_precision",
    "EndocrineMotor": "endocrine_precision",
    "HypertensionMotor": "hypertension_secondary",
    "InflammationMotor": "inflammation_score",
    "SleepApneaMotor": "sleep_apnea_risk",
    "LaboratoryStewardshipMotor": "lab_stewardship_gap",
    "FunctionalSarcopeniaMotor": "functional_sarcopenia",
    "FLIMotor": "fli_score",
    "VAIMotor": "vai_score",
    "NFSMotor": "nfs_score",
    "ApoBApoA1Motor": "apob_apoa1_ratio",
    "PulsePressureMotor": "pulse_pressure",
    "GLP1MonitoringMotor": "glp1_adverse_risk",
    "ACEScoreEngine": "ace_score",
    "MetforminB12Motor": "metformin_b12_deficiency",
    "CancerScreeningMotor": "cancer_screening_pending",
    "SGLT2iBenefitMotor": "sglt2i_benefit",
    "KFREMotor": "kfre_score",
    "CharlsonMotor": "charlson_index",
    "FreeTestosteroneMotor": "free_testosterone",
    "VitaminDMotor": "vitamin_d_status",
    "FriedFrailtyMotor": "fried_frailty_score",
    "TyGBMIMotor": "tyg_bmi",
    "CVDReclassifierMotor": "cvd_reclass_risk",
    "WomensHealthMotor": "womens_health_risk",
    "MensHealthMotor": "mens_health_risk",
    "BodyCompositionTrendMotor": "body_comp_trend",
    "ObesityPharmaEligibilityMotor": "aom_eligibility",
    "GLP1TitrationMotor": "glp1_titration_step",
    "DrugInteractionMotor": "drug_interaction_alerts",
    "ProteinEngineMotor": "protein_adequacy",
    "CVDHazardMotor": "cvd_hazard_ratio",
    "MarkovProgressionMotor": "markov_progression_state",
    "ObesityMasterMotor": "obesity_master_class",
    "ClinicalGuidelinesMotor": "guideline_adherence",
}


def _extract_risk_level(value_str: str) -> str:
    """Normalize a motor calculated_value to a risk tier."""
    if not value_str:
        return "UNKNOWN"
    v = value_str.upper()
    if any(k in v for k in ["HIGH", "SEVERE", "3", "STAGE 3", "ELEVATED"]):
        return "HIGH"
    if any(k in v for k in ["MODERATE", "MEDIUM", "2", "STAGE 2", "INTERMEDIATE"]):
        return "MODERATE"
    if any(k in v for k in ["LOW", "MILD", "1", "STAGE 1", "OPTIMAL"]):
        return "LOW"
    if any(k in v for k in ["NORMAL", "HEALTHY", "0", "NO RISK"]):
        return "NORMAL"
    return "UNKNOWN"


def _flatten_observations(observations: List[ObservationModel]) -> Dict[str, Any]:
    """Convert list of observations to flat column dict."""
    row = {}
    for obs in observations:
        col_name = OBS_COLUMNS.get(obs.code)
        if col_name:
            try:
                row[col_name] = float(obs.value)
            except (ValueError, TypeError):
                row[col_name] = obs.value
    return row


def _flatten_motor_outputs(
    phenotype_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Flatten motor outputs into columnar format."""
    if not phenotype_result:
        return {}

    row = {}
    for motor_name, output in phenotype_result.items():
        if not isinstance(output, dict):
            continue

        prefix = MOTOR_VALUE_COLS.get(motor_name, motor_name.lower())
        value = output.get("calculated_value", "")
        confidence = output.get("confidence")
        evidence = output.get("evidence", [])
        estado_ui = output.get("estado_ui", "")
        risk_level = _extract_risk_level(str(value))

        row[f"{prefix}_value"] = value
        row[f"{prefix}_confidence"] = confidence
        row[f"{prefix}_risk_level"] = risk_level
        row[f"{prefix}_status"] = estado_ui
        row[f"{prefix}_evidence_count"] = (
            len(evidence) if isinstance(evidence, list) else 0
        )

    return row


def _build_derived_columns(
    obs: Dict[str, Any], motors: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute derived/feature engineering columns."""
    derived = {}

    if "weight_kg" in obs and "height_cm" in obs and obs["height_cm"] > 0:
        height_m = obs["height_cm"] / 100
        derived["bmi"] = round(obs["weight_kg"] / (height_m**2), 2)

    if obs.get("systolic_bp") and obs.get("diastolic_bp"):
        derived["pulse_pressure_calc"] = obs["systolic_bp"] - obs["diastolic_bp"]

    if obs.get("hdl_mg_dl") and obs.get("triglycerides_mg_dl"):
        derived["non_hdl_chol"] = (
            obs.get("total_cholesterol_mg_dl", 0) - obs["hdl_mg_dl"]
        )
        try:
            derived["tg_hdl_ratio"] = round(
                obs["triglycerides_mg_dl"] / max(obs["hdl_mg_dl"], 1), 2
            )
        except (ZeroDivisionError, TypeError):
            derived["tg_hdl_ratio"] = None

    if obs.get("ldl_mg_dl") and obs.get("triglycerides_mg_dl"):
        try:
            derived["ldl_tg_ratio"] = round(
                obs["ldl_mg_dl"] / max(obs["triglycerides_mg_dl"], 1), 2
            )
        except (ZeroDivisionError, TypeError):
            derived["ldl_tg_ratio"] = None

    if obs.get("waist_cm") and obs.get("hip_cm") and obs["hip_cm"] > 0:
        derived["whr"] = round(obs["waist_cm"] / obs["hip_cm"], 3)

    acosta = motors.get("AcostaPhenotypeMotor", {})
    eoss = motors.get("EOSSStagingMotor", {})
    derived["phenotype_label"] = acosta.get("calculated_value", "UNKNOWN")
    derived["eoss_label"] = eoss.get("calculated_value", "UNKNOWN")
    derived["cv_risk_label"] = _extract_risk_level(
        motors.get("CVDHazardMotor", {}).get("calculated_value", "")
    )

    return derived


def encounter_to_row(encounter: EncounterModel) -> Dict[str, Any]:
    """Convert a single EncounterModel into a flat ML-ready row."""
    patient = encounter.patient

    age = None
    if patient and patient.date_of_birth:
        try:
            dob_str = patient.date_of_birth
            if isinstance(dob_str, str):
                dob = date.fromisoformat(dob_str[:10])
            else:
                dob = dob_str
            age = (date.today() - dob).days // 365
        except Exception:
            age = None

    base = {
        "encounter_id": encounter.id,
        "patient_id": encounter.patient_id if patient else "",
        "age": age,
        "gender": patient.gender if patient else "",
        "encounter_date": (
            encounter.created_at.date().isoformat() if encounter.created_at else ""
        ),
        "status": encounter.status,
        "agreement_rate": encounter.agreement_rate,
        "reason_for_visit": encounter.reason_for_visit or "",
    }

    obs_dict = _flatten_observations(list(encounter.observations))
    motor_dict = _flatten_motor_outputs(encounter.phenotype_result)
    derived_dict = _build_derived_columns(obs_dict, encounter.phenotype_result or {})

    row = {**base, **obs_dict, **motor_dict, **derived_dict}
    return row


def get_all_columns(rows: List[Dict[str, Any]]) -> List[str]:
    """Union of all column names across rows."""
    cols = set()
    for row in rows:
        cols.update(row.keys())
    return sorted(cols)


def export_dataset(
    session: Session,
    output_path: str,
    format: str = "csv",
    status_filter: Optional[str] = "FINALIZED",
    limit: Optional[int] = None,
    include_deltas: bool = True,
) -> Dict[str, Any]:
    """
    Query finalized encounters and export as ML-ready dataset.

    Args:
        session: SQLAlchemy session
        output_path: Output file path (.csv or .parquet)
        format: "csv" or "parquet" (parquet requires pandas)
        status_filter: Only export encounters with this status. None = all.
        limit: Max number of encounters to export
        include_deltas: Compute delta vs previous encounter per patient (T0, T1, T2...)

    Returns:
        Summary dict with row count, columns, and file path
    """
    stmt = (
        select(EncounterModel)
        .options(
            selectinload(EncounterModel.observations),
            selectinload(EncounterModel.patient),
        )
        .order_by(EncounterModel.patient_id, EncounterModel.created_at)
    )

    if status_filter:
        stmt = stmt.where(EncounterModel.status == status_filter)

    if limit:
        stmt = stmt.limit(limit)

    encounters = session.execute(stmt).scalars().all()

    if not encounters:
        return {
            "exported": 0,
            "columns": [],
            "output_path": output_path,
            "format": format,
            "status": "no_data",
        }

    rows = []
    prev_rows_by_patient: Dict[str, Dict[str, Any]] = {}

    for enc in encounters:
        try:
            row = encounter_to_row(enc)
        except Exception as e:
            print(f"  SKIP encounter {enc.id}: {e}")
            continue

        patient_id = row.get("patient_id", "")

        if include_deltas and patient_id in prev_rows_by_patient:
            prev = prev_rows_by_patient[patient_id]
            delta_t = _compute_deltas(prev, row)
            row = {**row, **delta_t}
            prev_t = prev.get("encounter_number", "T0")
            current_t = int(prev_t.replace("T", "")) + 1
            row["encounter_number"] = f"T{current_t}"
            row["delta_vs_previous"] = prev_t
        else:
            row["encounter_number"] = "T0"
            row["delta_vs_previous"] = None

        rows.append(row)
        prev_rows_by_patient[patient_id] = row

    all_cols = get_all_columns(rows)
    priority_cols = [
        "encounter_id",
        "patient_id",
        "encounter_number",
        "delta_vs_previous",
        "encounter_date",
        "age",
        "gender",
        "status",
        "agreement_rate",
    ]
    cols_to_write = priority_cols + [c for c in all_cols if c not in priority_cols]

    if format == "parquet":
        if not HAS_PANDAS:
            raise ImportError(
                "pandas is required for Parquet export. Install with: pip install pandas"
            )
        df = pd.DataFrame(rows)
        df = df.reindex(columns=cols_to_write)
        df.to_parquet(output_path, index=False)
    else:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cols_to_write, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    return {
        "exported": len(rows),
        "columns": cols_to_write,
        "output_path": output_path,
        "format": format,
        "status": "success",
    }


def _compute_deltas(prev: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """Compute delta (current - previous) for key clinical metrics."""
    deltas = {}
    metrics = [
        "weight_kg",
        "bmi",
        "waist_cm",
        "hip_cm",
        "glucose_mg_dl",
        "hba1c_percent",
        "triglycerides_mg_dl",
        "ldl_mg_dl",
        "hdl_mg_dl",
        "systolic_bp",
        "diastolic_bp",
        "whr",
        "tg_hdl_ratio",
        "non_hdl_chol",
    ]
    for metric in metrics:
        prev_val = prev.get(metric)
        curr_val = current.get(metric)
        if prev_val is not None and curr_val is not None:
            try:
                deltas[f"delta_{metric}"] = round(float(curr_val) - float(prev_val), 3)
            except (ValueError, TypeError):
                deltas[f"delta_{metric}"] = None
        else:
            deltas[f"delta_{metric}"] = None

    return deltas


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export Integrum dataset for ML")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--format", default="csv", choices=["csv", "parquet"], help="Output format"
    )
    parser.add_argument("--status", default="FINALIZED", help="Encounter status filter")
    parser.add_argument("--limit", type=int, default=None, help="Max rows")
    parser.add_argument(
        "--db-url", default=None, help="Database URL (default: from .env)"
    )
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Use --db-url or set DATABASE_URL in .env")
        sys.exit(1)

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print(f"Exporting to {args.output} ...")
    result = export_dataset(
        session,
        args.output,
        format=args.format,
        status_filter=args.status,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, default=str))
