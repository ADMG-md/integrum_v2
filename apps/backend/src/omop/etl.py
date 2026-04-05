"""
OMOP CDM 5.4 ETL for Integrum V2 Encounters.

Converts Integrum V2 encounters into OMOP CDM 5.4 format for:
- Longitudinal patient history
- OHDSI/HADES analysis
- Federated research networks (IMI-SOPHIA style)
- OMOP-on-FHIR exposure

This module generates SQL INSERT statements that can be executed against
an OMOP CDM database. It does NOT write directly to OMOP tables —
that should be done via a proper ETL pipeline (WhiteRabbit/Rabbit-In-A-Hat).

References:
- OMOP CDM 5.4: https://ohdsi.github.io/CommonDataModel/
- OHDSI Book of ETL: https://ohdsi.github.io/TheBookOfOhdsi/
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.omop.concept_map import (
    get_omop_measurement_concept,
    get_omop_condition_concept,
    get_omop_drug_concept,
    LOINC_TO_OMOP_MEASUREMENT,
)
from src.fhir.concept_map import (
    OBSERVATION_TO_LOINC,
    MEDICATION_TO_ATC,
    get_loinc_for_code,
    get_atc_for_medication,
)


def encounter_to_omop_sql(
    encounter,
    person_id: int,
    visit_occurrence_id: int,
    encounter_id_counter: int = 1,
) -> Dict[str, List[str]]:
    """
    Convert an Integrum V2 Encounter to OMOP CDM 5.4 SQL INSERT statements.

    Args:
        encounter: The Integrum Encounter object
        person_id: OMOP person_id for this patient
        visit_occurrence_id: OMOP visit_occurrence_id for this encounter
        encounter_id_counter: Counter for generating unique IDs

    Returns:
        Dict mapping OMOP table names to lists of SQL INSERT statements
    """
    sql_statements: Dict[str, List[str]] = {
        "VISIT_OCCURRENCE": [],
        "CONDITION_OCCURRENCE": [],
        "MEASUREMENT": [],
        "DRUG_EXPOSURE": [],
        "OBSERVATION": [],
        "NOTE": [],
    }

    encounter_date = (
        encounter.created_at.strftime("%Y-%m-%d")
        if hasattr(encounter, "created_at") and encounter.created_at
        else datetime.utcnow().strftime("%Y-%m-%d")
    )
    encounter_datetime = (
        encounter.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(encounter, "created_at") and encounter.created_at
        else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    )

    # 1. VISIT_OCCURRENCE
    sql_statements["VISIT_OCCURRENCE"].append(
        f"""INSERT INTO visit_occurrence (
            visit_occurrence_id, person_id, visit_concept_id, visit_start_date,
            visit_start_datetime, visit_end_date, visit_end_datetime,
            visit_type_concept_id, provider_id, care_site_id,
            visit_source_value, visit_source_concept_id,
            admitted_from_concept_id, admitted_from_source_value,
            discharged_to_concept_id, discharged_to_source_value
        ) VALUES (
            {visit_occurrence_id}, {person_id}, 9202, '{encounter_date}',
            '{encounter_datetime}', '{encounter_date}', '{encounter_datetime}',
            44818517, 0, 0,
            'Integrum Encounter', 0,
            0, '', 0, ''
        );"""
    )

    # 2. CONDITIONS
    if hasattr(encounter, "conditions"):
        for condition in encounter.conditions:
            omop_cond = get_omop_condition_concept(condition.code)
            if omop_cond:
                concept_id, concept_name = omop_cond
            else:
                concept_id = 0  # No match found
                concept_name = condition.title or condition.code

            sql_statements["CONDITION_OCCURRENCE"].append(
                f"""INSERT INTO condition_occurrence (
                condition_occurrence_id, person_id, condition_concept_id,
                condition_start_date, condition_start_datetime,
                condition_end_date, condition_end_datetime,
                condition_type_concept_id, condition_status_concept_id,
                stop_reason, provider_id, visit_occurrence_id,
                condition_source_value, condition_source_concept_id
            ) VALUES (
                {encounter_id_counter}, {person_id}, {concept_id},
                '{encounter_date}', '{encounter_datetime}',
                NULL, NULL,
                32020, 32883,
                NULL, 0, {visit_occurrence_id},
                '{condition.code}', 0
            );"""
            )
        encounter_id_counter += 1

    # 3. OBSERVATIONS → MEASUREMENT
    for obs in encounter.observations:
        loinc_info = get_loinc_for_code(obs.code)
        if loinc_info:
            loinc_code, display, unit = loinc_info
        else:
            loinc_code = obs.code
            display = obs.code
            unit = obs.unit or ""

        omop_meas = get_omop_measurement_concept(loinc_code)
        if omop_meas:
            concept_id, concept_name = omop_meas
        else:
            concept_id = 0
            concept_name = display

        try:
            value_num = float(obs.value)
        except (ValueError, TypeError):
            value_num = None

        if value_num is not None:
            sql_statements["MEASUREMENT"].append(
                f"""INSERT INTO measurement (
                    measurement_id, person_id, measurement_concept_id,
                    measurement_date, measurement_datetime,
                    measurement_time, measurement_type_concept_id,
                    operator_concept_id, value_as_number, value_as_concept_id,
                    unit_concept_id, range_low, range_high, provider_id,
                    visit_occurrence_id, measurement_source_value,
                    measurement_source_concept_id, unit_source_value,
                    value_source_value
                ) VALUES (
                    {encounter_id_counter}, {person_id}, {concept_id},
                    '{encounter_date}', '{encounter_datetime}',
                    NULL, 44818702,
                    4172703, {value_num}, 0,
                    0, NULL, NULL, 0,
                    {visit_occurrence_id}, '{display}',
                    0, '{unit}', NULL
                );"""
            )
        encounter_id_counter += 1

    # 4. Calculated indices as MEASUREMENT
    calculated_indices = _get_calculated_indices(encounter)
    for calc_name, calc_value, calc_unit in calculated_indices:
        # Find LOINC code for this calculated index
        loinc_code = _get_loinc_for_calculated(calc_name)
        omop_meas = get_omop_measurement_concept(loinc_code) if loinc_code else None

        if omop_meas:
            concept_id, _ = omop_meas
        else:
            concept_id = 0  # No standard concept for calculated indices

        sql_statements["MEASUREMENT"].append(
            f"""INSERT INTO measurement (
                measurement_id, person_id, measurement_concept_id,
                measurement_date, measurement_datetime,
                measurement_type_concept_id, operator_concept_id,
                value_as_number, value_as_concept_id,
                unit_concept_id, provider_id, visit_occurrence_id,
                measurement_source_value, measurement_source_concept_id,
                unit_source_value
            ) VALUES (
                {encounter_id_counter}, {person_id}, {concept_id},
                '{encounter_date}', '{encounter_datetime}',
                44818702, 4172703,
                {calc_value}, 0,
                0, 0, {visit_occurrence_id},
                '{calc_name}', 0,
                '{calc_unit}'
            );"""
        )
        encounter_id_counter += 1

    # 5. MEDICATIONS → DRUG_EXPOSURE
    for med in encounter.medications:
        atc_info = get_atc_for_medication(med.name)
        if atc_info:
            atc_code, display, atc_class = atc_info
        else:
            atc_code = ""
            display = med.name
            atc_class = ""

        omop_drug = get_omop_drug_concept(atc_code) if atc_code else None
        if omop_drug:
            concept_id, _ = omop_drug
        else:
            concept_id = 0

        med_start = (
            med.start_date.strftime("%Y-%m-%d") if med.start_date else encounter_date
        )
        med_end = med.end_date.strftime("%Y-%m-%d") if med.end_date else None

        sql_statements["DRUG_EXPOSURE"].append(
            f"""INSERT INTO drug_exposure (
                drug_exposure_id, person_id, drug_concept_id,
                drug_exposure_start_date, drug_exposure_start_datetime,
                drug_exposure_end_date, drug_exposure_end_datetime,
                drug_type_concept_id, stop_reason, refills, quantity,
                days_supply, sig, route_concept_id,
                lot_number, provider_id, visit_occurrence_id,
                drug_source_value, drug_source_concept_id,
                route_source_value, dose_unit_source_value
            ) VALUES (
                {encounter_id_counter}, {person_id}, {concept_id},
                '{med_start}', '{encounter_datetime}',
                {f"'{med_end}'" if med_end else "NULL"}, {f"'{med_end}'" if med_end else "NULL"},
                38000177, NULL, 0, NULL,
                NULL, '{med.dose_amount or ""} {med.frequency or ""}', 0,
                '', 0, {visit_occurrence_id},
                '{display}', 0,
                '', '{med.dose_amount or ""}'
            );"""
        )
        encounter_id_counter += 1

    # 6. Psychometrics → OBSERVATION
    if hasattr(encounter, "psychometrics") and encounter.psychometrics:
        psych = encounter.psychometrics
        psych_mappings = [
            ("phq9_score", "PHQ-9", 44249),
            ("gad7_score", "GAD-7", 69737),
            ("tf_eq_uncontrolled_eating", "TFEQ Uncontrolled", 0),
            ("tf_eq_cognitive_restraint", "TFEQ Cognitive", 0),
            ("tf_eq_emotional_eating", "TFEQ Emotional", 0),
            ("atenas_insomnia_score", "Athens Insomnia", 72133),
            ("fnq_intrusive_thoughts", "FNQ Intrusive", 0),
            ("fnq_control_difficulty", "FNQ Control", 0),
        ]

        for attr, name, concept_id in psych_mappings:
            value = getattr(psych, attr, None)
            if value is not None:
                sql_statements["OBSERVATION"].append(
                    f"""INSERT INTO observation (
                        observation_id, person_id, observation_concept_id,
                        observation_date, observation_datetime,
                        observation_type_concept_id, value_as_number,
                        value_as_string, value_as_concept_id,
                        qualifier_concept_id, unit_concept_id,
                        provider_id, visit_occurrence_id,
                        observation_source_value, observation_source_concept_id,
                        unit_source_value, qualifier_source_value,
                        value_source_value, observation_event_id,
                        obs_event_field_concept_id
                    ) VALUES (
                        {encounter_id_counter}, {person_id}, {concept_id},
                        '{encounter_date}', '{encounter_datetime}',
                        45905771, {value},
                        NULL, 0,
                        0, 0,
                        0, {visit_occurrence_id},
                        '{name}', 0,
                        'score', NULL,
                        '{value}', 0, 0
                    );"""
                )
                encounter_id_counter += 1

    # 7. Clinical Notes → NOTE
    if encounter.clinical_notes or encounter.reason_for_visit:
        note_text = []
        if encounter.reason_for_visit:
            note_text.append(f"Reason: {encounter.reason_for_visit}")
        if encounter.clinical_notes:
            note_text.append(f"Notes: {encounter.clinical_notes}")

        sql_statements["NOTE"].append(
            f"""INSERT INTO note (
                note_id, person_id, note_date, note_datetime,
                note_type_concept_id, note_class_concept_id,
                note_title, note_text, encoding_concept_id,
                language_concept_id, provider_id, visit_occurrence_id
            ) VALUES (
                {encounter_id_counter}, {person_id}, '{encounter_date}',
                '{encounter_datetime}',
                44814638, 44814640,
                'Integrum Clinical Note',
                {" ".join(note_text)}',
                32678, 4180186, 0, {visit_occurrence_id}
            );"""
        )
        encounter_id_counter += 1

    return sql_statements


def _get_calculated_indices(encounter) -> List[tuple]:
    """Get calculated indices from encounter as (name, value, unit) tuples."""
    indices = []

    if encounter.bmi:
        indices.append(("BMI", encounter.bmi, "kg/m2"))
    if encounter.homa_ir:
        indices.append(("HOMA-IR", encounter.homa_ir, ""))
    if encounter.homa_b:
        indices.append(("HOMA-B", encounter.homa_b, "%"))
    if encounter.tyg_index:
        indices.append(("TyG Index", encounter.tyg_index, ""))
    if encounter.tyg_bmi:
        indices.append(("TyG-BMI", encounter.tyg_bmi, ""))
    if encounter.mets_ir:
        indices.append(("METS-IR", encounter.mets_ir, ""))
    if encounter.egfr_ckd_epi:
        indices.append(("eGFR CKD-EPI", encounter.egfr_ckd_epi, "mL/min/1.73m2"))
    if encounter.uacr:
        indices.append(("UACR", encounter.uacr, "mg/g"))
    if encounter.pulse_pressure:
        indices.append(("Pulse Pressure", encounter.pulse_pressure, "mmHg"))
    if encounter.mean_arterial_pressure:
        indices.append(("MAP", encounter.mean_arterial_pressure, "mmHg"))
    if encounter.remnant_cholesterol:
        indices.append(("Remnant Cholesterol", encounter.remnant_cholesterol, "mg/dL"))
    if encounter.aip:
        indices.append(("AIP", encounter.aip, ""))
    if encounter.castelli_index_i:
        indices.append(("Castelli I", encounter.castelli_index_i, ""))
    if encounter.castelli_index_ii:
        indices.append(("Castelli II", encounter.castelli_index_ii, ""))
    if encounter.apob_apoa1_ratio:
        indices.append(("ApoB/ApoA1 Ratio", encounter.apob_apoa1_ratio, ""))
    if encounter.non_hdl_cholesterol:
        indices.append(("Non-HDL Cholesterol", encounter.non_hdl_cholesterol, "mg/dL"))

    return indices


def _get_loinc_for_calculated(name: str) -> Optional[str]:
    """Get LOINC code for a calculated index name."""
    loinc_map = {
        "BMI": "39156-5",
        "HOMA-IR": "89242-2",
        "HOMA-B": "89242-3",
        "TyG Index": "89243-0",
        "TyG-BMI": "89244-8",
        "METS-IR": "89245-5",
        "eGFR CKD-EPI": "33914-3",
        "UACR": "14959-1",
        "Pulse Pressure": "8479-8",
        "MAP": "8480-6",
        "Remnant Cholesterol": "89248-9",
        "AIP": "89249-7",
        "Castelli I": "89250-5",
        "Castelli II": "89251-3",
        "ApoB/ApoA1 Ratio": "89252-1",
        "Non-HDL Cholesterol": "89253-9",
    }
    return loinc_map.get(name)
