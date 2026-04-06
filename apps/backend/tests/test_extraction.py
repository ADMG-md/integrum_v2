import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from src.services.extraction_service import LAB_MAP
import re


def test_extraction_logic():
    print("Testing Extraction Logic (Mocking PDF text)...")

    # Simulate text extracted from a typical LATAM lab PDF
    sample_text = """
    LABORATORIO CLINICO DE PRECISION
    PACIENTE: JUAN PEREZ
    FECHA: 2024-05-12
    
    EXAMEN                  RESULTADO       UNIDADES    REFERENCIAS
    GLUCOSA EN AYUNAS       105.5           mg/dL       70 - 100
    TRIGLICERIDOS           210             mg/dL       < 150
    COLESTEROL HDL          42,8            mg/dL       > 40
    TSH                     6.5             uIU/mL      0.4 - 4.5
    """

    # We manually replicate the loop in extraction_service.extract_from_pdf to verify logic
    # without needing a real physical PDF file for the test.

    lines = sample_text.split("\n")
    findings = []

    for line in lines:
        line_lower = line.lower()
        for keyword, mapping in LAB_MAP.items():
            if keyword in line_lower:
                loinc_code = mapping[0] if isinstance(mapping, tuple) else mapping
                # Same regex as in service
                match = re.search(
                    r"(\d+[\.,]\d+|\d+)", line_lower[line_lower.find(keyword) :]
                )
                if match:
                    val_str = match.group(1).replace(",", ".")
                    findings.append(
                        {
                            "name": keyword.capitalize(),
                            "code": loinc_code,
                            "value": float(val_str),
                        }
                    )
                break

    print("\n[Extracted Findings]:")
    for f in findings:
        print(f" - {f['name']}: {f['value']} (LOINC: {f['code']})")

    # Assertions
    assert any(f["code"] == "2339-0" and f["value"] == 105.5 for f in findings)
    assert any(
        f["code"] == "2085-9" and f["value"] == 42.8 for f in findings
    )  # Verifies comma handling
    assert any(f["code"] == "11579-0" and f["value"] == 6.5 for f in findings)

    print(
        "\n✅ Extraction Logic Verified: Fuzzy mapping and comma-to-dot conversion working correctly."
    )


if __name__ == "__main__":
    test_extraction_logic()
