from src.engines.base import BaseClinicalMotor
from src.engines.domain import Encounter, AdjudicationResult, ClinicalEvidence
from typing import Tuple


class AcostaPhenotypeMotor(BaseClinicalMotor):
    """
    Acosta Metabolic Phenotype Classifier.
    Refactored for V2 to consume structured conditions and observations.
    """

    REQUIREMENT_ID = "ACOSTA-2021"  # DOI: 10.1002/oby.23120

    # Unified CODES Catalog (R-01 Fix: merged duplicated dicts)
    # Sources: Acosta 2015 (original phenotyping) + 2021 (open-scale adaptation)
    CODES = {
        # --- Primary Phenotype Markers (2021 Adaptation) ---
        "AD_LIBITUM_KCAL": "BUFFET-KCAL",  # Ad-Libitum Buffet Intake
        "ANXIETY_SCORE": "GAD-7",  # GAD-7 (Anxiety) - Alternative to HADS-A
        "GASTRIC_EMPTYING": "GE-T12",  # Scintigraphy T1/2
        "REE_MEASURED": "REE-M",  # Resting Energy Expenditure
        "SACIEDAD_TEMPRANA": "ST-001",  # Early Satiety Questionnaire
        # --- Secondary / Complementary Markers (2015 Original) ---
        "BINGE_EATING": "F50.81",  # CIE-10/11 Binge Eating
        "TFEQ_EMOTIONAL": "TFEQ-EMOTIONAL",  # Emotional eating subscale
        "TFEQ_UNCONTROLLED": "TFEQ-UNCONTROLLED",  # Hedonic drive
        "HEDONIC_HUNGER": "HEDONIC-001",  # Hedonic hunger marker
        "SMI": "SMI-001",  # Skeletal Muscle Index
        "TFEQ_COGNITIVE": "TFEQ-COGNITIVE",  # Cognitive restraint
        "ATHENS_INSOMNIA": "AIS-001",  # Sleep debt (Athens Scale)
    }

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        # Minimal data for Acosta: check if we have BMI.
        # If not, we skip the motor silently rather than blocking the report.
        if not encounter.bmi:
            return False, "Skipping Acosta: Missing BMI."
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence = []
        phenotypes_active = []
        confidence_map = {}

        # 1. Cerebro Hambriento (Saciación Retrasada)
        buffet = encounter.get_observation(self.CODES["AD_LIBITUM_KCAL"])
        is_male = encounter.metadata.get("sex") == "M"

        if buffet:
            try:
                buffet_val = float(buffet.value)
                threshold = 1376 if is_male else 894
                if buffet_val > threshold:
                    # US: Solo si 2 encuentros consecutivos positivos (confidence placeholder)
                    # For now, following MAESTRO: Max 0.70 for Hungry Brain
                    confidence_map["Cerebro Hambriento"] = 0.70
                    phenotypes_active.append("Cerebro Hambriento")
                    evidence.append(
                        ClinicalEvidence(
                            type="Observation",
                            code=self.CODES["AD_LIBITUM_KCAL"],
                            value=buffet_val,
                            threshold=f">{threshold}",
                            display="Ingesta Ad-Libitum",
                        )
                    )
            except (ValueError, TypeError):
                pass

        # 2. Intestino Hambriento (Saciedad Acelerada / Temprana)
        ge = encounter.get_observation(self.CODES["GASTRIC_EMPTYING"])
        st = encounter.get_observation(self.CODES["SACIEDAD_TEMPRANA"])

        if ge:
            try:
                ge_val = float(ge.value)
                if ge_val < 85:
                    confidence_map["Intestino Hambriento"] = 0.82
                    phenotypes_active.append("Intestino Hambriento")
                    evidence.append(
                        ClinicalEvidence(
                            type="Observation",
                            code=self.CODES["GASTRIC_EMPTYING"],
                            value=ge_val,
                            threshold="<85 min",
                            display="Vaciado Gástrico T1/2",
                        )
                    )
            except (ValueError, TypeError):
                pass

        # AUDITOR RULE: Questionnaire alone = 0.60 confidence
        if st and "Intestino Hambriento" not in phenotypes_active:
            try:
                st_val = float(st.value)
                if st_val > 0:
                    confidence_map["Intestino Hambriento"] = 0.60
                    phenotypes_active.append("Intestino Hambriento")
                    evidence.append(
                        ClinicalEvidence(
                            type="Observation",
                            code=self.CODES["SACIEDAD_TEMPRANA"],
                            value=st_val,
                            display="Cuestionario Saciedad Temprana",
                        )
                    )
            except (ValueError, TypeError):
                pass

        # 3. Hambre Emocional o Hedónica (Drive Ansioso/Hedónico)
        anxiety = encounter.get_observation(self.CODES["ANXIETY_SCORE"])
        tfeq_emotional = encounter.get_observation(self.CODES["TFEQ_EMOTIONAL"])
        tfeq_uncontrolled = encounter.get_observation(self.CODES["TFEQ_UNCONTROLLED"])
        psych_confirm = encounter.metadata.get("external_psych_confirmation", False)

        emotional_markers = []
        if anxiety and float(anxiety.value) >= 10:
            emotional_markers.append(f"GAD-7 ({anxiety.value})")
        if tfeq_emotional and float(tfeq_emotional.value) > 2.5:  # Scale 1-4
            emotional_markers.append(f"TFEQ-Emotional ({tfeq_emotional.value})")
        if tfeq_uncontrolled and float(tfeq_uncontrolled.value) > 2.5:
            emotional_markers.append(f"TFEQ-Uncontrolled ({tfeq_uncontrolled.value})")

        if emotional_markers:
            # Multi-component confidence (H-019 Hardening)
            conf = 0.85 if (len(emotional_markers) >= 2 or psych_confirm) else 0.65
            confidence_map["Hambre Emocional"] = conf
            phenotypes_active.append("Hambre Emocional")
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code="BEHAVIORAL_CLUSTER",
                    value=", ".join(emotional_markers),
                    display="Clúster Conductual (Emocional/Hedónico)",
                )
            )

        # 4. Falta de Sueño (Influenciador de Hambre Hedónica)
        insomnia = encounter.get_observation(self.CODES["ATHENS_INSOMNIA"])
        if insomnia and float(insomnia.value) >= 6:
            phenotypes_active.append("Privación de Sueño (Driver de Hambre)")
            confidence_map["Privación de Sueño (Driver de Hambre)"] = (
                0.60  # Base findings confidence
            )
            evidence.append(
                ClinicalEvidence(
                    type="Observation",
                    code=self.CODES["ATHENS_INSOMNIA"],
                    value=insomnia.value,
                    threshold=">=6",
                    display="Escala de Atenas",
                )
            )

        # Final Adjudication Orquestration
        if not phenotypes_active:
            return AdjudicationResult(
                calculated_value="Fenotipo Metabólico Basal",
                confidence=1.0,
                estado_ui="CONFIRMED_ACTIVE",
                explanation="No se detectaron desviaciones fenotípicas significativas.",
            )

        # We take the max confidence for the primary status
        primary_phenotype = phenotypes_active[0]
        primary_conf = confidence_map.get(primary_phenotype, 0.0)

        estado = "INDETERMINATE_LOCKED"
        recs = []
        missing = None

        if primary_conf >= 0.80:
            estado = "CONFIRMED_ACTIVE"
        elif primary_conf > 0.65:
            estado = "PROBABLE_WARNING"

        # Pharmacological Lock: STRICTLY < 0.65 (so >= 0.65 is allowed)
        if primary_conf >= 0.65:
            if "Cerebro Hambriento" in primary_phenotype:
                recs.append("Agonista Receptor GLP-1 (ej: Semaglutida)")
            if "Intestino Hambriento" in primary_phenotype:
                recs.append("Liraglutida / Fibra Viscosa")
            if "Hambre Emocional" in primary_phenotype:
                recs.append("Naltrexona/Bupropión")
        else:
            if "Hambre Emocional" in primary_phenotype:
                missing = "Confirmación psicológica externa (requerida para elevar confianza > 0.65)"
            elif "Intestino Hambriento" in primary_phenotype:
                missing = (
                    "Indicar MCG de 14 días (requerido para elevar confianza > 0.65)"
                )

        return AdjudicationResult(
            calculated_value=" | ".join(phenotypes_active),
            confidence=primary_conf,
            evidence=evidence,
            requirement_id="DOI:10.1002/oby.23120",
            estado_ui=estado,
            dato_faltante=missing,
            recomendacion_farmacologica=recs,
            explanation=f"Determinación basada en Acosta 2021. Estado: {estado}.",
        )
