from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple

class CTrajectoryMotor(BaseClinicalMotor):
    """
    Longitudinal clinical engine evaluating obesity therapy response and skeletal safety at 12 weeks.

    Primary Outcomes:
    - Early response at 12 weeks (Non-responder if < 5% weight loss).
      Reference: Wilding et al., 2021 (STEP 1 trial), Jastreboff et al., 2022 (SURMOUNT-1).
      Patients failing to achieve 5% weight loss at 12 weeks are highly unlikely to achieve 
      long-term success and should have their therapy modified.
    - Sarcopenic risk from excessive muscle (FFM) loss.
      Reference: Heymsfield et al., 2019 (Obesity).
      FFM loss representing >= 25% of total weight loss indicates a high risk of sarcopenia 
      and metabolic slowing.

    REQUIREMENT_ID: TRAJECTORY-12W
    """

    REQUIREMENT_ID = "TRAJECTORY-12W"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        meta = encounter.metadata or {}
        if not meta.get("baseline_weight_kg"):
            return False, "Missing baseline weight for trajectory evaluation."
        
        weight_obs = encounter.get_observation("29463-7") or encounter.get_observation("W-001")
        if not weight_obs:
            return False, "Missing current weight observation."
        
        if meta.get("days_elapsed") is None:
            return False, "Missing days_elapsed timeline metric."

        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        meta = encounter.metadata or {}
        
        baseline_weight = float(meta["baseline_weight_kg"])
        days_elapsed = int(meta["days_elapsed"])
        
        weight_obs = encounter.get_observation("29463-7") or encounter.get_observation("W-001")
        current_weight = float(weight_obs.value)

        baseline_ffm = meta.get("baseline_ffm_kg")
        if baseline_ffm is not None:
            baseline_ffm = float(baseline_ffm)

        ffm_obs = encounter.get_observation("BIA-FFM-KG") or encounter.get_observation("BIA-LEAN-KG")
        current_ffm = float(ffm_obs.value) if ffm_obs else None

        in_window = 76 <= days_elapsed <= 104

        if not in_window:
            return AdjudicationResult(
                calculated_value="C_INDETERMINATE",
                confidence=0.0,
                estado_ui="INDETERMINATE_LOCKED",
                dato_faltante="Fuera de ventana temporal de 12 semanas (76-104 días)",
                explanation=f"Evaluación longitudinal fuera de la ventana de 12 semanas (días transcurridos: {days_elapsed}).",
                metadata={"days_elapsed": days_elapsed, "completeness_status": "indeterminate"}
            )

        weight_diff = baseline_weight - current_weight
        weight_loss_pct = (weight_diff / baseline_weight) * 100 if baseline_weight > 0 else 0.0

        evidence = [
            ClinicalEvidence(
                type="Timeline",
                code="DAYS_ELAPSED",
                value=days_elapsed,
                display="Días de seguimiento"
            ),
            ClinicalEvidence(
                type="Observation",
                code="WEIGHT_LOSS_PCT",
                value=round(weight_loss_pct, 2),
                display="Porcentaje de pérdida de peso"
            )
        ]

        recs = []
        metadata = {
            "weight_loss_percent": round(weight_loss_pct, 2),
            "days_elapsed": days_elapsed,
            "completeness_status": "complete"
        }

        ffm_loss_ratio = 0.0
        sarcopenic_alert = False

        if baseline_ffm is not None and current_ffm is not None and weight_diff > 0:
            ffm_diff = baseline_ffm - current_ffm
            ffm_loss_ratio = ffm_diff / weight_diff
            metadata["ffm_loss_ratio"] = round(ffm_loss_ratio, 4)
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="FFM_LOSS_RATIO",
                    value=round(ffm_loss_ratio * 100, 2),
                    display="Proporción de pérdida de masa muscular"
                )
            )
            if ffm_loss_ratio >= 0.25:
                sarcopenic_alert = True
        elif (baseline_ffm is not None or current_ffm is not None):
            metadata["completeness_status"] = "partial"

        if weight_loss_pct < 5.0:
            calculated = "C2_NON_RESPONDER"
            estado_ui = "PROBABLE_WARNING"
            recs.append("Considerar escalamiento de dosis de GLP-1 o cambio de estrategia farmacológica")
            explanation = "No respondedor temprano a las 12 semanas (< 5% pérdida de peso). Se sugiere intensificación terapéutica."
        else:
            if sarcopenic_alert:
                calculated = "C3_RESPONDER_SARKOPENIC_RISK"
                estado_ui = "PROBABLE_WARNING"
                recs.append("Ajustar aporte proteico + entrenamiento de fuerza")
                explanation = "Buen respondedor en peso, pero con pérdida muscular excesiva (>= 25% del total perdido). Riesgo de sarcopenia."
            else:
                calculated = "C1_RESPONDER_SAFE"
                estado_ui = "CONFIRMED_ACTIVE"
                recs.append("Continuar con la estrategia terapéutica actual")
                explanation = "Buen respondedor temprano con preservación adecuada de masa muscular."

        return AdjudicationResult(
            calculated_value=calculated,
            confidence=CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE],
            estado_ui=estado_ui,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            recomendacion_farmacologica=recs,
            explanation=explanation,
            metadata=metadata
        )
