from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
)
from typing import Tuple, Dict, List, Any, Set


class LaboratorySuggestionMotor(BaseClinicalMotor):
    """
    Sugiere exámenes complementarios basados en datos disponibles, contexto clínico y gaps.

    Estrategias:
    1. Analiza qué datos tiene el paciente (panel base)
    2. Considera contexto: edad, género, condiciones, medicamentos
    3. Evalúa qué motores firing y qué datos requieren
    4. Identifica gaps críticos para completar la evaluación
    5. Sugiere exámenes específicos con justificación clínica y prioridad

    Evidence:
    - Choosing Wisely: Don't order lab tests without clear clinical indication.
    - American Board of Internal Medicine: Reduced unnecessary testing.
    - USPSTF: Screening guidelines by age and risk factors.

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

    CBC_CODES = {
        "HEMOGLOBIN": "718-7",
        "WBC": "6690-2",
        "PLATELETS": "777-3",
    }

    LIVER_CODES = {
        "ALBUMIN": "1754-0",
        "TOTAL_BILIRUBIN": "1975-2",
        "ALKALINE_PHOSPHATASE": "6768-6",
    }

    KIDNEY_CODES = {
        "BUN": "3096-1",
        "EGFR": "620-2",
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

    CONDITION_BASED_SUGGESTIONS = {
        "E11": {
            "code": "4548-4",
            "exam": "HbA1c trimestral",
            "rationale": "Diabetes: control glucémico",
        },
        "E11.9": {
            "code": "4548-4",
            "exam": "HbA1c trimestral",
            "rationale": "Diabetes: control glucémico",
        },
        "I10": {
            "code": "2093-3",
            "exam": "Perfil lipídico",
            "rationale": "Hipertensión: evaluar riesgo cardiovascular",
        },
        "I10.9": {
            "code": "2093-3",
            "exam": "Perfil lipídico",
            "rationale": "Hipertensión: evaluar riesgo cardiovascular",
        },
        "K59.0": {
            "code": "GGT-001",
            "exam": "Función hepática",
            "rationale": "Esteatosis hepática: monitoreo",
        },
        "M79.9": {
            "code": "30522-7",
            "exam": "PCR ultrasensible",
            "rationale": "Inflamación: evaluar artritis/condiciones autoinmunes",
        },
    }

    MEDICATION_MONITORING = {
        "metformin": {
            "exam": "Función renal",
            "components": ["Creatinina", "eGFR"],
            "codes": ["2160-0"],
            "rationale": "Metformina: monitoreo renal semestral",
        },
        "statin": {
            "exam": "Función hepática",
            "components": ["AST", "ALT"],
            "codes": ["29230-0", "22538-3"],
            "rationale": "Estatinas: monitoreo hepático",
        },
        "sglt2": {
            "exam": "Función renal",
            "components": ["Creatinina", "eGFR"],
            "codes": ["2160-0"],
            "rationale": "SGLT2i: monitoreo renal",
        },
        "glp1": {
            "exam": "Lipasa/Amilasa",
            "components": ["Lipasa", "Amilasa"],
            "codes": ["LIPASE-001", "AMYLASE-001"],
            "rationale": "GLP-1: monitoreo de pancreatitis",
        },
    }

    AGE_BASED_SCREENING = {
        (40, 50): {
            "exam": "Perfil lipídico",
            "codes": ["2093-3", "2085-9"],
            "rationale": "USPSTF: screening lípidos desde 40 años",
        },
        (50, 60): {
            "exam": "Colonoscopía o SOH",
            "codes": ["COLONOSCOPY"],
            "rationale": "USPSTF: screening cáncer colorrectal 45-75",
        },
        (60, 100): {
            "exam": "Densitometría ósea",
            "codes": ["DEXA"],
            "rationale": "Screening osteoporosis post-menopausia",
        },
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        return True, ""

    def _get_available_codes(self, encounter: Encounter) -> Set[str]:
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
        if mp and mp.platelets_k_u_l:
            available.add("PLT-001")
        if mp and mp.alkaline_phosphatase_u_l:
            available.add("6768-6")
        if mp and mp.albumin_g_dl:
            available.add("1754-0")
        return available

    def _has_condition(self, encounter: Encounter, icd10_pattern: str) -> bool:
        for c in encounter.conditions:
            if icd10_pattern in c.code:
                return True
        return False

    def _get_medications(self, encounter: Encounter) -> List[str]:
        meds = []
        for med in encounter.medications:
            name = med.name.lower() if med.name else ""
            for key in self.MEDICATION_MONITORING:
                if key in name:
                    meds.append(key)
        return meds

    def _get_age_group(self, age: int) -> tuple:
        for range_start, exam_info in self.AGE_BASED_SCREENING.items():
            if range_start[0] <= age < range_start[1]:
                return range_start
        return None

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        available = self._get_available_codes(encounter)
        age = encounter.demographics.age_years if encounter.demographics else None
        gender = encounter.demographics.gender if encounter.demographics else None

        suggestions = []
        evidence = []

        base_panel_missing = []
        for code in ["2339-0", "2085-9", "2571-8", "2160-0"]:
            if code not in available:
                base_panel_missing.append(code)

        if base_panel_missing:
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
                    "codes": base_panel_missing,
                }
            )

        if "18262-6" not in available and "2085-9" in available:
            suggestions.append(
                {
                    "exam": "Perfil Lipídico Completo",
                    "components": ["LDL-c directo", "Colesterol no-HDL", "ApoB"],
                    "rationale": "Evaluación precisa del riesgo cardiovascular aterogénico",
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
                    "rationale": "Detección de esteatosis hepática y estatus de hierro",
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
                    "rationale": "Alta prevalencia de deficiencia en población con limitada exposición solar",
                    "priority": "low",
                    "codes": ["VITD-001"],
                }
            )

        if "11579-0" not in available:
            suggestions.append(
                {
                    "exam": "Función Tiroidea (TSH)",
                    "components": ["TSH"],
                    "rationale": "Screening de hipotiroidismo subclínico, especialmente en mujeres",
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

        for condition_pattern, suggestion in self.CONDITION_BASED_SUGGESTIONS.items():
            if self._has_condition(encounter, condition_pattern):
                if suggestion["code"] not in available:
                    suggestions.append(
                        {
                            "exam": suggestion["exam"],
                            "components": [suggestion["exam"]],
                            "rationale": suggestion["rationale"],
                            "priority": "medium",
                            "codes": [suggestion["code"]],
                        }
                    )

        medications = self._get_medications(encounter)
        for med_key in medications:
            med_info = self.MEDICATION_MONITORING[med_key]
            missing_med_codes = [c for c in med_info["codes"] if c not in available]
            if missing_med_codes:
                suggestions.append(
                    {
                        "exam": f"Monitoreo: {med_info['exam']}",
                        "components": med_info["components"],
                        "rationale": med_info["rationale"],
                        "priority": "medium",
                        "codes": missing_med_codes,
                    }
                )

        if age and age >= 40:
            for (age_start, age_end), exam_info in self.AGE_BASED_SCREENING.items():
                if age_start <= age < age_end:
                    if age >= 45:
                        suggestions.append(
                            {
                                "exam": "Screening: " + exam_info["exam"],
                                "components": [exam_info["exam"]],
                                "rationale": exam_info["rationale"],
                                "priority": "low",
                                "codes": exam_info["codes"],
                            }
                        )
                    break

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

        calculated = f"Panel Sugerido: {len(suggestions)} elementos"
        if not suggestions:
            calculated = "Panel de laboratorio completo"

        explanation = (
            f"Análisis de {len(available)} parámetros disponibles. "
            f"Se sugieren {len(suggestions)} exámenes complementarios."
        )
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
            metadata={
                "suggestions": suggestions,
                "available_count": len(available),
                "age": age,
                "gender": gender,
            },
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="PROBABLE_WARNING" if suggestions else "INDETERMINATE_LOCKED",
        )
