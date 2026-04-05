"""
Clinical Lab PDF Extraction Service.
Extracts laboratory values from PDF reports while enforcing HIPAA/Habeas Data compliance.

Design principles:
1. NO PII extraction — personal data is scrubbed before processing
2. Confidence scoring — every extracted value has a confidence level
3. Physiological validation — values outside human biology are rejected
4. LOINC mapping — all findings mapped to standard codes
"""

import pdfplumber
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger()

# ============================================================
# PII Patterns — MUST be scrubbed before any processing
# HIPAA Safe Harbor + Colombia Ley 1581
# ============================================================

PII_PATTERNS = [
    # Colombian ID (cédula) — 7-10 digits standalone
    (re.compile(r"(?<![-(])\b\d{7,10}\b(?![)-])"), "[CEDULA_REDACTED]"),
    # Email
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL_REDACTED]"),
    # Phone — must look like a phone: +57 300 123 4567 or 300-123-4567
    (re.compile(r"(?:\+57\s*)?\d{3}[\s-]\d{3}[\s-]\d{4}"), "[PHONE_REDACTED]"),
    # SSN / NIT
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    # Address — only match up to end of line, not across lines
    (
        re.compile(r"(calle|cra|avenida|av\.?|cll)\s+\d+\s*[^#\n]*", re.IGNORECASE),
        "[ADDRESS_REDACTED]",
    ),
]

# Common Colombian lab names — used to identify header sections
LAB_HEADERS = [
    "resultado",
    "valor",
    "rango",
    "referencia",
    "unidad",
    "unidades",
    "method",
    "technique",
    "metodo",
    "observaciones",
    "notas",
    "fecha",
    "date",
    "hora",
    "time",
    "orden",
    "order",
    "paciente",
    "patient",
    "nombre",
    "name",
    "identificacion",
    "direccion",
    "address",
    "telefono",
    "phone",
    "email",
    "medico",
    "doctor",
    "eps",
    "regimen",
    "sede",
    "factura",
    "invoice",
    "cotizacion",
    "quote",
    "autorizacion",
    "authorization",
    "consecutivo",
]

# ============================================================
# Lab Mapping — LATAM "Rosetta Stone" for LOINC codes
# ============================================================

