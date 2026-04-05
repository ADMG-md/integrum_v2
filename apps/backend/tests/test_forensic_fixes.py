import sys
import os
import math

# Add apps/backend to path
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

from src.engines.domain import Encounter, Observation, Condition
from src.engines.specialty_runner import specialty_runner

def verify_math_properties():
    print("🧪 VERIFYING DOMAIN MATH PROPERTIES (FORENSIC FIXES)")
    
    # CASE 1: Missing observations (Should not crash)
    e_empty = Encounter(id="E-EMPTY", observations=[])
    print(f"   Empty Encounter: waist_to_hip={e_empty.waist_to_hip}")
    assert e_empty.waist_to_hip is None
    
    # CASE 2: Partially missing observations
    e_partial = Encounter(id="E-PARTIAL", observations=[Observation(code="WAIST-001", value=100)])
    print(f"   Partial Encounter: waist_to_hip={e_partial.waist_to_hip}")
    assert e_partial.waist_to_hip is None
    
    # CASE 3: Proper calculation (BUG_01 fix)
    e_full = Encounter(id="E-FULL", observations=[
        Observation(code="WAIST-001", value=100.0),
        Observation(code="HIP-001", value=110.0),
        Observation(code="8302-2", value=180.0) # Height
    ])
    wth = e_full.waist_to_hip
    print(f"   Full Encounter: waist_to_hip={wth}")
    assert wth == 100.0 / 110.0
    
    # CASE 4: Body Roundness Index (BUG_02 fix)
    bri = e_full.body_roundness_index
    print(f"   Full Encounter: BRI={bri}")
    # BRI calculation check: pi*1.8 ~ 5.65. w_m = 1.0. 1 - (1/5.65)^2 ~ 0.968
    # 364.2 - 365.5 * sqrt(0.968) ~ 364.2 - 365.5 * 0.984 ~ 364.2 - 359.8 ~ 4.4
    assert bri is not None and 4.0 < bri < 5.0
    
    print("✅ MATH PROPERTIES VALIDATED.")

def verify_orchestration():
    print("\n🧪 VERIFYING UNIFIED ORCHESTRATION")
    
    # Check if legacy motors are registered in SpecialtyRunner
    motor_names = [m.__class__.__name__ for m in specialty_runner.get_all_motors()]
    print(f"   Registered Motors: {motor_names}")
    
    expected = ["KleiberScalingMotor", "CoxHazardMotor", "MarkovProgressionMotor", "SleepApneaPrecisionMotor"]
    for ex in expected:
        assert ex in motor_names, f"Motor {ex} missing from SpecialtyRunner"
    
    print("✅ ORCHESTRATION UNIFIED.")

if __name__ == "__main__":
    try:
        verify_math_properties()
        verify_orchestration()
        print("\n🏆 FORENSIC REMEDIATION SUCCESSFUL. Zero crashes, Zero redundancies.")
    except Exception as e:
        print(f"\n❌ FORENSIC VERIFICATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
