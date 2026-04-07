from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple, Dict, List, Any


class LaboratorySuggestionMotor(BaseClinicalMotor):
    """
    Sugiere exámenes complementarios basados en datos disponibles y gaps clínicos.

    Estrategias:
    1. Analiza qué datosTiene el paciente (panel base)
    2. Evalúa qué motores firing y qué datos requieren
    3. Identifica gaps críticos para completar la evaluación
    4. Sugiere exámenes específicos con justificación clínica

    Evidence:
    - Choosing Wisely: Don't order lab tests without clear clinical indication.
    - American Board of Internal Medicine: Reduced unnecessary testing.

    REQUIREMENT_ID: LAB-SUGGESTION
    """

    REQUIREMENT_ID = "LAB-SUGGESTION"

    PANEL_BASE = {
        "GLUCOSE": "2339-0",
        "TOTAL_CHOLESTEROL": "2093-3",
        "HDL": "2085-9",
        "TRIGLYCERIDES": "2571-8",
        "CREATININE": "2160-0",
        "URIC_ACID": "UA-001",
    }

    PANEL_EXTENDIDO = {
        "LDL": "18262-6",
        "HBA1C": "4548-4",
        "AST": "29230-0",
        "ALT": "22538-3",
        "GGT": "GGT-001",
        "VITAMIN_D": "VITD-001",
        "TSH": "11579-0",
        "FT4": "FT4-001",
        "INSULIN": "20448-7",
        "C_PEPTIDE": "C-PEP-001",
        "PLATELETS": "PLT-001",
        "FERRITIN": "FER-001",
        "CRP": "30522-7",
    }

    MOTOR_REQUIREMENTS = {
        "MetabolicPrecisionMotor": ["GLUCOSE", "INSULIN"],
        "NFSMotor": ["AST", "ALT", "PLATELETS"],
        "FLIMotor": ["GGT", "TRIGLYCERIDES"],
        "VAIMotor": ["TRIGLYCERIDES", "HDL"],
        "TyGBMIMotor": ["GLUCOSE", "TRIGLYCERIDES"],
        "DeepMetabolicProxyMotor": [
            "GGT",
            "FER-001",
            "URIC_ACID",
            "TRIGLYCERIDES",
            "HDL",
        ],
        "VitaminDMotor": ["VITAMIN_D"],
        "EndocrinePrecisionMotor": ["TSH", "FT4"],
        "BiologicalAgeMotor": ["GLUCOSE", "CREATININE"],
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        return True, ""

    def _get_available_codes(self, encounter: Encounter) -> set:
        available = set()
        for obs in encounter.observations:
            available.add(obs.code)

        mp = encounter.metabolic_panel
        cp = encounter.cardio_panel

        if mp and mp.glucose_mg_dl:
            available.add("2339-0")
        if cp and cp.hdl_mg_dl:
            available.add("2085-9")
        if cp and cp.triglycerides_mg_dl:
            available.add("2571-8")
        if cp and cp.ldl_mg_dl:
            available.add("18262-6")
        if mp and mp.creatinine_mg_dl:
            available.add("2160-0")
        if mp and mp.uric_acid_mg_dl:
            available.add("UA-001")
        if mp and mp.hba1c_percent:
            available.add("4548-4")
        if mp and mp.alt_u_l:
            available.add("22538-3")
        if mp and mp.ast_u_l:
            available.add("29230-0")
        if mp and mp.ggt_u_l:
            available.add("GGT-001")
        if mp and mp.vitamin_d_ng_ml:
            available.add("VITD-001")
        if mp and mp.tsh_uIU_ml:
            available.add("11579-0")
        if mp and mp.hs_crp_mg_l:
            available.add("30522-7")
        if mp and mp.ferritin_ng_ml:
            available.add("FER-001")
        return available

    def _get_required_for_motor(self, motor: str) -> List[str]:
        return self.MOTOR_REQUIREMENTS.get(motor, [])

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        available = self._get_available_codes(encounter)
        all_required = set()
        for motor, reqs in self.MOTOR_REQUIREMENTS.items():
            all_required.update(reqs)

        missing_critical = []
        suggestions = []
        evidence = []

        for code in ["2339-0", "2085-9", "2571-8", "2160-0"]:
            if code not in available:
                missing_critical.append(code)

        if missing_critical:
            suggestions.append(
                {
                    "exam": "Perfil Metabólico Básico",
                    "components": [
                        "Glucosa",
                        "Colesterol Total",
                        "HDL",
                        "Triglicéridos",
                        "Creatinina",
                        "Ácido Úrico",
                    ],
                    "rationale": "Panel base requerido para evaluación cardiometabólica",
                    "priority": "high",
                    "codes": missing_critical,
                }
            )

        if "18262-6" not in available and "2085-9" in available:
            suggestions.append(
                {
                    "exam": "Perfil Lipídico Completo",
                    "components": ["LDL-c directo", "Colesterol no-HDL", "ApoB"],
                    "rationale": "LDL elevado requiere cuantificación directa para riesgo CVD",
                    "priority": "medium",
                    "codes": ["18262-6"],
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="LDL_MISSING",
                    value="Required",
                    display="LDL no disponible",
                )
            )

        if "4548-4" not in available:
            suggestions.append(
                {
                    "exam": "Hemoglobina Glicosilada (HbA1c)",
                    "components": ["HbA1c"],
                    "rationale": "Gold standard para diagnóstico y control de diabetes",
                    "priority": "medium",
                    "codes": ["4548-4"],
                }
            )

        if "GGT-001" not in available or "FER-001" not in available:
            suggestions.append(
                {
                    "exam": "Perfil Hepático y Ferritina",
                    "components": ["GGT", "ALT", "AST", "Ferritina"],
                    "rationale": "Detección de grasa hepática y estatus de hierro",
                    "priority": "low",
                    "codes": ["GGT-001", "FER-001"],
                }
            )
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="LIVER_IRON_MISSING",
                    value="Recommended",
                    display="Perfil hepático/ferritina no disponible",
                )
            )

        if "VITD-001" not in available:
            suggestions.append(
                {
                    "exam": "Vitamina D (25-OH)",
                    "components": ["25-hidroxivitamina D"],
                    "rationale": "Alta prevalencia de deficiencia en población con limited sun exposure",
                    "priority": "low",
                    "codes": ["VITD-001"],
                }
            )

        if "11579-0" not in available:
            suggestions.append(
                {
                    "exam": "Función Tiroidea",
                    "components": ["TSH"],
                    "rationale": "Screening de hipotiroidismo subclínico",
                    "priority": "low",
                    "codes": ["11579-0"],
                }
            )

        if "30522-7" not in available:
            suggestions.append(
                {
                    "exam": "Proteína C Reactiva (hs-CRP)",
                    "components": ["hs-PCR"],
                    "rationale": "Marcador de inflamación de bajo grado para riesgo cardiovascular",
                    "priority": "low",
                    "codes": ["30522-7"],
                }
            )

        action_checklist = []
        for s in suggestions:
            action_checklist.append(
                ActionItem(
                    category="diagnostic",
                    priority=s["priority"],
                    task=f"Solicitar: {s['exam']}",
                    rationale=s["rationale"],
                )
            )

        calculated = f"Sugerencias: {len(suggestions)} exámenes"
        if suggestions:
            calculated = f"Panel Sugerido: {len(suggestions)} elementos"

        explanation = "Evaluación de gaps de laboratorio basada en datos disponibles y requerimientos de motores clínicos."
        if not suggestions:
            explanation = (
                "Panel de laboratorio completo. No se requieren estudios adicionales."
            )

        return AdjudicationResult(
            calculated_value=calculated,
            confidence=0.95 if suggestions else 1.0,
            evidence=evidence,
            explanation=explanation,
            action_checklist=action_checklist,
            metadata={"suggestions": suggestions, "available_count": len(available)},
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="PROBABLE_WARNING" if suggestions else "INDETERMINATE_LOCKED",
        )
