"""
Observation Mapper — converts hierarchical encounter payload into flat LOINC observations.

This module extracts the observation-building logic from the encounter endpoint,
following Clean Architecture: pure mapping functions, no FastAPI, no DB.
"""

from src.engines.domain import Observation
from typing import List, Optional


def map_biometrics_to_observations(
    biometrics, gender: Optional[str] = None
) -> List[Observation]:
    """Map biometrics payload to LOINC-coded observations."""
    obs: List[Observation] = []
    b = biometrics

    obs.append(Observation(code="29463-7", value=b.weight_kg, unit="kg"))
    obs.append(Observation(code="8302-2", value=b.height_cm, unit="cm"))

    if b.waist_cm:
        obs.append(Observation(code="WAIST-001", value=b.waist_cm, unit="cm"))
    if b.hip_cm:
        obs.append(Observation(code="HIP-001", value=b.hip_cm, unit="cm"))
    if b.neck_cm:
        obs.append(Observation(code="NECK-001", value=b.neck_cm, unit="cm"))
    if b.systolic_bp:
        obs.append(Observation(code="8480-6", value=b.systolic_bp, unit="mmHg"))
    if b.diastolic_bp:
        obs.append(Observation(code="8462-4", value=b.diastolic_bp, unit="mmHg"))
    if b.arm_circumference_cm:
        obs.append(
            Observation(code="ARM-CIRC", value=b.arm_circumference_cm, unit="cm")
        )
    if b.calf_circumference_cm:
        obs.append(
            Observation(code="CALF-CIRC", value=b.calf_circumference_cm, unit="cm")
        )

    # BIA observations for Sarcopenia and Metabolic engines
    if b.muscle_mass_kg:
        obs.append(
            Observation(
                code="MMA-001", value=b.muscle_mass_kg, unit="kg", category="BIA"
            )
        )
        obs.append(
            Observation(
                code="MUSCLE-KG", value=b.muscle_mass_kg, unit="kg", category="BIA"
            )
        )
        obs.append(
            Observation(
                code="BIA-MUSCLE-KG", value=b.muscle_mass_kg, unit="kg", category="BIA"
            )
        )
    if b.skeletal_muscle_index:
        obs.append(
            Observation(
                code="SMI-001",
                value=b.skeletal_muscle_index,
                unit="kg/m2",
                category="BIA",
            )
        )
    if b.body_fat_percent:
        obs.append(
            Observation(
                code="BIA-FAT-PCT", value=b.body_fat_percent, unit="%", category="BIA"
            )
        )
    if b.fat_mass_kg:
        obs.append(
            Observation(
                code="BIA-FAT-KG", value=b.fat_mass_kg, unit="kg", category="BIA"
            )
        )
    if b.lean_mass_kg:
        obs.append(
            Observation(
                code="BIA-LEAN-KG", value=b.lean_mass_kg, unit="kg", category="BIA"
            )
        )
    # LBM por fórmula de Boer (SOURCE: Boer 1984, JPEN 8:670)
    if b.weight_kg and b.height_cm and gender:
        sex = gender.upper()
        if sex in ("M", "MALE"):
            lbm_boer = round((0.407 * b.weight_kg) + (0.267 * b.height_cm) - 19.2, 1)
        elif sex in ("F", "FEMALE"):
            lbm_boer = round((0.252 * b.weight_kg) + (0.473 * b.height_cm) - 48.3, 1)
        else:
            lbm_boer = None
        if lbm_boer is not None and lbm_boer > 0:
            obs.append(
                Observation(code="LBM-BOER", value=lbm_boer, unit="kg", category="BIA")
            )
    if b.visceral_fat_area_cm2:
        obs.append(
            Observation(
                code="BIA-VISCERAL",
                value=b.visceral_fat_area_cm2,
                unit="cm2",
                category="BIA",
            )
        )
    if b.visceral_fat_level:
        obs.append(
            Observation(
                code="BIA-VISCERAL-LVL",
                value=b.visceral_fat_level,
                unit="level",
                category="BIA",
            )
        )
    if b.basal_metabolic_rate:
        obs.append(
            Observation(
                code="BIA-BMR",
                value=b.basal_metabolic_rate,
                unit="kcal",
                category="BIA",
            )
        )
    if b.total_body_water_percent:
        obs.append(
            Observation(
                code="BIA-TBW",
                value=b.total_body_water_percent,
                unit="%",
                category="BIA",
            )
        )
    if b.bone_mass_kg:
        obs.append(
            Observation(
                code="BIA-BONE", value=b.bone_mass_kg, unit="kg", category="BIA"
            )
        )

    return obs


