"""
ClinicalDataReadinessEngine — Orchestration Infrastructure
==========================================================
REQUIREMENT_ID: DATA-READINESS-V1

Does NOT execute clinical logic. Runs motor.validate(encounter) on all
registered motors WITHOUT compute() to produce a data readiness map.

This is orchestration infrastructure, NOT a clinical motor:
- Does NOT go in PRIMARY_MOTORS
- Does NOT produce AdjudicationResult
- Does NOT have clinical hazards
- Lives alongside SpecialtyRunner, not inside it

Designed for Colombian EPS context where patients typically arrive
with 4-12 data points. The clinician sees which motors are evaluable
and which labs unlock additional clinical value.
"""

from dataclasses import dataclass, field
from typing import Optional
import structlog

logger = structlog.get_logger()


LAB_CODE_MAP = {
    "glucose": "GLUC-001",
    "triglycerides": "TRIG-001",
    "hdl": "HDL-001",
    "ldl": "LDL-001",
    "total_cholesterol": "TC-001",
    "hba1c": "HBA1C-001",
    "creatinine": "CREA-001",
    "egfr": "EGFR-001",
    "alt": "TGO-001",
    "ast": "TGP-001",
    "ggt": "GGT-001",
    "tsh": "TSH-001",
    "ft4": "FT4-001",
    "waist": "WAIST-001",
    "hip": "HIP-001",
    "weight": "WEIGHT-001",
    "height": "HEIGHT-001",
    "sbp": "SBP-001",
    "dbp": "DBP-001",
    "albumin": "ALB-001",
    "bun": "BUN-001",
    "sodium": "NA-001",
    "potassium": "K-001",
    "hemoglobin": "HGB-001",
    "uric_acid": "UA-001",
    "fasting": "FASTING-001",
    "apob": "APOB-001",
    "apoa1": "APOA1-001",
    "vitamin_d": "VITD-001",
    "shbg": "SHBG-001",
    "testosterone": "TEST-001",
    "uacr": "UACR-001",
    "lipase": "LIPASE-001",
    "crp": "CRP-001",
    "crp_hs": "CRP-HS-001",
    "homa_ir": "HOMA-IR-001",
    "metabolic_syndrome": "MET-SYN-001",
    "ace_score": "ACE-001",
    "phq9": "PHQ9-001",
    "phq9_item9": "PHQ9-I9-001",
    "stop_bang": "STOPBANG-001",
    "grip_right": "GRIP-R-001",
    "grip_left": "GRIP-L-001",
    "gait_speed": "GAIT-001",
    "smoking": "SMOKE-001",
    "age": "AGE-001",
    "gender": "GENDER-001",
    "conditions": "ICD10-001",
    "diabetes": "DM-001",
    "pcg": "PCG-001",
    "bmi": "BMI-001",
    "muscle_mass": "MUSCLE-001",
    "bone_mass": "BONE-001",
    "visceral_fat": "VFAT-001",
    "body_fat_percent": "BFAT-001",
    "sarcf_score": "SARCF-001",
}


