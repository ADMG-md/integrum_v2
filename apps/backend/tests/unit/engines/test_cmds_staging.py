import pytest
from typing import List, Dict, Any

from src.engines.domain import (
    Encounter,
    Condition,
    Observation,
    MedicationStatement,
    DemographicsSchema,
    MetabolicPanelSchema,
    ClinicalHistory
)
from src.engines.specialty.cmds import CMDSStagingMotor


def _build_encounter(
    conditions: List[str] = [],
    meds: List[Dict[str, Any]] = [],
    waist: float = None,
    gender: str = "male",
    sbp: float = None,
    dbp: float = None,
    glucose: float = None,
    hba1c: float = None,
    tg: float = None,
    hdl: float = None,
    egfr: float = None,
    history_dm2: bool = False
) -> Encounter:
    demographics = DemographicsSchema(gender=gender, age_years=40)
    metabolic = MetabolicPanelSchema(
        glucose_mg_dl=glucose,
        hba1c_percent=hba1c,
        triglycerides_mg_dl=tg,
        hdl_mg_dl=hdl
    )
    
    cond_objs = [Condition(code=c, title=c) for c in conditions]
    
    med_objs = [
        MedicationStatement(code="TEST", name=m["name"], is_active=m.get("is_active", True))
        for m in meds
    ]
    
    obs = []
    if waist is not None:
        obs.append(Observation(code="ANTHRO-004", value=waist, unit="cm"))
    if sbp is not None:
        obs.append(Observation(code="BP-001", value=sbp, unit="mmHg"))
    if dbp is not None:
        obs.append(Observation(code="BP-002", value=dbp, unit="mmHg"))
    if egfr is not None:
        # EGFR is calculated via RenalFunction, which uses creatinine and age.
        # But we can also just inject it if we spoof the RenalFunction, 
        # actually RenalFunction uses creatinine_mg_dl. Let's just mock the property if needed,
        # or supply creatinine. Let's supply creatinine to get eGFR.
        # Alternatively, the motor reads encounter.egfr_ckd_epi which calls _get_renal().
        pass

    # For eGFR to work naturally, we need creatinine.
    # 1.0 creatinine in a 40yo male gives eGFR around 90-100.
    # 2.5 creatinine gives eGFR < 30.
    # 1.5 creatinine gives eGFR 30-59.
    creatinine = None
    if egfr is not None:
        if egfr < 30:
            creatinine = 3.0
        elif egfr <= 59:
            creatinine = 1.5
        else:
            creatinine = 0.9
            
    if creatinine:
        metabolic = MetabolicPanelSchema(
            glucose_mg_dl=glucose,
            hba1c_percent=hba1c,
            triglycerides_mg_dl=tg,
            hdl_mg_dl=hdl,
            creatinine_mg_dl=creatinine
        )
        
    history = ClinicalHistory(has_type2_diabetes=history_dm2)

    return Encounter(
        id="TEST-ENCOUNTER",
        demographics=demographics,
        metabolic_panel=metabolic,
        conditions=cond_objs,
        observations=obs,
        medications=med_objs,
        history=history
    )


def test_e4_by_dm2_no_labs():
    # Patient E4 by DM2 without labs available.
    enc = _build_encounter(conditions=["E11"])
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.calculated_value == "Stage 4"
    assert res.estado_ui == "CONFIRMED_ACTIVE"
    # missing components should be 4 (Waist, BP, TG, HDL) because SM_glu is automatically 1 due to DM2
    assert res.metadata["completeness_status"] == "partial"
    assert len(res.metadata["missing_components"]) == 4


def test_e3_by_sm_count_3_with_sm_glu_1():
    # Patient E3 by SM_count=3 with SM_glu=1
    # Needs: Waist, BP, Glu -> 3. TG, HDL normal.
    enc = _build_encounter(
        waist=95, gender="male",  # sm_waist=1
        sbp=135, dbp=80,          # sm_bp=1
        glucose=110, hba1c=5.9,   # sm_glu=1
        tg=100, hdl=50,           # normal
        egfr=90
    )
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.calculated_value == "Stage 3"
    assert res.metadata["sm_count"] == 3
    assert res.metadata["sm_glu"] == 1
    assert res.metadata["completeness_status"] == "complete"


def test_e2_isolated_prediabetes():
    # Patient E2 by isolated prediabetes.
    enc = _build_encounter(
        waist=80, gender="male",  # sm_waist=0
        sbp=110, dbp=70,          # sm_bp=0
        glucose=115, hba1c=6.0,   # sm_glu=1
        tg=100, hdl=50,           # sm_tg=0, sm_hdl=0
        egfr=90
    )
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.calculated_value == "Stage 2"
    assert res.metadata["sm_count"] == 1
    assert res.metadata["sm_glu"] == 1
    assert res.metadata["completeness_status"] == "complete"


def test_active_antihypertensive_sm_bp_1():
    # Patient with active antihypertensive -> SM_bp=1
    enc = _build_encounter(
        meds=[{"name": "Losartan 50mg", "is_active": True}],
        waist=80, gender="male",  
        sbp=110, dbp=70,          # Normal BP but on meds
        glucose=90, hba1c=5.0,    
        tg=100, hdl=50,           
        egfr=90
    )
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.metadata["sm_bp"] == 1
    # SM count = 1, so Stage 1
    assert res.calculated_value == "Stage 1"
    assert res.metadata["completeness_status"] == "complete"


def test_missing_partial_labs():
    # Patient with missing partial labs -> completeness_status=partial.
    enc = _build_encounter(
        waist=95, gender="male",  # sm_waist=1
        glucose=115,              # sm_glu=1
        # missing bp, tg, hdl, egfr
    )
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.metadata["completeness_status"] == "partial"
    assert "BP" in res.metadata["missing_components"]
    assert "Triglycerides" in res.metadata["missing_components"]
    assert "HDL" in res.metadata["missing_components"]
    
    # SM count = 2, SM_glu = 1. But because no DM2/CVD and not E4/E3, we fall to E2 for prediabetes.
    assert res.calculated_value == "Stage 2"

def test_indeterminate_all_missing():
    enc = _build_encounter()
    motor = CMDSStagingMotor()
    res = motor.compute(enc)
    
    assert res.metadata["completeness_status"] == "indeterminate"
    assert res.calculated_value == "Indeterminate"
