from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    ActionItem,
    safe_float,
)
from typing import Tuple


class GLP1TitrationMotor(BaseClinicalMotor):
    """
    GLP-1/GIP Dose Titration Protocol Engine.

    Most GLP-1 "failures" are due to inadequate titration, not drug failure.
    This engine evaluates current dose, response, and adverse effects to
    recommend titration adjustments.

    Semaglutide (Wegovy/Ozempic) titration:
    - 0.25mg weekly x 4 weeks → 0.5mg x 4 weeks → 1.0mg x 4 weeks → 1.7mg x 4 weeks → 2.4mg maintenance
    - If intolerant at any step: maintain current dose 4 more weeks before escalating

    Tirzepatide (Zepbound/Mounjaro) titration:
    - 2.5mg weekly x 4 weeks → 5mg x 4 weeks → 7.5mg x 4 weeks → 10mg x 4 weeks → 12.5mg → 15mg maintenance

    Response assessment:
    - <5% weight loss at 12 weeks on maintenance dose → consider alternative
    - >=5% at 12 weeks → continue, consider dose escalation if tolerated
    - Plateau after initial response → evaluate adherence, diet, exercise

    REQUIREMENT_ID: GLP1-TITRATION
    """

    REQUIREMENT_ID = "GLP1-TITRATION"

    SEMAGLUTIDE_DOSES = [0.25, 0.5, 1.0, 1.7, 2.4]
    TIRZEPATIDE_DOSES = [2.5, 5.0, 7.5, 10.0, 12.5, 15.0]

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        on_glp1 = any(
            med.name.upper().replace(" ", "")
            in (
                "SEMAGLUTIDE",
                "WEGOVY",
                "OZEMPIC",
                "TIRZEPATIDE",
                "ZEPBOUND",
                "MOUNJARO",
            )
            or med.code in ("SEMAGLUTIDE", "TIRZEPATIDE", "GLP1-RA", "GIP-GLP1")
            for med in encounter.medications
        )
        if not on_glp1:
            return False, "No GLP-1/GIP therapy detected."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        # Find current GLP-1 medication
        current_med = None
        for med in encounter.medications:
            name = med.name.upper().replace(" ", "")
            if name in ("SEMAGLUTIDE", "WEGOVY", "OZEMPIC"):
                current_med = ("semaglutide", med.dose_amount or "0.25mg")
                break
            elif name in ("TIRZEPATIDE", "ZEPBOUND", "MOUNJARO"):
                current_med = ("tirzepatide", med.dose_amount or "2.5mg")
                break

        if not current_med:
            return AdjudicationResult(
                calculated_value="No se pudo determinar medicamento GLP-1 actual",
                confidence=0.0,
                evidence=[],
                requirement_id=self.REQUIREMENT_ID,
                estado_ui="INDETERMINATE_LOCKED",
                explanation="No se encontró GLP-1/GIP en medicamentos.",
            )

        drug, dose_str = current_med
        # Extract numeric dose
        dose_match = safe_float(dose_str.replace("mg", "").strip())
        if dose_match is None:
            dose_match = 0.25 if drug == "semaglutide" else 2.5

        doses = (
            self.SEMAGLUTIDE_DOSES if drug == "semaglutide" else self.TIRZEPATIDE_DOSES
        )
        drug_label = "Semaglutida" if drug == "semaglutide" else "Tirzepatida"
        max_dose = doses[-1]

        weeks_on_therapy = encounter.metadata.get("glp1_weeks", 4)
        prev_weight = encounter.metadata.get("prev_weight_kg")
        w_obs = encounter.get_observation("29463-7")
        current_weight = safe_float(w_obs.value) if w_obs else None

        findings = []
        actions = []

        # Weight loss assessment
        if prev_weight and current_weight and prev_weight > 0:
            weight_loss_pct = ((prev_weight - current_weight) / prev_weight) * 100
            weight_loss_pct = round(weight_loss_pct, 1)

            if weeks_on_therapy >= 12 and weight_loss_pct < 5:
                findings.append(
                    f"Respuesta subóptima: {weight_loss_pct}% pérdida a {weeks_on_therapy} semanas "
                    f"(esperado: >=5% a 12 semanas)"
                )
                if dose_match < max_dose:
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="high",
                            task=f"Escalar dosis de {drug_label} a siguiente nivel",
                            rationale=f"Solo {weight_loss_pct}% de pérdida. Escalar antes de considerar cambio de fármaco.",
                        )
                    )
                else:
                    findings.append(
                        f"Dosis máxima de {drug_label} alcanzada. Considerar alternativa terapéutica."
                    )
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="high",
                            task="Evaluar cambio a otro AOM o terapia combinada",
                            rationale=f"Respuesta insuficiente con dosis máxima de {drug_label}.",
                        )
                    )
            elif weight_loss_pct >= 5:
                findings.append(
                    f"Respuesta adecuada: {weight_loss_pct}% pérdida de peso"
                )
                if dose_match < max_dose and weeks_on_therapy >= 16:
                    actions.append(
                        ActionItem(
                            category="pharmacological",
                            priority="medium",
                            task="Considerar escalada de dosis para mayor eficacia",
                            rationale=f"Buena respuesta ({weight_loss_pct}%). Puede beneficiarse de dosis mayor.",
                        )
                    )
            else:
                findings.append(
                    f"Respuesta temprana: {weight_loss_pct}% a {weeks_on_therapy} semanas. "
                    f"Continuar y reevaluar a 12 semanas."
                )
        else:
            findings.append("Sin datos de peso serial para evaluar respuesta")

        # Current dose status
        dose_idx = doses.index(dose_match) if dose_match in doses else -1
        if dose_idx >= 0:
            findings.append(
                f"Dosis actual: {dose_match}mg ({dose_idx + 1}/{len(doses)} pasos)"
            )
            if dose_idx < len(doses) - 1:
                next_dose = doses[dose_idx + 1]
                findings.append(f"Siguiente escalón: {next_dose}mg")
            else:
                findings.append("Dosis máxima alcanzada")

        estado = (
            "CONFIRMED_ACTIVE"
            if any("subóptima" in f or "máxima" in f for f in findings)
            else "INDETERMINATE_LOCKED"
        )
        confidence = 0.88

        return AdjudicationResult(
            calculated_value=f"Titulación de {drug_label}: {'; '.join(findings[:2])}",
            confidence=confidence,
            evidence=[
                ClinicalEvidence(
                    type="Assessment",
                    code="GLP1-TITRATION",
                    value=dose_match,
                    threshold=f"max {max_dose}mg",
                    display=f"Titulación de {drug_label}",
                )
            ],
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado,
            explanation="; ".join(findings),
            action_checklist=actions,
            metadata={
                "drug": drug,
                "current_dose_mg": dose_match,
                "max_dose_mg": max_dose,
                "dose_step": dose_idx + 1 if dose_idx >= 0 else 0,
                "total_steps": len(doses),
                "weeks_on_therapy": weeks_on_therapy,
            },
        )
