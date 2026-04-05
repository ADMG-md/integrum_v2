import requests
import time
import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
def test_partial_data_stability():
    print("🔬 Iniciando Prueba de Resiliencia (Data Parcial)...")

    # 1. Login
    login_data = {"username": "admin@integrum.com", "password": "Integrum2024*"}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Minimal Patient
    patient_ext_id = f"res-test-{int(time.time())}"
    patient_payload = {
        "external_id": patient_ext_id,
        "full_name": "Resilience Test Patient",
        "date_of_birth": "1990-01-01",
        "gender": "Female",
        "email": f"{patient_ext_id}@test.com",
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/patients/", json=patient_payload, headers=headers
    )
    patient = resp.json()
    patient_uuid = patient["id"]
    print(f"✅ Paciente Creado: {patient_uuid}")

    # 3. Handle Legal Consent (Correct Endpoint)
    consent_payload = {
        "patient_id": patient_uuid,
        "consent_type": "Informed Consent v1",
        "is_granted": True,
        "terms_version": "1.0",
    }
    requests.post(f"{BASE_URL}/api/v1/consent/", json=consent_payload, headers=headers)
    print("✅ Consentimiento Registrado.")

    # 4. Execute Analysis with PARTIAL DATA (Only Weight and Height)
    process_payload = {
        "patient_id": patient_uuid,
        "observations": [
            {"code": "29463-7", "value": "85.0", "unit": "kg"},  # Weight
            {"code": "8302-2", "value": "170.0", "unit": "cm"},  # Height
        ],
        "conditions": [],
        "medications": [],
        "reason_for_visit": "Prueba de Degradación con Gracia",
    }

    print("📡 Enviando análisis parcial (Peso/Talla)...")
    start_time = time.time()
    resp = requests.post(
        f"{BASE_URL}/api/v1/encounters/process?generate_report=true",
        json=process_payload,
        headers=headers,
    )

    if resp.status_code == 200:
        print(f"✅ ÉXITO: El sistema analizó en {round(time.time() - start_time, 2)}s.")
        data = resp.json()
        # In T0 process, if generate_report=true, data is the ClinicalReportSchema
        report = data
        adjudications = report.get("engine_adjudications", {})
        print(f"📋 Motores Ejecutados: {list(adjudications.keys())}")

        # Verify specific calculations that should work with partial data
        if "acosta" in report:
            print(f"🏁 Acosta Phenotype: {report['acosta']['calculated_value']}")
        if "kleiber" in report:
            print(f"🔥 Kleiber BMR: {report['kleiber']['calculated_value']}")

        print("\n🏆 Misión Cumplida: El sistema es resiliente a la data incompleta.")
    else:
        print(f"❌ FALLO: Código {resp.status_code}")
        print(resp.text)
        exit(1)


if __name__ == "__main__":
    test_partial_data_stability()
