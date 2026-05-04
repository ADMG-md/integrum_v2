from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, ClinicalEvidence
from src.engines.base_models import AdjudicationResult, ActionItem, MedicationGap
from typing import Tuple, List, Dict, Any
import math

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class ClinicalGuidelinesMotor(BaseClinicalMotor):
    """
    Tier 3 / Layer 5 Motor: Decision support based on established clinical guidelines
    (ACC/AHA for HTN, ESC for Lipids, ADA for Diabetes).
    Detects Clinical Inertia and provides actionable next steps.
    """

    REQUIREMENT_ID = "CLINICAL-GUIDELINES"

    CODES = {
        "SBP": "8480-6",
        "DBP": "8462-4",
        "LDL": "13457-7",
        "NON_HDL": "NON-HDL",
        "GLUCOSE": "2339-0",
        "INSULIN": "20448-7",
    }

    MED_CLASSES = {
        "STATIN": [
            "ATORVASTATIN",
            "ROSUVASTATIN",
            "SIMVASTATIN",
            "PRAVASTATIN",
            "STATIN",
        ],
        "ACE_ARB": [
            "ENALAPRIL",
            "LOSARTAN",
            "VALSARTAN",
            "TELMISARTAN",
            "LISINOPRIL",
            "CAPTOPRIL",
        ],
        "GLP1": [
            "SEMAGLUTIDE",
            "LIRAGLUTIDE",
            "DULAGLUTIDE",
            "EXENATIDE",
            "OZEMPIC",
            "VICTOZA",
            "WEGOVY",
        ],
        "GIP_GLP1": ["TIRZEPATIDE", "MOUNJARO", "ZEPBOUND"],
        "TRIPLE_AGONIST": ["RETATRUTIDE"],  # Investigacional 2026
        "SGLT2": [
            "EMPAGLIFLOZIN",
            "DAPAGLIFLOZIN",
            "CANAGLIFLOZIN",
            "JARDIANCE",
            "FORXIGA",
        ],
        "BETA_BLOCKER": [
            "ATENOLOL",
            "METOPROLOL",
            "CARVEDILOL",
            "BISOPROLOL",
            "RX-303",
        ],
    }

    def _is_on_class(self, encounter: Encounter, med_class: str) -> bool:
        keywords = self.MED_CLASSES.get(med_class, [])
        for med in encounter.medications:
            if not med.is_active:
                continue
            name_upper = med.name.upper()
            if any(kw in name_upper for kw in keywords) or med.code in keywords:
                return True
        return False

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Requires basic vitals or lipids to provide guidance
        has_vitals = encounter.get_observation(self.CODES["SBP"]) is not None
        has_lipids = (
            encounter.metabolic_panel.ldl_mg_dl is not None
            or encounter.metabolic_panel.total_cholesterol_mg_dl is not None
        )
        if not (has_vitals or has_lipids):
            return False, "Insufficient vitals or lipids for guideline audit"
        return True, ""

    def compute(
        self, encounter: Encounter, context: Dict[str, Any] = None
    ) -> AdjudicationResult:
        """
        Context expects results from other motors: 'ascvd_risk', 'score2_risk', 'homa_b'.
        """
        findings = []
        action_checklist = []
        critical_omissions = []
        evidence = []

        # 1. Hypertension Audit (ACC/AHA 2017)
        sbp_obs = encounter.get_observation(self.CODES["SBP"])
        dbp_obs = encounter.get_observation(self.CODES["DBP"])
        is_on_htn_meds = self._is_on_class(encounter, "ACE_ARB") or self._is_on_class(
            encounter, "BETA_BLOCKER"
        )

        if sbp_obs and dbp_obs:
            sbp, dbp = float(sbp_obs.value), float(dbp_obs.value)
            evidence.append(
                ClinicalEvidence(
                    type="Observation", code="SBP", value=sbp, display="TAS"
                )
            )
            evidence.append(
                ClinicalEvidence(
                    type="Observation", code="DBP", value=dbp, display="TAD"
                )
            )

            if sbp >= 140 or dbp >= 90:
                findings.append(
                    f"Hipertensión {'No Controlada' if is_on_htn_meds else 'Estadio 2'}"
                )
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="high" if sbp < 180 else "critical",
                        task="Intensificar terapia antihipertensiva"
                        if is_on_htn_meds
                        else "Iniciar terapia antihipertensiva dual",
                        rationale=f"Cifras tensionales ({sbp}/{dbp}) por encima de metas ACC/AHA 2017 (>130/80).",
                    )
                )
                if not is_on_htn_meds:
                    critical_omissions.append(
                        MedicationGap(
                            drug_class="Antihipertensivos (IECA/ARA-II)",
                            gap_type="OMISSION",
                            severity="high",
                            clinical_rationale="Paciente con HTA Estadio 2 sin tratamiento activo.",
                        )
                    )

        # 2. Dyslipidemia & Clinical Inertia (ESC 2021)
        ldl = encounter.metabolic_panel.ldl_mg_dl
        is_on_statin = self._is_on_class(encounter, "STATIN")
        cvd_risk = context.get("cvd_risk_category") if context else None

        if ldl and cvd_risk:
            evidence.append(
                ClinicalEvidence(
                    type="Observation", code="LDL", value=ldl, display="LDL-C"
                )
            )

            goal = 116  # Default low risk
            if cvd_risk == "high":
                goal = 70
            elif cvd_risk == "very_high":
                goal = 55
            elif cvd_risk == "intermediate":
                goal = 100

            if ldl > goal:
                findings.append(f"Inercia Clínica en Lípidos (LDL {ldl} > Meta {goal})")
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="medium",
                        task="Ajustar estatinas de alta potencia"
                        if is_on_statin
                        else "Iniciar estatinas de alta potencia",
                        rationale=f"LDL ({ldl}) excede meta de riesgo {cvd_risk} (<{goal} mg/dL) según ESC 2021.",
                    )
                )
                if not is_on_statin:
                    critical_omissions.append(
                        MedicationGap(
                            drug_class="Estatinas",
                            gap_type="OMISSION",
                            severity="medium",
                            clinical_rationale=f"Riesgo {cvd_risk} con LDL {ldl} mg/dL sin protección farmacológica.",
                        )
                    )

        # 3. Beta-Cell Protection (HOMA-B)
        homa_b = encounter.homa_b
        is_on_glp1 = self._is_on_class(encounter, "GLP1")
        if homa_b and homa_b < 50:
            findings.append("Reserva Pancreática Comprometida (HOMA-B < 50%)")
            action_checklist.append(
                ActionItem(
                    category="pharmacological",
                    priority="medium",
                    task="Priorizar análogos GLP-1"
                    if not is_on_glp1
                    else "Ajustar dosis de GLP-1 para protección beta",
                    rationale="HOMA-B < 50% sugiere falla de célula beta; los GLP-1RA han demostrado preservación de masa beta.",
                )
            )
            if not is_on_glp1:
                critical_omissions.append(
                    MedicationGap(
                        drug_class="Análogos GLP-1",
                        gap_type="OMISSION",
                        severity="medium",
                        clinical_rationale="Falla incipiente de célula beta detectada; requiere terapia de preservación.",
                    )
                )

        # 4. Cardio-Metabolic Protection (SELECT Trial 2023/2024 - Non-Diabetic Obesity)
        is_obese = encounter.bmi and encounter.bmi >= 27
        glucose_obs = encounter.get_observation(self.CODES["GLUCOSE"])
        glucose_val = float(glucose_obs.value) if glucose_obs else None
        hba1c_val = encounter.hba1c
        is_non_diabetic = (glucose_val is not None and glucose_val < 126) or (
            hba1c_val is not None and hba1c_val < 6.5
        )
        is_on_glp1 = self._is_on_class(encounter, "GLP1")

        if (
            is_obese
            and is_non_diabetic
            and cvd_risk in ["high", "very_high", "intermediate"]
        ):
            if not is_on_glp1:
                findings.append("Déficit de Protección Cardiovascular (SELECT Trial)")
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="high",
                        task="Priorizar dosis cardio-protectoras de GLP-1RA (Semaglutida 2.4mg)",
                        rationale="En pacientes con IMC >= 27 y ECV establecida sin diabetes, la Semaglutida reduce MACE en un 20% (SELECT Trial 2023).",
                    )
                )
                critical_omissions.append(
                    MedicationGap(
                        drug_class="Análogos GLP-1 (Cardio-protección)",
                        gap_type="OMISSION",
                        severity="high",
                        clinical_rationale="Inercia en protección cardiovascular para obesidad no diabética de alto riesgo.",
                    )
                )

        # 5. Precision Incretin Choice (Obesity Staging 2026)
        is_on_any_incretin = is_on_glp1 or self._is_on_class(encounter, "GIP_GLP1")
        has_osa = encounter.has_condition("G47.3") or (
            encounter.get_observation("AIS-001")
            and float(encounter.get_observation("AIS-001").value) >= 8
        )

        if is_obese and not is_on_any_incretin:
            if has_osa:
                findings.append("Indicación Primaria de Tirzepatida (AOS + Obesidad)")
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="high",
                        task="Priorizar Tirzepatida (GIP/GLP-1RA) sobre Semaglutida",
                        rationale="En pacientes con AOS (Apnea Obstructiva del Sueño), la Tirzepatida ha demostrado reducciones significativas del IAH y peso superior (SURMOUNT-OSA 2024).",
                    )
                )
            elif encounter.bmi >= 35:
                findings.append("Elección de Alta Potencia: Tirzepatida")
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="high",
                        task="Iniciar terapia con GIP/GLP-1RA (Tirzepatida)",
                        rationale="Para reducciones >20%, la Tirzepatida es el estándar clínico en 2026 frente a análogos GLP-1 únicos.",
                    )
                )
            elif is_non_diabetic:
                findings.append("Sugerencia: Semaglutida / Liraglutida")
                action_checklist.append(
                    ActionItem(
                        category="pharmacological",
                        priority="medium",
                        task="Considerar Semaglutida para control ponderal",
                        rationale="Eficacia protectora establecida y alta disponibilidad (SELECT Trial compliant).",
                    )
                )

        # 6. Experimental Escalation (Retatrutide Eligibility Flag - Investigational)
        if encounter.bmi and encounter.bmi >= 40 and is_on_any_incretin:
            findings.append("Candidato a Tri-Agonismo (Retatrutide - Investigacional)")
            action_checklist.append(
                ActionItem(
                    category="pharmacological",
                    priority="low",
                    task="Monitorear disponibilidad de Retatrutida (Triple Agonismo)",
                    rationale="Se detecta refractariedad/severidad extrema; el tri-agonismo (GIP/GLP1/Glucagón) muestra pérdidas >28% (Trial TRIUMPH 2026).",
                )
            )

        summary = (
            " | ".join(findings)
            if findings
            else "Sin alertas de guías clínicas críticas."
        )

        return AdjudicationResult(
            calculated_value=summary,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.PROXY_MARKER],
            evidence=evidence,
            explanation="Checklist de Acción Clínica generado basado en metas internacionales.",
            estado_ui="CONFIRMED_ACTIVE"
            if any(
                "Inercia" in f or "Estadio 2" in f or "Hipertensión" in f
                for f in findings
            )
            else "PROBABLE_WARNING",
            action_checklist=action_checklist,
            critical_omissions=critical_omissions,
        )