MOTOR_REQUIREMENTS = {
    "AcostaPhenotypeMotor": {
        "required": [
            "weight",
            "height",
            "waist",
            "hip",
            "triglycerides",
            "hdl",
            "glucose",
        ],
        "optional": ["hba1c", "alt", "ggt", "bmi"],
    },
    "EOSSStagingMotor": {
        "required": ["conditions", "weight", "height"],
        "optional": ["glucose", "triglycerides", "hdl", "sbp", "dbp", "crp_hs"],
    },
    "SarcopeniaMotor": {
        "required": ["weight", "height", "muscle_mass"],
        "optional": ["grip_right", "gait_speed"],
    },
    "BiologicalAgeMotor": {
        "required": ["glucose", "hdl", "alt"],
        "optional": [
            "hba1c",
            "triglycerides",
            "creatinine",
            "albumin",
            "hgb",
            "uric_acid",
        ],
    },
    "MetabolicPrecisionMotor": {
        "required": ["glucose", "triglycerides", "hdl", "waist", "height"],
        "optional": ["hba1c", "ldl", "fasting"],
    },
    "DeepMetabolicProxyMotor": {
        "required": ["glucose", "triglycerides"],
        "optional": ["hdl", "hba1c"],
    },
    "Lifestyle360Motor": {
        "required": [],
        "optional": [],
    },
    "AnthropometryMotor": {
        "required": ["waist", "height"],
        "optional": ["hip", "weight", "sbp"],
    },
    "EndocrineMotor": {
        "required": ["tsh", "ft4"],
        "optional": ["glucose", "hba1c"],
    },
    "HypertensionMotor": {
        "required": ["sbp", "dbp"],
        "optional": ["creatinine", "potassium", "sodium"],
    },
    "InflammationMotor": {
        "required": ["crp_hs"],
        "optional": ["crp", "glucose"],
    },
    "SleepApneaMotor": {
        "required": ["stop_bang"],
        "optional": ["sbp", "dbp", "bmi"],
    },
    "LaboratoryStewardshipMotor": {
        "required": [],
        "optional": [],
    },
    "FunctionalSarcopeniaMotor": {
        "required": ["grip_right", "gait_speed"],
        "optional": ["weight", "height"],
    },
    "FLIMotor": {
        "required": ["triglycerides", "bmi", "alt", "ggt"],
        "optional": ["waist"],
    },
    "VAIMotor": {
        "required": ["waist", "height", "triglycerides", "hdl"],
        "optional": ["weight"],
    },
    "CMIMotor": {
        "required": ["waist", "height", "triglycerides", "hdl"],
        "optional": ["glucose", "sbp", "dbp"],
    },
    "ApoBApoA1Motor": {
        "required": ["apob", "apoa1"],
        "optional": ["ldl"],
    },
    "PulsePressureMotor": {
        "required": ["sbp", "dbp"],
        "optional": [],
    },
    "NFSMotor": {
        "required": ["age", "bmi", "alt", "ggt", "platelets"],
        "optional": ["creatinine", "albumin"],
    },
    "GLP1MonitoringMotor": {
        "required": [],
        "optional": ["lipase", "glucose", "hba1c"],
    },
    "MetforminB12Motor": {
        "required": ["hba1c"],
        "optional": ["vitamin_b12"],
    },
    "CancerScreeningMotor": {
        "required": ["age", "gender", "bmi"],
        "optional": [],
    },
    "SGLT2iBenefitMotor": {
        "required": ["egfr"],
        "optional": ["uacr", "glucose"],
    },
    "ACEScoreEngine": {
        "required": ["ace_score"],
        "optional": [],
    },
    "KFREMotor": {
        "required": ["age", "egfr", "uacr"],
        "optional": ["creatinine"],
    },
    "CharlsonMotor": {
        "required": ["conditions", "age"],
        "optional": ["creatinine", "glucose", "hgb"],
    },
    "FreeTestosteroneMotor": {
        "required": ["testosterone", "shbg"],
        "optional": ["albumin"],
    },
    "VitaminDMotor": {
        "required": ["vitamin_d"],
        "optional": ["pth"],
    },
    "FriedFrailtyMotor": {
        "required": ["weight", "grip_right", "gait_speed"],
        "optional": ["bmi", "sbp"],
    },
    "TyGBMIMotor": {
        "required": ["glucose", "triglycerides", "weight", "height"],
        "optional": ["waist"],
    },
    "CVDReclassifierMotor": {
        "required": ["ldl", "hdl"],
        "optional": ["sbp", "triglycerides"],
    },
    "WomensHealthMotor": {
        "required": ["gender"],
        "optional": ["conditions", "glucose"],
    },
    "MensHealthMotor": {
        "required": ["gender"],
        "optional": ["conditions"],
    },
    "BodyCompositionTrendMotor": {
        "required": [],
        "optional": [],
    },
    "ObesityPharmaEligibilityMotor": {
        "required": ["bmi", "weight", "height"],
        "optional": ["phq9_item9", "conditions"],
    },
    "GLP1TitrationMotor": {
        "required": [],
        "optional": [],
    },
    "DrugInteractionMotor": {
        "required": [],
        "optional": [],
    },
    "ProteinEngineMotor": {
        "required": ["egfr"],
        "optional": ["weight", "creatinine"],
    },
    "LipidRiskPrecisionMotor": {
        "required": ["ldl", "total_cholesterol", "triglycerides"],
        "optional": ["hdl", "egfr", "conditions"],
    },
}


@dataclass
class QuickWin:
    motor: str
    missing_codes: list[str]


@dataclass
class Blocked:
    motor: str
    missing_codes: list[str]


@dataclass
class LabRecommendation:
    code: str
    display_name: str
    unlocks: int


@dataclass
class DataReadinessReport:
    feasibility_score: float
    tier: str
    total_motors: int
    ready_count: int
    quickwin_count: int
    blocked_count: int
    ready_motors: list[str] = field(default_factory=list)
    quickwins: list[QuickWin] = field(default_factory=list)
    priority_labs: list[LabRecommendation] = field(default_factory=list)
    blocked_motors: list[Blocked] = field(default_factory=list)
    available_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "feasibility_score": round(self.feasibility_score, 2),
            "tier": self.tier,
            "total_motors": self.total_motors,
            "ready_count": self.ready_count,
            "quickwin_count": self.quickwin_count,
            "blocked_count": self.blocked_count,
            "ready_motors": self.ready_motors,
            "quickwins": [
                {"motor": qw.motor, "missing": qw.missing_codes}
                for qw in self.quickwins
            ],
            "priority_labs": [
                {"code": lr.code, "name": lr.display_name, "unlocks": lr.unlocks}
                for lr in self.priority_labs
            ],
            "blocked_motors": [
                {"motor": b.motor, "missing_codes": b.missing_codes}
                for b in self.blocked_motors
            ],
        }


