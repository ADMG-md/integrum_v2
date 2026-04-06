import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.engines.domain import (
    Encounter,
    Observation,
    Condition,
    MedicationStatement,
    DemographicsSchema,
    MetabolicPanelSchema,
    CardioPanelSchema,
)
from src.engines.specialty_runner import specialty_runner
from src.services.report_service import report_service


def test_full_ignition():
    print("🔥 INICIANDO TEST DE ENCENDIDO: INTEGRUM V2 V12 ENGINE 🔥")
    print("-" * 50)

    print("[1/4] Simulando Extracción de Laboratorio (OCR/PDF)...")
    print("[2/4] Construyendo Encounter Multidimensional (Lifestyle + Labs)...")

    encounter = Encounter(
        id="v12-ignition-test",
        demographics=DemographicsSchema(age_years=45, gender="male"),
        metabolic_panel=MetabolicPanelSchema(
            glucose_mg_dl=112.0,
            triglycerides_mg_dl=245.0,
            hs_crp_mg_l=4.1,
            total_cholesterol_mg_dl=215.0,
            hdl_mg_dl=44.0,
            ldl_mg_dl=138.0,
        ),
        cardio_panel=CardioPanelSchema(
            glucose_mg_dl=112.0,
            triglycerides_mg_dl=245.0,
            total_cholesterol_mg_dl=215.0,
            hdl_mg_dl=44.0,
            ldl_mg_dl=138.0,
        ),
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            Observation(
                code="LIFE-SLEEP", value=5.0, unit="hours", category="Lifestyle"
            ),
            Observation(code="TFEQ-EMOTIONAL", value=22.0, category="Psychometry"),
        ],
        medications=[MedicationStatement(code="RX-202", name="Prednisona")],
    )

    print("[3/4] Ejecutando Motores Determinísticos y Capa de Precisión...")
    results = specialty_runner.run_all(encounter)

    print("[4/4] Generando Reporte...")
    report = report_service.generate_report(
        results, encounter, encounter_id="v12-ignition-test"
    )

    print("-" * 50)
    print(f"✅ MOTOR ENCENDIDO: Encounter ID: {report['encounter_id']}")
    print(f"   Motores ejecutados: {report['results_count']}")

    assert report["encounter_id"] == "v12-ignition-test"
    assert report["results_count"] > 0
    assert "EOSSStagingMotor" in report["motors_executed"]
    assert "BiologicalAgeMotor" in report["motors_executed"]

    print(
        "\n🚀 CONCLUSIÓN: El Ferrari ha encendido a la primera. "
        "Sincronización perfecta entre Lab, Lifestyle y Lógica."
    )


if __name__ == "__main__":
    test_full_ignition()
