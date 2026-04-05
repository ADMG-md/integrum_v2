import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.engines.domain import Encounter, Observation, Condition, MedicationStatement
from src.engines.specialty_runner import specialty_runner
from src.engines.acosta import AcostaPhenotypeMotor
from src.engines.eoss import EOSSStagingMotor
from src.services.report_service import report_service
from src.services.extraction_service import extraction_service
import json

def test_full_ignition():
    print("🔥 INICIANDO TEST DE ENCENDIDO: INTEGRUM V2 V12 ENGINE 🔥")
    print("-" * 50)

    # PASO 1: Simulación de Ingesta Inteligente (Misión 5.5)
    # Imaginamos que el médico subió un PDF y el extractor devolvió esto:
    print("[1/4] Simulando Extracción de Laboratorio (OCR/PDF)...")
    raw_extracted_findings = [
        {"code": "2339-0", "value": 112.0, "name": "Glucosa"},
        {"code": "2571-8", "value": 245.0, "name": "Trigliceridos"},
        {"code": "30522-7", "value": 4.1, "name": "PCR"}
    ]
    
    # PASO 2: Construcción del Encounter 360 (Misión 4.5)
    print("[2/4] Construyendo Encounter Multidimensional (Lifestyle + Labs)...")
    encounter = Encounter(
        id="v12-ignition-test",
        conditions=[Condition(code="E66", title="Obesity")],
        observations=[
            # Datos extraídos del PDF
            Observation(code=f['code'], value=f['value'], category="Clinical") for f in raw_extracted_findings
        ] + [
            # Datos de estilo de vida (Historia Clínica)
            Observation(code="LIFESTYLE-SLEEP-HRS", value=5.0, category="Lifestyle"),
            Observation(code="TFEQ-HEDONIC", value=22.0, category="Psychometry")
        ],
        medications=[
            MedicationStatement(code="RX-202", name="Prednisona")
        ]
    )

    # PASO 3: Ignición de Motores (Misión 3 & 4)
    print("[3/4] Ejecutando Motores Determinísticos y Capa de Precisión...")
    acosta = AcostaPhenotypeMotor()
    eoss = EOSSStagingMotor()
    
    results = {
        "AcostaPhenotypeMotor": acosta.compute(encounter),
        "EOSSStagingMotor": eoss.compute(encounter)
    }
    results.update(specialty_runner.run_all(encounter))

    # PASO 4: Generación de Narrativa y Reporte (Misión 5)
    print("[4/4] Orquestando Narrativa Clínica Final...")
    report = report_service.generate_report(results, encounter)

    print("-" * 50)
    print(f"✅ MOTOR ENCENDIDO: Report ID: {report.report_id}")
    print("\n📝 RESUMEN CLÍNICO GENERADO:")
    print(f"'{report.technical_summary}'")
    
    print("\n📊 PERFIL DE RIESGO (RADAR DATA):")
    for pillar, val in report.phenotype_radar_data.items():
        print(f"   - {pillar}: {val*100}%")

    # Verificaciones finales
    assert "desregulación metabólico-circadiana" in report.technical_summary
    assert "sabotaje farmacológico" in report.technical_summary
    print("\n🚀 CONCLUSIÓN: El Ferrari ha encendido a la primera. Sincronización perfecta entre Lab, Lifestyle y Lógica.")

if __name__ == "__main__":
    test_full_ignition()
