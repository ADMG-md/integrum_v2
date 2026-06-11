"""
Database Backfill Script — EAV to JSONB Hybrid Migration.
Processes historical encounters in memory-safe batches of 100 using yield_per.
"""

import asyncio
import json
import os
import sys
import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import SessionLocal
from src.models.encounter import EncounterModel, ObservationModel
from src.domain.models import MetabolicPanelSchema

logger = structlog.get_logger()

# Mapping of LOINC/custom codes to MetabolicPanelSchema fields
OBSERVATION_CODE_MAP = {
    "2339-0": "glucose_mg_dl",
    "4548-4": "hba1c_percent",
    "20448-7": "insulin_mu_u_ml",
    "C-PEP-001": "c_peptide_ng_ml",
    "GADA-001": "gada_antibodies",
    "2160-0": "creatinine_mg_dl",
    "UA-001": "uric_acid_mg_dl",
    "29230-0": "ast_u_l",
    "22538-3": "alt_u_l",
    "GGT-001": "ggt_u_l",
    "ALKPHOS-001": "alkaline_phosphatase_u_l",
    "WBC-001": "wbc_k_ul",
    "26474-7": "lymphocyte_percent",
    "26499-4": "neutrophil_percent",
    "MCV-001": "mcv_fl",
    "RDW-001": "rdw_percent",
    "PLT-001": "platelets_k_u_l",
    "30522-7": "hs_crp_mg_l",
    "FER-001": "ferritin_ng_ml",
    "ALB-001": "albumin_g_dl",
    "11579-0": "tsh_u_iu_ml",
    "FT4-001": "ft4_ng_dl",
    "FT3-001": "ft3_pg_ml",
    "RT3-001": "rt3_ng_dl",
    "SHBG-001": "shbg_nmol_l",
    "CORT-AM": "cortisol_am_mcg_dl",
    "ALDO-001": "aldosterone_ng_dl",
    "RENIN-001": "renin_ng_ml_h",
    "2093-3": "total_cholesterol_mg_dl",
    "13457-7": "ldl_mg_dl",
    "2085-9": "hdl_mg_dl",
    "2571-8": "triglycerides_mg_dl",
    "VLDL-001": "vldl_mg_dl",
    "APOB-001": "apob_mg_dl",
    "LPA-001": "lpa_mg_dl",
    "APOA1-001": "apoa1_mg_dl",
    "vitd_ngml": "vitamin_d_ng_ml",
    "vitb12_pgml": "vitamin_b12_pg_ml",
    "homocys_umolL": "homocysteine_umol_l",
    "tpoab_iuml": "tpo_antibodies_iu_ml",
    "testo_ngdl": "testosterone_total_ng_dl",
    "amh_ngml": "amh_ng_ml",
    "lh_uL": "lh_u_l",
    "fsh_uL": "fsh_u_l",
    "estradiol_pgml": "estradiol_pg_ml",
    "prolactin_ngml": "prolactin_ng_ml",
    "dheas_mcgdl": "dhea_s_mcg_dl",
    "psa_ngml": "psa_ng_ml",
}

BATCH_SIZE = 100


async def backfill_historical_encounters():
    logger.info("Starting database backfill from EAV to JSONB payloads...")
    
    async with SessionLocal() as db:
        # 1. Fetch encounters that do not have JSONB payloads yet
        # Using execution_options(yield_per=BATCH_SIZE) to stream in batches of 100
        stmt = (
            select(EncounterModel)
            .options(selectinload(EncounterModel.observations))
            .where(
                (EncounterModel.metabolic_panel_payload.is_(None)) & 
                (EncounterModel.clinical_history_payload.is_(None))
            )
            .execution_options(yield_per=BATCH_SIZE)
        )
        
        result = await db.stream(stmt)
        processed_count = 0
        
        # 2. Iterate through streamed records memory-safely
        async for encounter in result.scalars():
            try:
                # Reconstruct Metabolic Panel from Observations
                metabolic_data = {}
                for obs in encounter.observations:
                    field_name = OBSERVATION_CODE_MAP.get(obs.code)
                    if field_name:
                        # Convert string value back to appropriate type
                        val = obs.value
                        if val == "True":
                            val = True
                        elif val == "False":
                            val = False
                        else:
                            try:
                                val = float(val)
                            except ValueError:
                                pass
                        metabolic_data[field_name] = val
                
                # Enforce coherence check to ensure data sanity
                if metabolic_data:
                    try:
                        # Validate structure through domain schema
                        panel = MetabolicPanelSchema(**metabolic_data)
                        encounter.metabolic_panel_payload = panel.model_dump()
                    except Exception as coherence_err:
                        logger.warning(
                            "metabolic_coherence_failed_for_encounter",
                            encounter_id=encounter.id,
                            error=str(coherence_err)
                        )
                        # Store raw payload even if warnings exist, fallback to unvalidated dictionary
                        encounter.metabolic_panel_payload = metabolic_data
                
                # Reconstruct Clinical History from clinical_notes
                if encounter.clinical_notes and "History: " in encounter.clinical_notes:
                    try:
                        raw_json = encounter.clinical_notes.split("History: ", 1)[1]
                        history_dict = json.loads(raw_json)
                        encounter.clinical_history_payload = history_dict
                    except Exception as history_err:
                        logger.warning(
                            "history_parsing_failed_for_encounter",
                            encounter_id=encounter.id,
                            error=str(history_err)
                        )
                
                processed_count += 1
                
                # 3. Commit in batches of BATCH_SIZE to optimize transaction log
                if processed_count % BATCH_SIZE == 0:
                    await db.commit()
                    logger.info(
                        "batch_committed", 
                        processed_records=processed_count
                    )
                    
            except Exception as item_err:
                logger.error(
                    "item_processing_failed",
                    encounter_id=encounter.id,
                    error=str(item_err)
                )
                await db.rollback()
                continue
        
        # Commit remaining records
        if processed_count % BATCH_SIZE != 0:
            await db.commit()
            
        logger.info(
            "backfill_completed", 
            total_records_processed=processed_count
        )


if __name__ == "__main__":
    asyncio.run(backfill_historical_encounters())
