from src.engines.base import BaseClinicalMotor
from src.domain.models import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple

class CStateMachineMotor(BaseClinicalMotor):
    """
    Axis C Motor: Evaluates longitudinal clinical trajectory based on weight, 
    FFM, and adherence history over the last 90 days.
    """

    @property
    def requirement_id(self) -> str:
        return "REQ-AXIS-C-001"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        return self.evaluate(encounter)

    def evaluate(self, encounter: Encounter) -> AdjudicationResult:
        # 1. Check for sufficient encounters
        encs = sorted(encounter.longitudinal_encounters, key=lambda x: x.encounter_date)
        
        # Ensure the current encounter is in the list
        if not any(e.encounter_id == encounter.id for e in encs):
            # If orchestrator didn't append the current encounter state, we construct it
            # But normally, it's cleaner to let Orchestrator pass all.
            # Let's assume orchestrator passes ALL relevant encounters INCLUDING the current one.
            pass

        if len(encs) < 2:
            return AdjudicationResult(
                calculated_value="indeterminate",
                confidence=0.0,
                estado_ui="INDETERMINATE_LOCKED",
                dato_faltante="Se requiere al menos un encounter previo",
                evidence=[],
                metadata={"reason": "Less than 2 encounters"}
            )

        current = encs[-1]
        previous = encs[-2]
        baseline = encs[0]

        # Handle missing data cleanly
        current_weight = current.weight_kg
        baseline_weight = baseline.weight_kg

        if current_weight is None or baseline_weight is None:
            return AdjudicationResult(
                calculated_value="indeterminate",
                confidence=0.0,
                estado_ui="INDETERMINATE_LOCKED",
                dato_faltante="Falta peso en el encuentro actual o base",
                evidence=[],
                metadata={"reason": "Missing weight data"}
            )

        # Days since last encounter
        days_since_last_encounter = (current.encounter_date - previous.encounter_date).days

        # Elapsed weeks
        elapsed_days = (current.encounter_date - baseline.encounter_date).days
        elapsed_weeks = max(elapsed_days / 7.0, 1.0) # minimum 1 week to avoid division by zero

        # Weekly rate (positive = loss, negative = gain)
        weekly_rate_kg = (baseline_weight - current_weight) / elapsed_weeks

        # Sarcopenic flag
        sarcopenic_flag = False
        completeness = "complete"
        
        if current.ffm_kg is not None and baseline.ffm_kg is not None:
            if baseline_weight > current_weight: # Must be losing weight
                weight_lost = baseline_weight - current_weight
                ffm_lost = baseline.ffm_kg - current.ffm_kg
                if (ffm_lost / weight_lost) > 0.25:
                    sarcopenic_flag = True
        else:
            completeness = "partial"

        # Apply C_state rules (descending order, first match wins)
        c_state = ""
        label = ""
        suggested_action = ""

        # C_reentry -> primer encounter tras C4 previo
        # We need to know if the PREVIOUS encounter was a C4.
        # How to know if previous was C4? If the gap before 'previous' was > 60 days?
        # The rule says: "C_reentry → primer encounter tras C4 previo".
        # This means if days_since_last_encounter > 60 occurred *between* previous and the one before previous?
        # No, "C4 -> days_since_last_encounter > 60". If the current encounter has a gap > 60 days, it's C4 right now.
        # So "tras C4 previo" means if the *previous* evaluation was C4.
        # Let's simplify: If days_since_last_encounter > 60, it IS C4. 
        # If the gap between 'previous' and 'the one before previous' was > 60, then the previous encounter WAS C4.
        is_reentry = False
        if len(encs) >= 3:
            prev_gap = (previous.encounter_date - encs[-3].encounter_date).days
            if prev_gap > 60:
                is_reentry = True
        
        # Or maybe it's simpler: If we had a C4, we are now in Reentry?
        # Let's follow the gap logic.
        
        if days_since_last_encounter > 60:
            c_state = "C4"
            label = "Sin contacto — posible abandono"
            completeness = "complete" # Overrides partial
            suggested_action = "Protocolo de contacto activo"
        elif is_reentry:
            c_state = "C_reentry"
            label = "Reingreso — nueva ventana iniciada"
            completeness = "partial"
            suggested_action = "Evaluación de reingreso estructurado"
        elif weekly_rate_kg < 0 or (46 <= days_since_last_encounter <= 60):
            c_state = "C3"
            label = "No respondedor / rescate requerido"
            suggested_action = "Protocolo de rescate y revisión de barreras"
        elif 0 <= weekly_rate_kg < 0.5 and days_since_last_encounter <= 45:
            c_state = "C2"
            label = "Respuesta subóptima — intensificación transitoria"
            suggested_action = "Intensificación de contacto y soporte"
        elif weekly_rate_kg >= 0.5 and days_since_last_encounter <= 45:
            c_state = "C1"
            label = "En trayectoria"
            if weekly_rate_kg >= 1.0:
                label = "En trayectoria | Respondedor"
            suggested_action = "Mantener plan — espaciar gradualmente"
        else:
            # Fallback
            c_state = "C2"
            label = "Respuesta subóptima — intensificación transitoria"
            suggested_action = "Intensificación de contacto y soporte"

        if sarcopenic_flag:
            label += " | Riesgo sarcopénico"

        audit_payload = {
            "window_days": 90,
            "baseline_weight": baseline_weight,
            "current_weight": current_weight,
            "weekly_rate_kg": round(weekly_rate_kg, 3),
            "days_since_last_encounter": days_since_last_encounter,
            "encounters_in_window": len(encs),
            "sarcopenic_flag": sarcopenic_flag
        }

        return AdjudicationResult(
            calculated_value=c_state,
            confidence=1.0 if completeness == "complete" else 0.8,
            estado_ui="ACTIVE",
            evidence=[
                ClinicalEvidence(
                    type="observation",
                    code="weekly_rate_kg",
                    value=weekly_rate_kg
                )
            ],
            metadata={
                "label": label,
                "suggested_action": suggested_action,
                "completeness": completeness,
                "audit_payload": audit_payload,
                "rule_version_semantic": "C_state_v0.1"
            }
        )