def map_metabolic_to_observations(metabolic) -> List[Observation]:
    """Map metabolic panel payload to LOINC-coded observations."""
    obs: List[Observation] = []
    m = metabolic

    # Glucose/Insulin
    if m.glucose_mg_dl:
        obs.append(Observation(code="2339-0", value=m.glucose_mg_dl, unit="mg/dL"))
    if m.hba1c_percent:
        obs.append(Observation(code="4548-4", value=m.hba1c_percent, unit="%"))
    if m.insulin_mu_u_ml:
        obs.append(Observation(code="20448-7", value=m.insulin_mu_u_ml, unit="muU/mL"))
    if m.c_peptide_ng_ml:
        obs.append(Observation(code="C-PEP-001", value=m.c_peptide_ng_ml, unit="ng/mL"))
    if m.gada_antibodies:
        obs.append(
            Observation(code="GADA-001", value=m.gada_antibodies, category="Autoimmune")
        )

    # Renal
    if m.creatinine_mg_dl:
        obs.append(Observation(code="2160-0", value=m.creatinine_mg_dl, unit="mg/dL"))
    if m.uric_acid_mg_dl:
        obs.append(Observation(code="UA-001", value=m.uric_acid_mg_dl, unit="mg/dL"))

    # Liver
    if m.ast_u_l:
        obs.append(Observation(code="29230-0", value=m.ast_u_l, unit="U/L"))
    if m.alt_u_l:
        obs.append(Observation(code="22538-3", value=m.alt_u_l, unit="U/L"))
    if m.ggt_u_l:
        obs.append(Observation(code="GGT-001", value=m.ggt_u_l, unit="U/L"))
    if m.alkaline_phosphatase_u_l:
        obs.append(
            Observation(
                code="ALKPHOS-001", value=m.alkaline_phosphatase_u_l, unit="U/L"
            )
        )

    # CBC
    if m.wbc_k_ul:
        obs.append(Observation(code="WBC-001", value=m.wbc_k_ul, unit="k/uL"))
    if m.lymphocyte_percent:
        obs.append(Observation(code="26474-7", value=m.lymphocyte_percent, unit="%"))
    if m.neutrophil_percent:
        obs.append(Observation(code="26499-4", value=m.neutrophil_percent, unit="%"))
    if m.mcv_fl:
        obs.append(Observation(code="MCV-001", value=m.mcv_fl, unit="fL"))
    if m.rdw_percent:
        obs.append(Observation(code="RDW-001", value=m.rdw_percent, unit="%"))
    if m.platelets_k_u_l:
        obs.append(Observation(code="PLT-001", value=m.platelets_k_u_l, unit="k/uL"))

    # Inflammation/Iron
    if m.hs_crp_mg_l:
        obs.append(Observation(code="30522-7", value=m.hs_crp_mg_l, unit="mg/L"))
    if m.ferritin_ng_ml:
        obs.append(Observation(code="FER-001", value=m.ferritin_ng_ml, unit="ng/mL"))
    if m.albumin_g_dl:
        obs.append(Observation(code="ALB-001", value=m.albumin_g_dl, unit="g/dL"))

    # Thyroid
    if m.tsh_u_iu_ml:
        obs.append(Observation(code="11579-0", value=m.tsh_u_iu_ml, unit="uIU/mL"))
    if m.ft4_ng_dl:
        obs.append(Observation(code="FT4-001", value=m.ft4_ng_dl, unit="ng/dL"))
    if m.ft3_pg_ml:
        obs.append(Observation(code="FT3-001", value=m.ft3_pg_ml, unit="pg/mL"))
    if m.rt3_ng_dl:
        obs.append(Observation(code="RT3-001", value=m.rt3_ng_dl, unit="ng/dL"))
    if m.shbg_nmol_l:
        obs.append(Observation(code="SHBG-001", value=m.shbg_nmol_l, unit="nmol/L"))
    if m.cortisol_am_mcg_dl:
        obs.append(
            Observation(code="CORT-AM", value=m.cortisol_am_mcg_dl, unit="mcg/dL")
        )
    if m.aldosterone_ng_dl:
        obs.append(
            Observation(code="ALDO-001", value=m.aldosterone_ng_dl, unit="ng/dL")
        )
    if m.renin_ng_ml_h:
        obs.append(Observation(code="RENIN-001", value=m.renin_ng_ml_h, unit="ng/mL/h"))

    # Lipids
    if m.total_cholesterol_mg_dl:
        obs.append(
            Observation(code="2093-3", value=m.total_cholesterol_mg_dl, unit="mg/dL")
        )
    if m.ldl_mg_dl:
        obs.append(Observation(code="13457-7", value=m.ldl_mg_dl, unit="mg/dL"))
    if m.hdl_mg_dl:
        obs.append(Observation(code="2085-9", value=m.hdl_mg_dl, unit="mg/dL"))
    if m.triglycerides_mg_dl:
        obs.append(
            Observation(code="2571-8", value=m.triglycerides_mg_dl, unit="mg/dL")
        )
    if m.vldl_mg_dl:
        obs.append(Observation(code="VLDL-001", value=m.vldl_mg_dl, unit="mg/dL"))
    if m.apob_mg_dl:
        obs.append(Observation(code="APOB-001", value=m.apob_mg_dl, unit="mg/dL"))
    if m.lpa_mg_dl:
        obs.append(Observation(code="LPA-001", value=m.lpa_mg_dl, unit="mg/dL"))
    if m.apoa1_mg_dl:
        obs.append(Observation(code="APOA1-001", value=m.apoa1_mg_dl, unit="mg/dL"))

    return obs


