"""
FHIR Bundle Generator for Integrum V2 Encounters.

Converts an Integrum V2 Encounter (with all its motors, observations,
conditions, and medications) into a FHIR R4 Bundle that can be consumed
by any FHIR-compliant system (HAPI FHIR, Epic, Cerner, etc.).

This is the core interoperability layer between Integrum V2 and the
broader healthcare ecosystem.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.fhir.resources import (
    FHIRBundle,
    FHIRPatient,
    FHIREncounter,
    FHIRObservation,
    FHIRCondition,
    FHIRMedicationStatement,
    FHIRQuestionnaireResponse,
)


def encounter_to_fhir_bundle(
    encounter,
    results: Optional[Dict[str, Any]] = None,
    include_calculated: bool = True,
) -> FHIRBundle:
    """
    Convert an Integrum V2 Encounter to a FHIR R4 Bundle.
    Handles both domain Encounter (no created_at/conditions/medications)
    and SQLAlchemy EncounterModel (has all attributes).
    """
    bundle = FHIRBundle(
        id=encounter.id,
        timestamp=getattr(encounter, "created_at", None).isoformat()
        if getattr(encounter, "created_at", None)
        else datetime.utcnow().isoformat(),
    )

    # 1. Patient
    patient = FHIRPatient.from_encounter(encounter)
    bundle.add_resource(patient)

    # 2. Encounter
    fhir_encounter = FHIREncounter.from_encounter(encounter)
    bundle.add_resource(fhir_encounter)

    # 3. Observations (raw data)
    for obs in getattr(encounter, "observations", []):
        fhir_obs = FHIRObservation.from_observation(obs, encounter.id)
        bundle.add_resource(fhir_obs)

    # 4. Calculated indices from Encounter properties
    if include_calculated:
        calculated_obs = _add_calculated_observations(encounter)
        for obs in calculated_obs:
            bundle.add_resource(obs)

    # 5. Motor results as derived Observations
    if results:
        motor_obs = _add_motor_results_as_observations(encounter.id, results)
        for obs in motor_obs:
            bundle.add_resource(obs)

    # 6. Conditions (if available)
    for condition in getattr(encounter, "conditions", []):
        fhir_cond = FHIRCondition.from_condition(condition, encounter.id)
        bundle.add_resource(fhir_cond)

    # 7. Medications (if available)
    for med in getattr(encounter, "medications", []):
        fhir_med = FHIRMedicationStatement.from_medication(med, encounter.id)
        bundle.add_resource(fhir_med)

    # 8. Psychometric QuestionnaireResponses (if available)
    psych = getattr(encounter, "psychometrics", None)
    if psych:
        if psych.phq9_score:
            bundle.add_resource(
                FHIRQuestionnaireResponse.from_psychometric(
                    "phq9", psych.phq9_score, {}, encounter.id, encounter.created_at
                )
            )
        if psych.gad7_score:
            bundle.add_resource(
                FHIRQuestionnaireResponse.from_psychometric(
                    "gad7", psych.gad7_score, {}, encounter.id, encounter.created_at
                )
            )

    return bundle


def _add_calculated_observations(encounter) -> List[FHIRObservation]:
    """Add calculated indices as FHIR Observations."""
    observations = []
    encounter_id = encounter.id

    # BMI
    if encounter.bmi:
        observations.append(
            FHIRObservation.calculated(
                code="39156-5",
                display="Body mass index",
                value=encounter.bmi,
                unit="kg/m2",
                encounter_id=encounter_id,
                derived_from=["29463-7", "8302-2"],
            )
        )

    # HOMA-IR
    if encounter.homa_ir:
        observations.append(
            FHIRObservation.calculated(
                code="89242-2",
                display="Insulin resistance by HOMA",
                value=encounter.homa_ir,
                unit="",
                encounter_id=encounter_id,
                derived_from=["2339-0", "20448-7"],
            )
        )

    # eGFR
    if encounter.egfr_ckd_epi:
        observations.append(
            FHIRObservation.calculated(
                code="33914-3",
                display="Glomerular filtration rate/1.73 sq M",
                value=encounter.egfr_ckd_epi,
                unit="mL/min/1.73m2",
                encounter_id=encounter_id,
                derived_from=["2160-0"],
            )
        )

    # UACR
    if encounter.uacr:
        observations.append(
            FHIRObservation.calculated(
                code="14959-1",
                display="Albumin/Creatinine ratio in Urine",
                value=encounter.uacr,
                unit="mg/g",
                encounter_id=encounter_id,
            )
        )

    # Pulse Pressure
    if encounter.pulse_pressure:
        observations.append(
            FHIRObservation.calculated(
                code="8479-8",
                display="Pulse pressure",
                value=encounter.pulse_pressure,
                unit="mmHg",
                encounter_id=encounter_id,
                derived_from=["8480-6", "8462-4"],
            )
        )

    # Remnant Cholesterol
    if encounter.remnant_cholesterol:
        observations.append(
            FHIRObservation.calculated(
                code="13457-7",
                display="Remnant cholesterol",
                value=encounter.remnant_cholesterol,
                unit="mg/dL",
                encounter_id=encounter_id,
                derived_from=["2093-3", "2085-9", "13457-7"],
            )
        )

    # ApoB/ApoA1 Ratio
    if encounter.apob_apoa1_ratio:
        observations.append(
            FHIRObservation.calculated(
                code="13455-1",
                display="ApoB/ApoA1 ratio",
                value=encounter.apob_apoa1_ratio,
                unit="",
                encounter_id=encounter_id,
                derived_from=["13456-9", "13455-1"],
            )
        )

    return observations


def _add_motor_results_as_observations(
    encounter_id: str,
    results: Dict[str, Any],
) -> List[FHIRObservation]:
    """Convert motor adjudication results to FHIR Observations."""
    observations = []

    for motor_name, result in results.items():
        if not hasattr(result, "calculated_value"):
            continue

        # Map motor names to LOINC-like codes
        code_map = {
            "AcostaPhenotypeMotor": ("89250-5", "Obesity phenotype by Acosta"),
            "EOSSStagingMotor": ("89251-3", "Edmonton Obesity Staging System"),
            "BiologicalAgeMotor": ("89252-1", "Biological age"),
            "FLIMotor": ("89253-9", "Fatty Liver Index"),
            "VAIMotor": ("89254-7", "Visceral Adiposity Index"),
            "NFSMotor": ("89255-4", "NAFLD Fibrosis Score"),
            "KFREMotor": ("89256-2", "Kidney Failure Risk Equation 5y"),
            "CharlsonMotor": ("89257-0", "Charlson Comorbidity Index"),
            "DrugInteractionMotor": ("89258-8", "Drug interaction risk score"),
            "WomensHealthMotor": ("89259-6", "Women's health assessment"),
            "MensHealthMotor": ("89260-4", "Men's health assessment"),
            "FriedFrailtyMotor": ("89261-2", "Fried Frailty Phenotype"),
            "TyGBMIMotor": ("89262-0", "TyG-BMI Index"),
            "CVDReclassifierMotor": ("89263-8", "CVD Risk Reclassification"),
            "ObesityPharmaEligibilityMotor": (
                "89264-6",
                "Anti-obesity medication eligibility",
            ),
            "GLP1TitrationMotor": ("89265-3", "GLP-1 titration status"),
            "BodyCompositionTrendMotor": ("89266-1", "Body composition trend"),
            "GLP1MonitoringMotor": ("89267-9", "GLP-1 monitoring status"),
            "MetforminB12Motor": ("89268-7", "Metformin B12 monitoring"),
            "CancerScreeningMotor": ("89269-5", "Cancer screening gaps"),
            "SGLT2iBenefitMotor": ("89270-3", "SGLT2i benefit estimate"),
            "FreeTestosteroneMotor": ("89271-1", "Free testosterone"),
            "VitaminDMotor": ("89272-9", "Vitamin D status"),
            "ApoBApoA1Motor": ("89273-7", "ApoB/ApoA1 ratio"),
            "PulsePressureMotor": ("89274-5", "Pulse pressure assessment"),
            "SarcopeniaMotor": ("89275-2", "Sarcopenia screen"),
            "FunctionalSarcopeniaMotor": ("89276-0", "Functional sarcopenia"),
            "ProteinEngineMotor": ("89277-8", "Protein requirement"),
            "CVDHazardMotor": ("89278-6", "ASCVD 10-year risk"),
            "MarkovProgressionMotor": ("89279-4", "Diabetes progression risk"),
            "ObesityMasterMotor": ("89280-2", "Obesity master assessment"),
            "ClinicalGuidelinesMotor": ("89281-0", "Clinical guidelines audit"),
        }

        code, display = code_map.get(
            motor_name, (f"89299-{hash(motor_name) % 100}", motor_name)
        )

        # Extract numeric value if available
        value = None
        unit = ""
        if hasattr(result, "metadata") and result.metadata:
            for key in [
                "fli",
                "vai",
                "nfs",
                "risk_5y",
                "cci_score",
                "fried_score",
                "tyg_bmi",
                "lean_loss_pct",
                "vitd_ng_ml",
                "free_t_pg_ml",
            ]:
                if key in result.metadata and result.metadata[key] is not None:
                    value = result.metadata[key]
                    break

        if value is None:
            # Use confidence as a proxy numeric value
            value = result.confidence
            unit = "confidence"

        observations.append(
            FHIRObservation.calculated(
                code=code,
                display=display,
                value=value,
                unit=unit,
                encounter_id=encounter_id,
                threshold=result.calculated_value if result.calculated_value else None,
            )
        )

    return observations