def _to_lab_code(field: str) -> str:
    return LAB_CODE_MAP.get(field.lower(), field.upper())


class ClinicalDataReadinessEngine:
    """
    Orchestration layer that evaluates which clinical motors can run
    with available data without calling motor.compute().

    Usage:
        engine = ClinicalDataReadinessEngine()
        report = engine.score(encounter, registered_motors)
        # report.feasibility_score, report.tier, report.ready_motors, ...
    """

    def score(self, encounter, registered_motors: dict) -> DataReadinessReport:
        """
        Evaluate data readiness for all registered motors.

        Args:
            encounter: Encounter domain object
            registered_motors: dict of motor_name -> motor_class (from SpecialtyRunner)

        Returns:
            DataReadinessReport with categorized motors and lab recommendations
        """
        available_codes = self._get_available_codes(encounter)
        ready_motors = []
        quickwins = []
        blocked = []
        motor_validators = {}

        for name, motor_cls in registered_motors.items():
            try:
                motor = motor_cls()
                is_valid, reason = motor.validate(encounter)
                motor_validators[name] = (is_valid, reason)
            except Exception as e:
                logger.warning(
                    "readiness_validate_error", motor=name, error_type=type(e).__name__
                )
                motor_validators[name] = (False, f"Validation error: {str(e)}")

        for name, (is_valid, reason) in motor_validators.items():
            if is_valid:
                ready_motors.append(name)
                continue

            required_fields = MOTOR_REQUIREMENTS.get(name, {}).get("required", [])
            missing = []
            for field in required_fields:
                if not self._field_available(field, available_codes):
                    missing.append(_to_lab_code(field))

            if len(missing) == 0:
                missing = ["dato_requerido"]

            if len(missing) <= 1:
                quickwins.append(QuickWin(motor=name, missing_codes=missing))
            else:
                blocked.append(Blocked(motor=name, missing_codes=missing))

        priority_labs = self._rank_labs(quickwins)
        feasibility = (
            len(ready_motors) / len(registered_motors) if registered_motors else 0.0
        )
        tier = self._classify_tier(feasibility, len(ready_motors))

        return DataReadinessReport(
            feasibility_score=feasibility,
            tier=tier,
            total_motors=len(registered_motors),
            ready_count=len(ready_motors),
            quickwin_count=len(quickwins),
            blocked_count=len(blocked),
            ready_motors=ready_motors,
            quickwins=quickwins,
            priority_labs=priority_labs,
            blocked_motors=blocked,
            available_codes=available_codes,
        )

    def _get_available_codes(self, encounter) -> set:
        codes = set()
        mp = getattr(encounter, "metabolic_panel", None)
        cp = getattr(encounter, "cardio_panel", None)
        bm = getattr(encounter, "biometrics", None)

        if mp:
            for field in [
                "glucose_mg_dl",
                "triglycerides_mg_dl",
                "hdl_mg_dl",
                "ldl_mg_dl",
                "total_cholesterol_mg_dl",
                "hba1c",
                "creatinine_mg_dl",
                "alt_u_l",
                "ast_u_l",
                "ggt_u_l",
                "tsh_mi_u_l",
                "ft4_ng_dl",
            ]:
                val = getattr(mp, field, None)
                if val is not None:
                    codes.add(
                        field.replace("_mg_dl", "")
                        .replace("_u_l", "")
                        .replace("_mi_u_l", "")
                        .replace("_ng_dl", "")
                    )

        if cp:
            for field in [
                "glucose_mg_dl",
                "triglycerides_mg_dl",
                "hdl_mg_dl",
                "ldl_mg_dl",
                "total_cholesterol_mg_dl",
            ]:
                val = getattr(cp, field, None)
                if val is not None:
                    codes.add(field.replace("_mg_dl", ""))

        if bm:
            for field in [
                "weight_kg",
                "height_cm",
                "waist_cm",
                "hip_cm",
                "systolic_bp",
                "diastolic_bp",
            ]:
                val = getattr(bm, field, None)
                if val is not None:
                    codes.add(
                        field.replace("_kg", "").replace("_cm", "").replace("_bp", "")
                    )

        if encounter.observations:
            for obs in encounter.observations:
                if obs.value is not None:
                    codes.add(str(obs.code))

        if encounter.conditions:
            codes.add("conditions")

        if getattr(encounter, "demographics", None):
            d = encounter.demographics
            if getattr(d, "age_years", None) is not None:
                codes.add("age")
            if getattr(d, "gender", None):
                codes.add("gender")

        return codes

    def _field_available(self, field: str, available: set) -> bool:
        field_lower = field.lower()
        aliases = {
            "glucose": ["glucose", "glucose_mg_dl"],
            "triglycerides": ["triglycerides", "triglycerides_mg_dl"],
            "hdl": ["hdl", "hdl_mg_dl"],
            "ldl": ["ldl", "ldl_mg_dl"],
            "total_cholesterol": ["total_cholesterol", "total_cholesterol_mg_dl"],
            "creatinine": ["creatinine", "creatinine_mg_dl"],
            "hba1c": ["hba1c", "hba1c_percent"],
            "alt": ["alt", "alt_u_l", "alanine_aminotransferase"],
            "ggt": ["ggt", "ggt_u_l"],
            "tsh": ["tsh", "tsh_mi_u_l"],
            "ft4": ["ft4", "ft4_ng_dl"],
            "weight": ["weight", "weight_kg"],
            "height": ["height", "height_cm"],
            "waist": ["waist", "waist_cm"],
            "hip": ["hip", "hip_cm"],
            "sbp": ["sbp", "systolic_bp", "8480-6"],
            "dbp": ["dbp", "diastolic_bp", "8462-4"],
            "albumin": ["albumin", "albumin_g_dl"],
            "hgb": ["hemoglobin", "hgb", "718-7"],
            "egfr": ["egfr", "egfr_ckd_epi"],
            "uacr": ["uacr", "albumin_creatinine_ratio"],
            "apob": ["apob", "apob_mg_dl"],
            "apoa1": ["apoa1", "apoa1_mg_dl"],
            "vitamin_d": ["vitamin_d", "vitd"],
            "shbg": ["shbg"],
            "testosterone": ["testosterone", "total_testosterone"],
            "crp_hs": ["crp_hs", "hs_crp", "crp"],
            "platelets": ["platelets", "platelet_count"],
            "bmi": ["bmi", "bmi_calculated"],
            "grip_right": ["grip_right", "grip_r", "grip_right_kg"],
            "gait_speed": ["gait_speed", "gait"],
            "ace_score": ["ace_score", "ace"],
            "phq9_item9": ["phq9_item_9", "phq9_item9"],
            "conditions": ["conditions", "icd10"],
            "age": ["age", "age_years"],
            "gender": ["gender", "sex"],
        }
        for alias in aliases.get(field_lower, [field_lower]):
            if alias in available:
                return True
        return False

    def _rank_labs(self, quickwins: list[QuickWin]) -> list[LabRecommendation]:
        from collections import Counter

        counter: Counter = Counter()
        for qw in quickwins:
            for code in qw.missing_codes:
                counter[code] += 1
        return [
            LabRecommendation(
                code=code, display_name=self._lab_display_name(code), unlocks=count
            )
            for code, count in counter.most_common()
        ]

    def _lab_display_name(self, code: str) -> str:
        names = {
            "VITD-001": "25-OH Vitamina D",
            "UACR-001": "Relación Albumina/Creatinina (UACR)",
            "GRIP-R-001": "Dinamometría (fuerza de presa)",
            "GRIP-L-001": "Dinamometría (mano izquierda)",
            "GAIT-001": "Velocidad de marcha 4m",
            "APOB-001": "ApoB",
            "APOA1-001": "ApoA1",
            "TRIG-001": "Triglicéridos",
            "HDL-001": "Colesterol HDL",
            "LDL-001": "Colesterol LDL",
            "SHBG-001": "SHBG",
            "TEST-001": "Testosterona Total",
            "TSH-001": "TSH",
            "FT4-001": "T4 Libre",
            "HBA1C-001": "Hemoglobina Glicosilada",
            "EGFR-001": "eGFR (CKD-EPI)",
            "VIT-B12-001": "Vitamina B12",
            "TGO-001": "TGO/ALT",
            "TGP-001": "TGP/AST",
            "GGT-001": "GGT",
            "CRP-HS-001": "Proteína C Reactiva (hs-PCR)",
            "LIPASE-001": "Lipasa",
            "WEIGHT-001": "Peso corporal",
            "HEIGHT-001": "Talla",
            "WAIST-001": "Circunferencia de cintura",
            "HIP-001": "Circunferencia de cadera",
            "SBP-001": "Presión arterial sistólica",
            "DBP-001": "Presión arterial diastólica",
            "FASTING-001": "Glucosa en ayunas",
            "GLUC-001": "Glucosa",
        }
        return names.get(code, code.replace("-", " ").title())

    def _classify_tier(self, feasibility: float, ready_count: int) -> str:
        if ready_count <= 4:
            return "Básica"
        elif ready_count <= 12:
            return "Estándar"
        elif ready_count <= 20:
            return "Completa"
        else:
            return "Especializada"


readiness_engine = ClinicalDataReadinessEngine()
