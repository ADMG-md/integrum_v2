from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple


class LaboratoryStewardshipMotor(BaseClinicalMotor):
    """
    Precision Eligibility Engine (LATAM Strategy).
    Suggests high-cost biomarkers only when clinical flags justify them.

    Evidence:
    - Ahlqvist et al., 2018. Lancet Diabetes Endocrinol 6(5): 361-369.
      Novel subgroups of adult-onset diabetes: C-peptide + GADA for LADA classification.
    - Ladenson et al., 2000. Arch Intern Med 160(11): 1573-1575.
      Subclinical thyroid dysfunction: when to extend testing beyond TSH.
    - Sniderman et al., 2019. JAMA 321(1): 67-68.
      ApoB vs LDL-C for CVD risk: ApoB is superior in atherogenic dyslipidemia.
    - Angulo et al., 2007. Hepatology 45(4): 846-854.
      FIB-4 and NAFLD staging: transaminases as initial screening trigger.

    REQUIREMENT_ID: LAB-STEWARDSHIP
    """

    REQUIREMENT_ID = "LAB-STEWARDSHIP"

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        return True, ""  # Run always to assess eligibility

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        suggestions = []
        evidence = []

        # 1. Eligibility for Pack Ahlqvist (Diabetes Precision)
        hba1c = encounter.get_observation("4548-4")
        bmi = encounter.bmi
        if hba1c and hba1c.value > 8.0:
            if bmi and bmi < 25.0:
                suggestions.append("Solicitar 'Pack Ahlqvist' (Péptido C + GADA)")
                evidence.append(
                    ClinicalEvidence(
                        type="Flag",
                        code="LADA_SUSPICION",
                        value="Positive",
                        display="Diabetes con IMC Bajo",
                        threshold="HbA1c > 8 + BMI < 25",
                    )
                )

        # 2. Eligibility for Thyroid 360 (Advanced Endocrine)
        tsh = encounter.get_observation("11579-0")
        if tsh and 0.4 <= tsh.value <= 4.5:
            # If standard markers are normal but there are clinical comorbidities/symptoms
            # Note: Symptoms would come from conditions or a specific lifestyle flag
            if any(
                c.code in ["F41.1", "G47.0"] for c in encounter.conditions
            ):  # Anxiety, Insomnia
                suggestions.append("Escalar a 'Thyroid 360' (rT3 + SHBG)")
                evidence.append(
                    ClinicalEvidence(
                        type="Flag",
                        code="EUTHYROID_SYMPTOMS",
                        value="Present",
                        display="Síntomas persistentes con TSH normal",
                    )
                )

        # 3. Eligibility for Cardio-ApoB Pack
        ldl = encounter.get_observation("18262-6")
        tg = encounter.get_observation("2571-8")
        if ldl and ldl.value > 130 and tg and tg.value > 150:
            suggestions.append("Solicitar 'Cardio-ApoB Pack' (ApoB + Lp(a))")
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="ATHEROGENIC_DYSLIPIDEMIA",
                    value="Detected",
                    display="Dislipidemia Aterogénica (LDL > 130 + TG > 150)",
                )
            )

        # 4. Eligibility for LiverStaging (FIB-4 escalation)
        alt = encounter.get_observation("22538-3")
        ast = encounter.get_observation("29230-0")
        if (alt and alt.value > 30) or (ast and ast.value > 30):
            suggestions.append("Completar 'Perfil MASLD' (Plaquetas + GGT)")
            evidence.append(
                ClinicalEvidence(
                    type="Flag",
                    code="LIVER_FLAGS",
                    value="High",
                    display="Transaminasas > 30 (Alerta silente)",
                )
            )

        return AdjudicationResult(
            calculated_value=" | ".join(suggestions)
            if suggestions
            else "Protocolo Base Suficiente",
            confidence=1.0,  # Rules are deterministic stewardship flags
            evidence=evidence,
            explanation="Criterios de Medicina de Precisión LATAM: Justificación clínica para laboratorios de alto costo.",
        )
