from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple

from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel


class GLP1MonitoringMotor(BaseClinicalMotor):
    """
    GLP-1/GIP Therapy Monitoring Engine.

    Monitors patients on GLP-1 receptor agonists (semaglutide, tirzepatide, liraglutide)
    for:
    1. Weight loss velocity (expected: 0.5-1.0 kg/week initially)
    2. Lean mass loss detection (critical safety concern)
    3. Plateau detection (weight loss < 0.25 kg/week for 4+ weeks)
    4. Adverse effect screening (gallbladder, pancreas, gastroparesis)

    Evidence:
    - Wilding et al., 2021. NEJM 384: 989-1002. doi: 10.1056/NEJMoa2032183.
      STEP 1 trial: semaglutide 2.4mg, 14.9% weight loss at 68 weeks.
    - Jastreboff et al., 2022. NEJM 387: 205-216. doi: 10.1056/NEJMoa2206038.
      SURMOUNT-1: tirzepatide up to 22.5% weight loss at 72 weeks.
    - Rubino et al., 2021. Lancet Diabetes Endocrinol 9: 1-12.
      Lean mass loss with GLP-1: 20-40% of total weight loss is lean mass.
    - Davies et al., 2015. JAMA 314(12): 1274-1284.
      Liraglutide 3.0mg (SCALE): 8.0% weight loss at 56 weeks.
    - Pancreatitis risk: FDA Drug Safety Communication 2013.

    REQUIREMENT_ID: GLP1-MONITOR
    """

    REQUIREMENT_ID = "GLP1-MONITOR"

    OBESOGENIC_CODES = {
        "SEMAGLUTIDE",
        "TIRZEPATIDE",
        "LIRAGLUTIDE",
        "DULAGLUTIDE",
        "EXENATIDE",
        "GLP1-RA",
        "GIP-GLP1",
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        on_glp1 = any(
            med.name.upper().replace(" ", "") in self.OBESOGENIC_CODES
            or med.code in self.OBESOGENIC_CODES
            for med in encounter.medications
        )
        if not on_glp1:
            return False, "No GLP-1/GIP therapy detected. Skipping monitoring."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        findings = []
        evidence = []
        alerts = []

        current_weight_obs = encounter.get_observation("29463-7")
        current_weight = (
            safe_float(current_weight_obs.value) if current_weight_obs else None
        )
        prev_weight = encounter.metadata.get("prev_weight_kg")

        current_mm_obs = encounter.get_observation(
            "MMA-001"
        ) or encounter.get_observation("MUSCLE-KG")
        current_mm = safe_float(current_mm_obs.value) if current_mm_obs else None
        prev_mm = encounter.metadata.get("prev_muscle_mass_kg")

        # 1. Weight loss velocity
        if current_weight and prev_weight:
            weight_delta = prev_weight - current_weight
            weight_loss_pct = (
                (weight_delta / prev_weight) * 100 if prev_weight > 0 else 0
            )

            evidence.append(
                ClinicalEvidence(
                    type="Calculation",
                    code="WEIGHT-LOSS",
                    value=round(weight_delta, 1),
                    threshold="0.5-1.0 kg/week expected",
                    display=f"Cambio de peso: {weight_delta:.1f} kg ({weight_loss_pct:.1f}%)",
                )
            )

            if weight_loss_pct > 15:
                alerts.append(
                    f"Perdida de peso >15% ({weight_loss_pct:.1f}%). "
                    f"Riesgo de desnutricion y perdida de masa magra."
                )
            elif weight_loss_pct > 10:
                alerts.append(
                    f"Perdida de peso significativa ({weight_loss_pct:.1f}%). "
                    f"Monitorear composicion corporal."
                )

        # 2. Lean mass loss (CRITICAL)
        if current_mm and prev_mm and prev_mm > 0:
            mm_delta = prev_mm - current_mm
            mm_loss_pct = (mm_delta / prev_mm) * 100

            evidence.append(
                ClinicalEvidence(
                    type="Calculation",
                    code="MUSCLE-LOSS",
                    value=round(mm_delta, 1),
                    threshold="<5% loss acceptable",
                    display=f"Perdida de masa muscular: {mm_delta:.1f} kg ({mm_loss_pct:.1f}%)",
                )
            )

            if mm_loss_pct > 10:
                alerts.append(
                    f"ALERTA: Perdida de masa muscular >10% ({mm_loss_pct:.1f}%). "
                    f"Considerar reduccion de dosis, aumento de proteina, ejercicio de fuerza."
                )
                findings.append("Perdida excesiva de masa magra")
            elif mm_loss_pct > 5:
                alerts.append(
                    f"Perdida de masa muscular >5% ({mm_loss_pct:.1f}%). "
                    f"Reforzar ingesta proteica y entrenamiento de resistencia."
                )
                findings.append("Perdida moderada de masa magra")

        # 3. Plateau detection
        if current_weight and prev_weight:
            weight_delta = abs(prev_weight - current_weight)
            weeks_on_therapy = encounter.metadata.get("glp1_weeks", 12)
            if weeks_on_therapy >= 12 and weight_delta < 1.0:
                findings.append("Plateau de perdida de peso detectado")
                alerts.append(
                    "Plateau: Perdida <1 kg en ultimas semanas. "
                    "Considerar: ajuste de dosis, combinacion terapéutica, "
                    "evaluacion de adherencia."
                )

        # 4. GI adverse effect screening
        lipase_obs = encounter.get_observation("LIPASE-001")
        if lipase_obs:
            lipase = safe_float(lipase_obs.value)
            if lipase and lipase > 150:
                findings.append("Lipasa elevada - riesgo de pancreatitis")
                alerts.append(
                    f"Lipasa: {lipase} U/L (>3x ULN). "
                    f"Evaluar pancreatitis. Considerar suspension de GLP-1."
                )

        amylase_obs = encounter.get_observation("AMYLASE-001")
        if amylase_obs:
            amylase = safe_float(amylase_obs.value)
            if amylase and amylase > 120:
                findings.append("Amilasa elevada")

        # 5. Gallbladder monitoring
        alt = encounter.metabolic_panel.alt_u_l
        ast = encounter.metabolic_panel.ast_u_l
        alkphos = encounter.metabolic_panel.alkaline_phosphatase_u_l
        if alkphos and alkphos > 120:
            findings.append("Fosfatasa alcalina elevada - evaluar colestasis")
            alerts.append(
                "FA elevada. Evaluar litiasis biliar (efecto adverso de GLP-1). "
                "Considerar ecografia abdominal."
            )

        if not findings:
            findings.append("Terapia GLP-1 sin alertas de seguridad detectadas")

        if alerts:
            estado = "CONFIRMED_ACTIVE"
            explanation = "Alertas de monitoreo GLP-1: " + " | ".join(alerts)
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]
        else:
            estado = "INDETERMINATE_LOCKED"
            explanation = "Monitoreo GLP-1: Sin hallazgos de preocupacion."
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]

        return AdjudicationResult(
            calculated_value=" | ".join(findings),
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation=explanation,
            metadata={
                "alerts": alerts,
                "findings": findings,
                "weight_loss_pct": round(
                    ((prev_weight - current_weight) / prev_weight) * 100, 1
                )
                if current_weight and prev_weight
                else None,
                "muscle_loss_pct": round(((prev_mm - current_mm) / prev_mm) * 100, 1)
                if current_mm and prev_mm
                else None,
            },
        )
