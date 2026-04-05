import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def login():
    print("--- 🔐 Logging in as Dr. Precision ---")
    resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "doctor@integrum.ai",
        "password": "doctor123"
    })
    token = resp.json()["access_token"]
    print(f"Token acquired. Session active.")
    return token

def run_spark_test():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    test_cases = [
        {
            "id": "CASE-1: Acosta Hedonic + EOSS 2",
            "payload": {
                "patient_id": "SPARK-PAT-001",
                "conditions": [
                    {"code": "E66", "title": "Obesity", "system": "ICD-10"},
                    {"code": "E11", "title": "Diabetes Mellitus Type 2", "system": "ICD-10"},
                    {"code": "I10", "title": "Essential Hypertension", "system": "ICD-10"}
                ],
                "observations": [
                    {"code": "TFEQ-HEDONIC", "value": 18.5, "unit": "pts", "category": "psychometrics"},
                    {"code": "SMI-MUSCLE", "value": 8.2, "unit": "kg/m2", "category": "body_composition"}
                ],
                "medications": []
            }
        },
        {
            "id": "CASE-2: EOSS 3 (End-organ damage)",
            "payload": {
                "patient_id": "SPARK-PAT-002",
                "conditions": [
                    {"code": "E66", "title": "Obesity", "system": "ICD-10"},
                    {"code": "I21", "title": "Acute Myocardial Infarction", "system": "ICD-10"}
                ],
                "observations": [],
                "medications": []
            }
        },
        {
            "id": "CASE-3: Acosta Sarcopenic (Low Muscle)",
            "payload": {
                "patient_id": "SPARK-PAT-003",
                "conditions": [
                    {"code": "E66", "title": "Obesity", "system": "ICD-10"}
                ],
                "observations": [
                    {"code": "SMI-MUSCLE", "value": 6.2, "unit": "kg/m2", "category": "body_composition"},
                    {"code": "TFEQ-HEDONIC", "value": 5.0, "unit": "pts", "category": "psychometrics"}
                ],
                "medications": []
            }
        },
        {
            "id": "CASE-4: Mixed Metabolic Phenotype",
            "payload": {
                "patient_id": "SPARK-PAT-005",
                "conditions": [
                    {"code": "E66", "title": "Obesity", "system": "ICD-10"},
                    {"code": "F50.81", "title": "Binge Eating Disorder", "system": "ICD-10"}
                ],
                "observations": [
                    {"code": "TFEQ-HEDONIC", "value": 22.0, "unit": "pts", "category": "psychometrics"}
                ],
                "medications": []
            }
        }
    ]

    print(f"\n--- 🔥 Starting 'The Clinical Spark' (Inyectando {len(test_cases)} casos) ---")
    
    for case in test_cases:
        print(f"\n[Running {case['id']}]")
        try:
            start = time.time()
            resp = requests.post(f"{BASE_URL}/encounters/process", json=case["payload"], headers=headers)
            duration = time.time() - start
            
            if resp.status_code == 200:
                print(f"✅ Success ({duration:.2f}s)")
                results = resp.json()
                for motor, data in results.items():
                    print(f"   -> {motor.upper()}: {data['calculated_value']} (Conf: {data['confidence']})")
                    hash_val = data.get('integrity_hash', 'N/A')
                    print(f"   -> Integrity Hash: {hash_val[:32]}...")
            else:
                print(f"⚠️ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    run_spark_test()
