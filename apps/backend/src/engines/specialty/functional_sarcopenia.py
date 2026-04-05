from src.engines.base import BaseClinicalMotor
from src.engines.domain import (
    Encounter,
    AdjudicationResult,
    ClinicalEvidence,
    safe_float,
)
from typing import Tuple


class FunctionalSarcopeniaMotor(BaseClinicalMotor):
    """
    Functional Sarcopenia Assessment Motor.

    Evaluates physical performance and muscle strength per EWGSOP2 criteria
    using functional tests (not body composition):

    1. 5x Chair Stand Test (5xSTS) -- primary functional metric
       > 15 seconds = low physical performance (Cruz-Jentoft et al., 2019)
       Inability to complete = independent sarcopenia predictor
       (Sporin et al., 2023, DOI: 10.31382/eqol.230601)

    2. Grip Strength (Handgrip Dynamometry)
       < 27 kg (male) or < 16 kg (female) = reduced strength (EWGSOP2)

    3. Gait Speed
       <= 0.8 m/s = low physical performance (EWGSOP2)

    4. SARC-F Questionnaire
       >= 4 = sarcopenia risk (Malmstrom et al., 2016)

    This motor is INDEPENDENT from SarcopeniaMonitorMotor (which uses
    ASMI/BIA body composition). Together they provide the complete
    EWGSOP2 picture: composition + function.

    REQUIREMENT_ID: EWGSOP2-FUNC
    """

    REQUIREMENT_ID = "EWGSOP2-FUNC"

    GRIP_THRESHOLD_MALE = 27.0
    GRIP_THRESHOLD_FEMALE = 16.0
    GAIT_SPEED_THRESHOLD = 0.8
    FIVE_X_STS_THRESHOLD = 15.0
    SARCF_THRESHOLD = 4

    def validate(self, encounter: Encounter) -> Tuple[bool, str]:
        has_any = False
        missing = []

        if not encounter.get_observation("5XSTS-SEC"):
            missing.append("5XSTS-SEC")
        else:
            has_any = True

        grip_r = encounter.get_observation("GRIP-STR-R")
        grip_l = encounter.get_observation("GRIP-STR-L")
        if not grip_r and not grip_l:
            missing.append("GRIP-STR-R or GRIP-STR-L")
        else:
            has_any = True

        if not encounter.get_observation("GAIT-SPEED"):
            missing.append("GAIT-SPEED")
        else:
            has_any = True

        if not encounter.get_observation("SARCF-SCORE"):
            missing.append("SARCF-SCORE")
        else:
            has_any = True

        if not has_any:
            return False, (
                f"Skipping Functional Sarcopenia: No functional data. "
                f"Missing: {', '.join(missing)}"
            )
        return True, ""

    def compute(self, encounter: Encounter) -> AdjudicationResult:
        evidence = []
        flags = []
        score = 0
        tests_evaluated = 0

        is_male = encounter.metadata.get("sex", "").lower() in ["male", "m"]
        grip_threshold = (
            self.GRIP_THRESHOLD_MALE if is_male else self.GRIP_THRESHOLD_FEMALE
        )

        # 1. 5x Chair Stand Test
        sts_obs = encounter.get_observation("5XSTS-SEC")
        five_x_sts_result = None
        if sts_obs:
            tests_evaluated += 1
            sts_value = safe_float(sts_obs.value)
            if sts_value is not None and sts_value > 0:
                if sts_value > self.FIVE_X_STS_THRESHOLD:
                    score += 2
                    flags.append(
                        f"5xSTS: {sts_value:.1f}s (> {self.FIVE_X_STS_THRESHOLD}s = bajo rendimiento)"
                    )
                    five_x_sts_result = "abnormal"
                else:
                    five_x_sts_result = "normal"
                evidence.append(
                    ClinicalEvidence(
                        type="Observation",
                        code="5XSTS-SEC",
                        value=round(sts_value, 1),
                        threshold=f"<={self.FIVE_X_STS_THRESHOLD}s",
                        display="5x Chair Stand Test",
                    )
                )
            else:
                flags.append("5xSTS: valor invalido")

        # 2. Grip Strength (use best of R/L if both available)
        grip_r = encounter.get_observation("GRIP-STR-R")
        grip_l = encounter.get_observation("GRIP-STR-L")
        grip_values = []
        for grip_obs in [grip_r, grip_l]:
            if grip_obs:
                tests_evaluated += 1
                gv = safe_float(grip_obs.value)
                if gv is not None and gv > 0:
                    grip_values.append(gv)
                    is_low = gv < grip_threshold
                    if is_low:
                        score += 2
                        flags.append(
                            f"Grip {grip_obs.code}: {gv:.1f}kg (< {grip_threshold}kg = fuerza reducida)"
                        )
                    evidence.append(
                        ClinicalEvidence(
                            type="Observation",
                            code=grip_obs.code,
                            value=round(gv, 1),
                            threshold=f">={grip_threshold}kg",
                            display=f"Grip Strength ({grip_obs.code})",
                        )
                    )

        best_grip = max(grip_values) if grip_values else None

        # 3. Gait Speed
        gait_obs = encounter.get_observation("GAIT-SPEED")
        gait_speed_result = None
        if gait_obs:
            tests_evaluated += 1
            gs = safe_float(gait_obs.value)
            if gs is not None and gs > 0:
                if gs <= self.GAIT_SPEED_THRESHOLD:
                    score += 2
                    flags.append(
                        f"Gait speed: {gs:.2f}m/s (<={self.GAIT_SPEED_THRESHOLD}m/s = bajo rendimiento)"
                    )
                    gait_speed_result = "abnormal"
                else:
                    gait_speed_result = "normal"
                evidence.append(
                    ClinicalEvidence(
                        type="Observation",
                        code="GAIT-SPEED",
                        value=round(gs, 2),
                        threshold=f">{self.GAIT_SPEED_THRESHOLD}m/s",
                        display="Gait Speed",
                    )
                )

        # 4. SARC-F Questionnaire
        sarcf_obs = encounter.get_observation("SARCF-SCORE")
        sarcf_result = None
        if sarcf_obs:
            tests_evaluated += 1
            sarcf = safe_float(sarcf_obs.value)
            if sarcf is not None and sarcf >= 0:
                if sarcf >= self.SARCF_THRESHOLD:
                    score += 2
                    flags.append(
                        f"SARC-F: {int(sarcf)} (>={self.SARCF_THRESHOLD} = riesgo sarcopenia)"
                    )
                    sarcf_result = "positive"
                else:
                    sarcf_result = "negative"
                evidence.append(
                    ClinicalEvidence(
                        type="Observation",
                        code="SARCF-SCORE",
                        value=int(sarcf),
                        threshold=f"<{self.SARCF_THRESHOLD}",
                        display="SARC-F Score",
                    )
                )

        # Classification per EWGSOP2 algorithm
        # score >= 4 (2+ abnormal tests) = probable sarcopenia
        # score >= 2 (1 abnormal test) = possible sarcopenia
        # score == 0 = no functional sarcopenia indicators
        if score >= 4 and tests_evaluated >= 2:
            estado_ui = "CONFIRMED_ACTIVE"
            verdict = "SARCOPENIA FUNCIONAL PROBABLE"
            explanation = (
                f"Multiple indicadores funcionales de sarcopenia ({tests_evaluated} tests evaluados). "
                f"Hallazgos: {'; '.join(flags)}"
            )
            confidence = 0.92
        elif score >= 2:
            estado_ui = "PROBABLE_WARNING"
            verdict = "POSIBLE SARCOPENIA FUNCIONAL"
            explanation = (
                f"Indicador funcional aislado de sarcopenia ({tests_evaluated} tests evaluados). "
                f"Hallazgos: {'; '.join(flags)}. "
                f"Requiere confirmacion con ASMI/BIA."
            )
            confidence = 0.75
        else:
            estado_ui = "INDETERMINATE_LOCKED"
            verdict = "SIN INDICADORES FUNCIONALES DE SARCOPENIA"
            explanation = (
                f"Funcion fisica conservada en {tests_evaluated} test(s) evaluado(s)."
            )
            confidence = 0.85

        return AdjudicationResult(
            calculated_value=verdict,
            confidence=confidence,
            evidence=evidence,
            requirement_id=self.REQUIREMENT_ID,
            estado_ui=estado_ui,
            explanation=explanation,
            metadata={
                "tests_evaluated": tests_evaluated,
                "functional_score": score,
                "five_x_sts_status": five_x_sts_result,
                "best_grip_kg": round(best_grip, 1) if best_grip else None,
                "gait_speed_status": gait_speed_result,
                "sarcf_status": sarcf_result,
                "flags": flags,
                "is_male": is_male,
            },
        )
