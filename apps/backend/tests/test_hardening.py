import requests
import json
import uuid
import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
def test_hardened_lifecycle():
    print("🚀 Iniciando Verificación de 'Digital Plomería' (SaMD Bedrock)...")

    # 1. Login (Obtener Token) con el admin reseteado
    email = "admin@integrum.ai"
    password = "admin-password"
    login_data = {"username": email, "password": password}
    login_resp = requests.post(f"{BASE_URL}/api/v1/auth/login/", data=login_data)
    if login_resp.status_code != 200:
        print(f"❌ Error de Login: {login_resp.text}")
        return
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Autenticación exitosa.")

    # 2. Registrar Paciente
    external_id = f"TEST-{uuid.uuid4().hex[:6]}"
    patient_data = {
        "external_id": external_id,
        "full_name": "Paciente de Prueba Hardening",
        "date_of_birth": "1985-06-15",
        "gender": "male",
        "email": f"test_{external_id}@example.com",
        "phone": "555-1234",
    }
    patient_resp = requests.post(
        f"{BASE_URL}/api/v1/patients/", json=patient_data, headers=headers
    )
    if patient_resp.status_code != 200:
        print(f"❌ Error al crear paciente: {patient_resp.text}")
        return
    patient_id = patient_resp.json()["id"]
    print(f"✅ Paciente registrado: {patient_id}")

    # 3. Registrar Consentimiento Legal (Guardrail SaMD)
    consent_data = {
        "patient_id": patient_id,
        "consent_type": "SAMD_ANALYSIS_V1",
        "is_granted": True,
        "terms_version": "2026.03.14-ES",
    }
    consent_resp = requests.post(
        f"{BASE_URL}/api/v1/consent/", json=consent_data, headers=headers
    )
    if consent_resp.status_code != 200:
        print(f"❌ Error al registrar consentimiento: {consent_resp.text}")
        return
    print("✅ Consentimiento legal registrado.")

    # 4. Crear Encuentro con Datos Clínicos (8 Columnas)
    encounter_data = {
        "patient_id": patient_id,
        "reason_for_visit": "Prueba de integridad de base de datos y contratos.",
        "personal_history": "Antecedente de hipertensión controlada.",
        "family_history": "Padre con diabetes tipo 2.",
        "observations": [
            {"code": "29463-7", "value": "95.5", "unit": "kg"},  # Peso
            {"code": "8302-2", "value": "178", "unit": "cm"},  # Talla
            {"code": "2339-0", "value": "110", "unit": "mg/dL"},  # Glucosa
        ],
        "biometrics": {"weight_kg": 95.5, "height_cm": 178},
        "conditions": [{"code": "E66.9", "title": "Obesidad"}],
    }

    process_resp = requests.post(
        f"{BASE_URL}/api/v1/encounters/process?generate_report=true",
        json=encounter_data,
        headers=headers,
    )
    if process_resp.status_code != 200:
        print(f"❌ Error al procesar encuentro: {process_resp.text}")
        return

    report_data = process_resp.json()
    encounter_id = report_data["report_id"]
    print(f"✅ Encuentro analizado por motores Acosta/EOSS: {encounter_id}")

    # 4. Finalizar Consulta (Persistencia de Notas y Plan)
    finalize_data = {
        "clinical_notes": "El paciente presenta riesgo metabólico moderado. Se observan 8/8 columnas sincronizadas.",
        "plan_of_action": {
            "dieta": "Hipocalórica avanzada",
            "ejercicio": "150 min/semana caminata",
            "seguimiento": "3 meses",
        },
    }
    finalize_resp = requests.patch(
        f"{BASE_URL}/api/v1/encounters/{encounter_id}/finalize",
        json=finalize_data,
        headers=headers,
    )
    if finalize_resp.status_code != 200:
        print(f"❌ Error al finalizar consulta: {finalize_resp.text}")
        return
    print("✅ Consulta finalizada y bloqueada.")

    # 5. Verificación de Integridad en BD (Data Contract Proof)
    read_resp = requests.get(
        f"{BASE_URL}/api/v1/encounters/patient/{patient_id}", headers=headers
    )
    encounters = read_resp.json()
    latest = encounters[0]

    # Check key columns
    checks = {
        "Reason for Visit": latest.get("reason_for_visit")
        == encounter_data["reason_for_visit"],
        "Clinical Notes": latest.get("clinical_notes")
        == finalize_data["clinical_notes"],
        "Plan of Action": latest.get("plan_of_action")
        == finalize_data["plan_of_action"],
        "Status": latest.get("status") == "FINALIZED",
    }

    for key, passed in checks.items():
        search_key = key.lower().replace(" ", "_")
        if passed:
            print(f"✅ VERIFICACIÓN DE INTEGRIDAD: {key} [OK]")
        else:
            print(f"❌ VERIFICACIÓN DE INTEGRIDAD: {key} [FALLÓ]")
            # Try to get from encounter_data or finalize_data
            expected = encounter_data.get(search_key) or finalize_data.get(search_key)
            print(f"   Esperado: {expected}")
            print(f"   Obtenido: {latest.get(search_key)}")

    if all(checks.values()):
        print(
            "\n🏆 VEREDICTO DE ARQUITECTO: El 'Boring MVP' tiene cimientos de Roca Firme. Proceso Completado."
        )
    else:
        print("\n⚠️ FALLO EN INTEGRIDAD: Revisar mapeo de parámetros.")


if __name__ == "__main__":
    test_hardened_lifecycle()
