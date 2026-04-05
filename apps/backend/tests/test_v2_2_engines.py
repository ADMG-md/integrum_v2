import sys
import os

# Add apps/backend to path
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

from src.engines.domain import Encounter, Observation, Condition
from src.engines.specialty_runner import specialty_runner

def run_auditor_matrix():
    print("--- 🩺 INTEGRUM V2.2: MANDATORY AUDIT TEST MATRIX ---")
    
    # --- TEST_01: GAD-7 = 12 (Exact 0.65 Confidence) ---
    e1 = Encounter(
        id="TEST_01",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="GAD-7", value=12),
            Observation(code="8302-2", value=165.0), # 165cm
            Observation(code="29463-7", value=95.0),   # 95kg -> BMI ~34.9
        ],
        metadata={"sex": "F"}
    )
    res1 = specialty_runner.run_all(e1).get("AcostaPhenotypeMotor")
    print(f"\n[TEST_01] GAD-7=12 (0.65 Threshold):")
    assert res1 is not None, "Motor skipped due to validation failure"
    assert res1.confidence == 0.65, f"Expected 0.65, got {res1.confidence}"
    assert res1.estado_ui == "PROBABLE_WARNING", f"Expected PROBABLE_WARNING, got {res1.estado_ui}"
    assert "Naltrexona/Bupropión" in res1.recomendacion_farmacologica, "Pharma rec missing for 0.65"
    print("✅ Passed: 0.65 is bottom of acceptance range.")

    # --- TEST_02: Saciedad Temprana (0.60 Confidence) ---
    e2 = Encounter(
        id="TEST_02",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="ST-001", value=1),
            Observation(code="8302-2", value=170.0),
            Observation(code="29463-7", value=100.0),
        ],
        metadata={"sex": "M"}
    )
    res2 = specialty_runner.run_all(e2).get("AcostaPhenotypeMotor")
    print(f"\n[TEST_02] Early Satiety (< 0.65):")
    assert res2 is not None
    assert res2.confidence == 0.60
    assert res2.estado_ui == "INDETERMINATE_LOCKED"
    assert "Indicar MCG de 14 días" in res2.dato_faltante
    print("✅ Passed: Locked due to low confidence (< 0.65).")

    # --- TEST_03: Weight Loss 1.5kg (RPL Artefact Guard) ---
    e3 = Encounter(
        id="TEST_03",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="29463-7", value=98.5), # Weight kg
            Observation(code="8302-2", value=170.0),
            Observation(code="MMA-001", value=24.2), # Current Muscle
        ],
        metadata={
            "sex": "M",
            "prev_weight_kg": 100.0,      # Delta Weight = 1.5kg (< 2.0kg)
            "prev_muscle_mass_kg": 25.0    # Delta Muscle = 0.8
        }
    )
    res3 = specialty_runner.run_all(e3).get("SarcopeniaMonitorMotor")
    print("\n[TEST_03] RPL Guard (Delta < 2.0kg):")
    # rpl should NOT be in metadata or be 0.0 if guard worked
    assert res3.metadata.get("rpl", 0.0) == 0.0
    assert res3.metadata.get("alerta_roja") == False
    print("✅ Passed: Sarcopenia alert suppressed for minor weight fluctuation.")

    # --- TEST_04: Sarcopenia Risk + Renal Failure (Priority) ---
    e4 = Encounter(
        id="TEST_04",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="8302-2", value=175.0),
            Observation(code="29463-7", value=120.0),
            Observation(code="FFM-001", value=85.0),   
            Observation(code="2160-0", value=1.8),     
            Observation(code="AGE-001", value=50),
        ],
        metadata={"sex": "M"}
    )
    res4 = specialty_runner.run_all(e4).get("ProteinEngineMotor")
    print("\n[TEST_04] Renal Priority (IBW vs FFM):")
    target = res4.metadata.get("target_grams")
    print(f"   Protein target: {target}g")
    # IBW for 175cm M ~ 70kg. 0.8 * 70 = 56g. 
    assert target < 60.0, f"Target {target} suggests FFM was used instead of IBW"
    assert "Prioridad Renal" in res4.metadata.get("limitadores")[0]
    print("✅ Passed: Protein target correctly capped using IBW.")

    # --- TEST_05: eGFR 55 + Albuminuria (Pharma Shield) ---
    e5 = Encounter(
        id="TEST_05",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(code="2160-0", value=1.5),     
            Observation(code="UACR-001", value=45),    
            Observation(code="AGE-001", value=50),
            Observation(code="FFM-001", value=80.0),
            Observation(code="8302-2", value=175.0),
            Observation(code="29463-7", value=110.0),
        ],
        metadata={"sex": "M"}
    )
    res5 = specialty_runner.run_all(e5).get("ProteinEngineMotor")
    print("\n[TEST_05] Pharma Shield Activation:")
    assert res5 is not None
    pharma_str = " ".join(res5.recomendacion_farmacologica)
    assert "Iniciar iSGLT2" in pharma_str
    print("✅ Passed: Renal shielding recommendations triggered.")

if __name__ == "__main__":
    try:
        run_auditor_matrix()
        print("\n🏆 ALL AUDIT TESTS PASSED. SYSTEM HARDENED.")
    except AssertionError as e:
        print(f"\n❌ AUDIT FAILED: {str(e)}")
        sys.exit(1)