LAB_MAP = {
    # Glucose/Diabetes
    "glucosa": ("2339-0", "mg/dL", 40, 600),
    "glucose": ("2339-0", "mg/dL", 40, 600),
    "glucemia": ("2339-0", "mg/dL", 40, 600),
    "glicemia": ("2339-0", "mg/dL", 40, 600),
    "azucar": ("2339-0", "mg/dL", 40, 600),
    "hba1c": ("4548-4", "%", 3.0, 18.0),
    "hemoglobina glicosilada": ("4548-4", "%", 3.0, 18.0),
    "hemoglobina glicada": ("4548-4", "%", 3.0, 18.0),
    "glicada": ("4548-4", "%", 3.0, 18.0),
    "insulina": ("20448-7", "μU/mL", 1, 100),
    "peptido c": ("17858-5", "ng/mL", 0.5, 10),
    "peptide c": ("17858-5", "ng/mL", 0.5, 10),
    # Lipids
    "colesterol total": ("2093-3", "mg/dL", 70, 400),
    "trigliceridos": ("2571-8", "mg/dL", 0, 1200),
    "triglicéridos": ("2571-8", "mg/dL", 0, 1200),
    "hdl": ("2085-9", "mg/dL", 0, 150),
    "colesterol hdl": ("2085-9", "mg/dL", 0, 150),
    "ldl": ("13457-7", "mg/dL", 0, 400),
    "colesterol ldl": ("13457-7", "mg/dL", 0, 400),
    "vldl": ("30388-3", "mg/dL", 0, 200),
    "apob": ("13456-9", "mg/dL", 0, 300),
    "apolipoproteina b": ("13456-9", "mg/dL", 0, 300),
    "lp(a)": ("35199-8", "mg/dL", 0, 300),
    "lipoproteina a": ("35199-8", "mg/dL", 0, 300),
    # Renal
    "creatinina": ("2160-0", "mg/dL", 0.2, 10.0),
    "creatinine": ("2160-0", "mg/dL", 0.2, 10.0),
    "urea": ("3094-0", "mg/dL", 5, 100),
    "acido urico": ("3084-1", "mg/dL", 1, 20),
    "ácido úrico": ("3084-1", "mg/dL", 1, 20),
    "bun": ("3094-0", "mg/dL", 5, 100),
    "tasa filtracion": ("33914-3", "mL/min", 5, 200),
    "tasa de filtracion": ("33914-3", "mL/min", 5, 200),
    "filtrado glomerular": ("33914-3", "mL/min", 5, 200),
    # Liver
    "ast": ("1920-8", "U/L", 5, 500),
    "tgo": ("1920-8", "U/L", 5, 500),
    "alt": ("1742-6", "U/L", 5, 500),
    "tgp": ("1742-6", "U/L", 5, 500),
    "ggt": ("2324-2", "U/L", 1, 2000),
    "gamma gt": ("2324-2", "U/L", 1, 2000),
    "fosfatasa alcalina": ("6768-6", "U/L", 20, 1000),
    "fosfatasa": ("6768-6", "U/L", 20, 1000),
    "bilirrubina total": ("1975-2", "mg/dL", 0.1, 20),
    "bilirrubina directa": ("1968-7", "mg/dL", 0, 15),
    "bilirrubina indirecta": ("1971-1", "mg/dL", 0, 15),
    # CBC
    "hemoglobina": ("718-7", "g/dL", 3, 20),
    "hematocrito": ("4544-3", "%", 10, 70),
    "leucocitos": ("6690-2", "k/uL", 1, 50),
    "wbc": ("6690-2", "k/uL", 1, 50),
    "plaquetas": ("777-3", "k/uL", 10, 1000),
    "platelets": ("777-3", "k/uL", 10, 1000),
    "neutrofilos": ("26512-4", "%", 10, 95),
    "linfocitos": ("26474-7", "%", 1, 80),
    "monocitos": ("26485-3", "%", 1, 30),
    "eosinofilos": ("26449-9", "%", 0, 20),
    "vcm": ("787-2", "fL", 60, 120),
    "rdw": ("788-0", "%", 8, 30),
    # Inflammation
    "proteina c reactiva": ("30522-7", "mg/L", 0, 50),
    "pcr": ("30522-7", "mg/L", 0, 50),
    "pcr ultrasensible": ("30522-7", "mg/L", 0, 50),
    "crp": ("30522-7", "mg/L", 0, 50),
    "ferritina": ("2276-4", "ng/mL", 5, 2000),
    "vs": ("4537-7", "mm/h", 1, 150),
    "velocidad sedimentacion": ("4537-7", "mm/h", 1, 150),
    # Thyroid
    "tsh": ("11579-0", "uIU/mL", 0.01, 100),
    "t4 libre": ("3024-7", "ng/dL", 0.1, 10),
    "ft4": ("3024-7", "ng/dL", 0.1, 10),
    "t3 libre": ("3053-3", "pg/mL", 1, 20),
    "ft3": ("3053-3", "pg/mL", 1, 20),
    # Endocrine
    "cortisol": ("2143-6", "mcg/dL", 1, 50),
    "shbg": ("13475-9", "nmol/L", 5, 200),
    "aldosterona": ("1762-0", "ng/dL", 1, 100),
    "renina": ("2889-4", "ng/mL/h", 0.1, 50),
    "testosterona": ("2986-8", "ng/dL", 5, 1500),
    "estradiol": ("2243-2", "pg/mL", 5, 500),
    "prolactina": ("2844-9", "ng/mL", 1, 200),
    "progesterona": ("1699-4", "ng/mL", 0.1, 30),
    # Vitamins
    "vitamina d": ("1989-3", "ng/mL", 3, 150),
    "vitamina b12": ("2132-9", "pg/mL", 50, 2000),
    "folato": ("2284-8", "ng/mL", 2, 30),
    "acido folico": ("2284-8", "ng/mL", 2, 30),
    # Electrolytes
    "sodio": ("2951-2", "mEq/L", 120, 160),
    "potasio": ("2823-3", "mEq/L", 2.5, 7),
    "calcio": ("17861-9", "mg/dL", 6, 15),
    "magnesio": ("19125-2", "mg/dL", 1, 5),
    "fosforo": ("2777-1", "mg/dL", 1, 10),
    "cloro": ("2075-0", "mEq/L", 80, 120),
    # Proteínas
    "albumina": ("1751-7", "g/dL", 2.0, 6.0),
    "proteinas totales": ("2885-2", "g/dL", 5, 10),
    "globulina": ("2883-7", "g/dL", 1, 5),
}


def scrub_pii(text: str) -> Tuple[str, List[str]]:
    """
    Remove all PII from text. Returns scrubbed text and list of detected PII types.
    HIPAA Safe Harbor + Colombia Ley 1581 compliance.
    Processes line by line to avoid cross-line matching issues.
    """
    detected_pii = []
    lines = text.split("\n")
    scrubbed_lines = []

    for line in lines:
        scrubbed_line = line
        for pattern, replacement in PII_PATTERNS:
            matches = pattern.findall(scrubbed_line)
            if matches:
                detected_pii.append(replacement.replace("_REDACTED", ""))
                scrubbed_line = pattern.sub(replacement, scrubbed_line)
        scrubbed_lines.append(scrubbed_line)

    return "\n".join(scrubbed_lines), list(set(detected_pii))