def map_psychometrics_to_observations(psychometrics) -> List[Observation]:
    """Map psychometrics payload to observations."""
    obs: List[Observation] = []
    p = psychometrics

    if p.phq9_score is not None:
        obs.append(
            Observation(code="PHQ-9", value=p.phq9_score, category="Psychometry")
        )
    if p.gad7_score is not None:
        obs.append(
            Observation(code="GAD-7", value=p.gad7_score, category="Psychometry")
        )
    if p.atenas_insomnia_score is not None:
        obs.append(
            Observation(
                code="AIS-001", value=p.atenas_insomnia_score, category="Psychometry"
            )
        )
    if p.tfeq_emotional_eating is not None:
        obs.append(
            Observation(
                code="TFEQ-EMOTIONAL",
                value=p.tfeq_emotional_eating,
                category="Psychometry",
            )
        )
    if p.tfeq_uncontrolled_eating is not None:
        obs.append(
            Observation(
                code="TFEQ-UNCONTROLLED",
                value=p.tfeq_uncontrolled_eating,
                category="Psychometry",
            )
        )
    if p.tfeq_cognitive_restraint is not None:
        obs.append(
            Observation(
                code="TFEQ-COGNITIVE",
                value=p.tfeq_cognitive_restraint,
                category="Psychometry",
            )
        )

    return obs


def map_lifestyle_to_observations(lifestyle) -> List[Observation]:
    """Map lifestyle payload to observations."""
    obs: List[Observation] = []
    l = lifestyle

    if l.sleep_hours is not None:
        obs.append(
            Observation(
                code="LIFE-SLEEP",
                value=l.sleep_hours,
                unit="hours",
                category="Lifestyle",
            )
        )
    if l.physical_activity_min_week is not None:
        obs.append(
            Observation(
                code="LIFE-EXERCISE",
                value=l.physical_activity_min_week,
                unit="min/week",
                category="Lifestyle",
            )
        )
    if l.stress_level_vas is not None:
        obs.append(
            Observation(
                code="LIFE-STRESS",
                value=l.stress_level_vas,
                unit="1-10",
                category="Lifestyle",
            )
        )

    return obs


def build_flat_observations(payload, gender: Optional[str] = None) -> list:
    flat: list = list(payload.observations)

    if payload.biometrics:
        flat.extend(map_biometrics_to_observations(payload.biometrics, gender))
    if payload.metabolic:
        flat.extend(map_metabolic_to_observations(payload.metabolic))
    if payload.psychometrics:
        flat.extend(map_psychometrics_to_observations(payload.psychometrics))
    if payload.lifestyle:
        flat.extend(map_lifestyle_to_observations(payload.lifestyle))

    return flat
