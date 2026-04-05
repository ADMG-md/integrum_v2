from src.schemas.encounter import ObservationSchema
from pydantic import ValidationError

def test_biological_guardrails():
    print("🛡️ TESTING BIOLOGICAL GUARDRAILS (SaMD Safety) 🛡️")
    
    # 1. Valid value
    obs = ObservationSchema(code="2339-0", value=110.5)
    print(f"✅ Normal value accepted: {obs.value}")

    # 2. Extreme Low (Below -50)
    try:
        ObservationSchema(code="TEMP", value=-100)
        raise Exception("Should have rejected -100")
    except ValidationError as e:
        print(f"✅ Rejected extreme low (-100): {e.errors()[0]['msg']}")

    # 3. Extreme High (Above 1000)
    try:
        ObservationSchema(code="GLUCOSE", value=2500)
        raise Exception("Should have rejected 2500")
    except ValidationError as e:
        print(f"✅ Rejected extreme high (2500): {e.errors()[0]['msg']}")

if __name__ == "__main__":
    test_biological_guardrails()

if __name__ == "__main__":
    test_biological_guardrails()
