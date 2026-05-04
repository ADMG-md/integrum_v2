from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel
from typing import Tuple

class EOSSStagingMotor(BaseClinicalMotor):
    """
    Edmonton Obesity Staging System (EOSS) Motor.
    Classifies patients into stages (0-4) based on clinical conditions.
    """
    REQUIREMENT_ID = "EOSS-2009"

    # Clinical systems mapping for mapping end-organ damage
    SYSTEMS = {
        "CARDIOVASCULAR": ["I10", "I20", "I21", "I50"], # HTN, Angina, MI, Heart Failure
        "METABOLIC": ["E11", "E78"],                    # DM2, Dyslipidemia
        "RESPIRATORY": ["J44", "G47.3"],                # COPD, Sleep Apnea
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # R-04 Fix: Accept either administrative code (E66) OR biometric obesity (BMI >= 30)
        obesity_dx = encounter.has_condition("E66")
        obesity_bmi = encounter.bmi is not None and encounter.bmi >= 30
        
        if not (obesity_dx or obesity_bmi):
            return False, "Not applicable: No obesity evidence (E66 code or BMI >= 30)"
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        stage = 0
        evidence = []
        confidence = CONFIDENCE_VALUES[ConfidenceLevel.ESTABLISHED_GUIDELINE]  # EOSS is highly deterministic
        
        # Stage 2: Established Chronic Disease
        active_conditions = [
            ("E11", "Diabetes Tipo 2"),
            ("I10", "Hipertensión Esencial"),
            ("G47.33", "Apnea del Sueño (OSA)"),
            ("E78.5", "Dislipidemia"),
            ("K76.0", "Hígado Graso (MASLD)")
        ]
        
        for code, display in active_conditions:
            if encounter.has_condition(code):
                stage = max(stage, 2)
                evidence.append(ClinicalEvidence(type="Condition", code=code, display=display))

        # Stage 4: Severe Functional Limitations / End-Stage
        disabling_conditions = [
            ("N18.5", "Enfermedad Renal Terminal (Diálisis)"),
            ("I50.4", "Insuficiencia Cardíaca Clase IV"),
            ("I63.9", "ACV con Discapacidad Severa")
        ]
        
        for code, display in disabling_conditions:
            if encounter.has_condition(code):
                stage = max(stage, 4)
                evidence.append(ClinicalEvidence(type="Condition", code=code, display=display))

        # Stage 3: End-Organ Damage
        damage_conditions = [
            ("I21", "Infarto al Miocardio"),
            ("I50", "Insuficiencia Cardíaca"),
            ("I63", "ACV Isquémico"),
            ("N18", "Enfermedad Renal Crónica")
        ]
        
        for code, display in damage_conditions:
            if encounter.has_condition(code):
                stage = max(stage, 3)
                evidence.append(ClinicalEvidence(type="Condition", code=code, display=display))

        # Check for Stage 1 (Risk Factors) if still at Stage 0
        if stage == 0:
            if encounter.has_condition("E09") or encounter.has_condition("R73.0"): # Prediabetes
                 stage = 1
                 evidence.append(ClinicalEvidence(type="Condition", code="R73.0", display="Prediabetes/Riesgo"))

        explanation = (
            f"El paciente se encuentra en EOSS Estadio {stage}. "
            f"{'Requiere intervención médica intensiva.' if stage >= 2 else 'Enfoque preventivo y de estilo de vida.'}"
        )

        return AdjudicationResult(
            calculated_value=f"EOSS Stage {stage}",
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui="CONFIRMED_ACTIVE",
            explanation=explanation
        )