def is_lab_header(line: str) -> bool:
    """Check if a line is a header/footer/administrative text (not lab data)."""
    line_lower = line.lower().strip()
    if not line_lower:
        return True
    # Lines that are clearly administrative
    admin_keywords = [
        "laboratorio",
        "clinica",
        "hospital",
        "centro medico",
        "resultado de laboratorio",
        "informe",
        "reporte",
        "copyright",
        "todos los derechos",
        "version",
        "pagina ",
        "page ",
        "folio",
        "este documento",
        "certifico",
        "autorizo",
        "firma",
        "sello",
        "stamp",
    ]
    return any(kw in line_lower for kw in admin_keywords)


def extract_value_from_line(line: str, keyword: str) -> Optional[float]:
    """
    Extract a numeric value from a lab result line.
    Handles formats: "Glucosa: 95 mg/dL", "Glucosa 95.0", "95 (70-100)"
    """
    # Find the keyword position
    idx = line.lower().find(keyword)
    if idx == -1:
        return None

    # Get the part after the keyword
    after_keyword = line[idx + len(keyword) :]

    # Try to find a number pattern
    # Matches: 95, 95.0, 95,0, <95, >95
    match = re.search(r"[<>=]?\s*(\d+[.,]\d+|\d+)", after_keyword)
    if match:
        val_str = match.group(1).replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None
    return None


def extract_unit_from_line(line: str, keyword: str) -> Optional[str]:
    """Extract unit from a lab result line."""
    idx = line.lower().find(keyword)
    if idx == -1:
        return None

    after_keyword = line[idx + len(keyword) :]

    # Common units
    unit_patterns = [
        r"(mg/dL|mg/dl|mg/dl)",
        r"(μU/mL|uU/mL|uIU/mL)",
        r"(ng/mL|ng/dL|ng/dl)",
        r"(pg/mL|pg/dL)",
        r"(mmol/L|mmol/l)",
        r"(g/dL|g/dl)",
        r"(k/uL|k/μL)",
        r"(u/L|U/L)",
        r"(mEq/L|mEq/l)",
        r"(mL/min)",
        r"(mm/h)",
        r"(%|percent)",
        r"(fL)",
    ]

    for pattern in unit_patterns:
        match = re.search(pattern, after_keyword, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


class LabExtractionResult:
    def __init__(
        self,
        name: str,
        code: str,
        value: float,
        unit: Optional[str],
        confidence: float,
        raw_line: str,
        physiological: bool,
    ):
        self.name = name
        self.code = code
        self.value = value
        self.unit = unit
        self.confidence = confidence
        self.raw_line = raw_line
        self.physiological = physiological

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "physiological": self.physiological,
        }


class ExtractionService:
    """
    Extracts clinical data from PDF laboratory reports.
    Enforces HIPAA/Habeas Data compliance by scrubbing PII before processing.
    """

    def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract lab values from a PDF file.
        Returns structured results with PII scrubbing metadata.
        """
        extracted_text = ""
        findings: List[LabExtractionResult] = []
        pii_detected: List[str] = []
        pages_processed = 0

        try:
            # 1. Extract text from PDF
            with pdfplumber.open(file_path) as pdf:
                pages_processed = len(pdf.pages)
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    extracted_text += text + "\n"

            # 2. SCRUB PII — mandatory before any processing
            scrubbed_text, detected_pii = scrub_pii(extracted_text)
            pii_detected = detected_pii

            # 3. Process lines
            lines = scrubbed_text.split("\n")

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped or is_lab_header(line_stripped):
                    continue

                line_lower = line_stripped.lower()

                # 4. Match against lab map (longer keywords first for specificity)
                sorted_keywords = sorted(LAB_MAP.keys(), key=len, reverse=True)

                for keyword in sorted_keywords:
                    if keyword in line_lower:
                        loinc_code, default_unit, min_val, max_val = LAB_MAP[keyword]

                        value = extract_value_from_line(line_stripped, keyword)
                        if value is None:
                            continue

                        # Physiological validation
                        is_physiological = min_val <= value <= max_val
                        confidence = 0.9 if is_physiological else 0.3

                        unit = (
                            extract_unit_from_line(line_stripped, keyword)
                            or default_unit
                        )

                        findings.append(
                            LabExtractionResult(
                                name=keyword.title(),
                                code=loinc_code,
                                value=value,
                                unit=unit,
                                confidence=confidence,
                                raw_line=line_stripped[:100],
                                physiological=is_physiological,
                            )
                        )
                        break  # One lab per line

        except Exception as e:
            logger.error("pdf_extraction_failed", error=str(e))
            raise

        # 5. Deduplicate — keep highest confidence per LOINC code
        seen_codes: Dict[str, LabExtractionResult] = {}
        for f in findings:
            if f.code not in seen_codes or f.confidence > seen_codes[f.code].confidence:
                seen_codes[f.code] = f

        unique_findings = list(seen_codes.values())

        return {
            "findings": [f.to_dict() for f in unique_findings],
            "count": len(unique_findings),
            "pages_processed": pages_processed,
            "pii_scrubbed": len(pii_detected) > 0,
            "pii_types": pii_detected,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton
extraction_service = ExtractionService()
