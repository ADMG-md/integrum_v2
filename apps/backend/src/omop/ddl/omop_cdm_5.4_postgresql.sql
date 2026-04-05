-- OMOP CDM 5.4 DDL for PostgreSQL (Alpine)
-- Core clinical tables needed for Integrum V2 obesity/cardiometabolic CDSS
-- Based on OHDSI CDM specification: https://ohdsi.github.io/CommonDataModel/
-- Generated: 2026-04-04

-- ============================================================
-- PERSON
-- ============================================================
CREATE TABLE IF NOT EXISTS person (
    person_id             BIGINT          NOT NULL,
    gender_concept_id     BIGINT          NOT NULL,
    year_of_birth         INTEGER         NOT NULL,
    month_of_birth        INTEGER         NULL,
    day_of_birth          INTEGER         NULL,
    birth_datetime        TIMESTAMP       NULL,
    race_concept_id       BIGINT          NOT NULL,
    ethnicity_concept_id  BIGINT          NOT NULL,
    location_id           BIGINT          NULL,
    provider_id           BIGINT          NULL,
    care_site_id          BIGINT          NULL,
    person_source_value   VARCHAR(50)     NULL,
    gender_source_value   VARCHAR(50)     NULL,
    gender_source_concept_id  BIGINT      NULL,
    race_source_value     VARCHAR(50)     NULL,
    race_source_concept_id    BIGINT      NULL,
    ethnicity_source_value  VARCHAR(50)   NULL,
    ethnicity_source_concept_id BIGINT    NULL,
    CONSTRAINT pk_person PRIMARY KEY (person_id)
);

-- ============================================================
-- OBSERVATION_PERIOD
-- ============================================================
CREATE TABLE IF NOT EXISTS observation_period (
    observation_period_id     BIGINT          NOT NULL,
    person_id                 BIGINT          NOT NULL,
    observation_period_start_date     DATE    NOT NULL,
    observation_period_end_date       DATE    NOT NULL,
    period_type_concept_id    BIGINT          NOT NULL,
    CONSTRAINT pk_observation_period PRIMARY KEY (observation_period_id)
);

-- ============================================================
-- VISIT_OCCURRENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS visit_occurrence (
    visit_occurrence_id     BIGINT          NOT NULL,
    person_id               BIGINT          NOT NULL,
    visit_concept_id        BIGINT          NOT NULL,
    visit_start_date        DATE            NOT NULL,
    visit_start_datetime    TIMESTAMP       NULL,
    visit_end_date          DATE            NOT NULL,
    visit_end_datetime      TIMESTAMP       NULL,
    visit_type_concept_id   BIGINT          NOT NULL,
    provider_id             BIGINT          NULL,
    care_site_id            BIGINT          NULL,
    visit_source_value      VARCHAR(50)     NULL,
    visit_source_concept_id BIGINT          NULL,
    admitted_from_concept_id    BIGINT      NULL,
    admitted_from_source_value VARCHAR(50)  NULL,
    discharged_to_concept_id    BIGINT      NULL,
    discharged_to_source_value VARCHAR(50)  NULL,
    preceding_visit_occurrence_id BIGINT    NULL,
    CONSTRAINT pk_visit_occurrence PRIMARY KEY (visit_occurrence_id)
);

-- ============================================================
-- CONDITION_OCCURRENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS condition_occurrence (
    condition_occurrence_id     BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    condition_concept_id        BIGINT          NOT NULL,
    condition_start_date        DATE            NOT NULL,
    condition_start_datetime    TIMESTAMP       NULL,
    condition_end_date          DATE            NULL,
    condition_end_datetime      TIMESTAMP       NULL,
    condition_type_concept_id   BIGINT          NOT NULL,
    condition_status_concept_id BIGINT          NULL,
    stop_reason                 VARCHAR(20)     NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    condition_source_value      VARCHAR(50)     NULL,
    condition_source_concept_id BIGINT          NULL,
    condition_status_source_value VARCHAR(50)   NULL,
    CONSTRAINT pk_condition_occurrence PRIMARY KEY (condition_occurrence_id)
);

-- ============================================================
-- DRUG_EXPOSURE
-- ============================================================
CREATE TABLE IF NOT EXISTS drug_exposure (
    drug_exposure_id            BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    drug_concept_id             BIGINT          NOT NULL,
    drug_exposure_start_date    DATE            NOT NULL,
    drug_exposure_start_datetime TIMESTAMP      NULL,
    drug_exposure_end_date      DATE            NOT NULL,
    drug_exposure_end_datetime  TIMESTAMP       NULL,
    verbatim_end_date           DATE            NULL,
    drug_type_concept_id        BIGINT          NOT NULL,
    stop_reason                 VARCHAR(20)     NULL,
    refills                     INTEGER         NULL,
    quantity                    NUMERIC         NULL,
    days_supply                 INTEGER         NULL,
    sig                         TEXT            NULL,
    route_concept_id            BIGINT          NULL,
    lot_number                  VARCHAR(50)     NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    drug_source_value           VARCHAR(50)     NULL,
    drug_source_concept_id      BIGINT          NULL,
    route_source_value          VARCHAR(50)     NULL,
    dose_unit_source_value      VARCHAR(50)     NULL,
    CONSTRAINT pk_drug_exposure PRIMARY KEY (drug_exposure_id)
);

-- ============================================================
-- MEASUREMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS measurement (
    measurement_id              BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    measurement_concept_id      BIGINT          NOT NULL,
    measurement_date            DATE            NOT NULL,
    measurement_datetime        TIMESTAMP       NULL,
    measurement_time            VARCHAR(10)     NULL,
    measurement_type_concept_id BIGINT          NOT NULL,
    operator_concept_id         BIGINT          NULL,
    value_as_number             NUMERIC         NULL,
    value_as_concept_id         BIGINT          NULL,
    unit_concept_id             BIGINT          NULL,
    range_low                   NUMERIC         NULL,
    range_high                  NUMERIC         NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    measurement_source_value    VARCHAR(50)     NULL,
    measurement_source_concept_id BIGINT        NULL,
    unit_source_value           VARCHAR(50)     NULL,
    value_source_value          VARCHAR(50)     NULL,
    measurement_event_id        BIGINT          NULL,
    meas_event_field_concept_id BIGINT          NULL,
    CONSTRAINT pk_measurement PRIMARY KEY (measurement_id)
);

-- ============================================================
-- OBSERVATION
-- ============================================================
CREATE TABLE IF NOT EXISTS observation (
    observation_id              BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    observation_concept_id      BIGINT          NOT NULL,
    observation_date            DATE            NOT NULL,
    observation_datetime        TIMESTAMP       NULL,
    observation_type_concept_id BIGINT          NOT NULL,
    value_as_number             NUMERIC         NULL,
    value_as_string             VARCHAR(60)     NULL,
    value_as_concept_id         BIGINT          NULL,
    qualifier_concept_id        BIGINT          NULL,
    unit_concept_id             BIGINT          NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    observation_source_value    VARCHAR(50)     NULL,
    observation_source_concept_id BIGINT        NULL,
    unit_source_value           VARCHAR(50)     NULL,
    qualifier_source_value      VARCHAR(50)     NULL,
    value_source_value          VARCHAR(50)     NULL,
    observation_event_id        BIGINT          NULL,
    obs_event_field_concept_id  BIGINT          NULL,
    CONSTRAINT pk_observation PRIMARY KEY (observation_id)
);

-- ============================================================
-- DEATH
-- ============================================================
CREATE TABLE IF NOT EXISTS death (
    person_id                   BIGINT          NOT NULL,
    death_date                  DATE            NOT NULL,
    death_datetime              TIMESTAMP       NULL,
    death_type_concept_id       BIGINT          NULL,
    cause_concept_id            BIGINT          NULL,
    cause_source_value          VARCHAR(50)     NULL,
    cause_source_concept_id     BIGINT          NULL,
    CONSTRAINT pk_death PRIMARY KEY (person_id)
);

-- ============================================================
-- PROCEDURE_OCCURRENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS procedure_occurrence (
    procedure_occurrence_id     BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    procedure_concept_id        BIGINT          NOT NULL,
    procedure_date              DATE            NOT NULL,
    procedure_datetime          TIMESTAMP       NULL,
    procedure_end_date          DATE            NULL,
    procedure_end_datetime      TIMESTAMP       NULL,
    procedure_type_concept_id   BIGINT          NOT NULL,
    modifier_concept_id         BIGINT          NULL,
    quantity                    INTEGER         NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    procedure_source_value      VARCHAR(50)     NULL,
    procedure_source_concept_id BIGINT          NULL,
    modifier_source_value       VARCHAR(50)     NULL,
    CONSTRAINT pk_procedure_occurrence PRIMARY KEY (procedure_occurrence_id)
);

-- ============================================================
-- DEVICE_EXPOSURE
-- ============================================================
CREATE TABLE IF NOT EXISTS device_exposure (
    device_exposure_id          BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    device_concept_id           BIGINT          NOT NULL,
    device_exposure_start_date  DATE            NOT NULL,
    device_exposure_start_datetime TIMESTAMP    NULL,
    device_exposure_end_date    DATE            NULL,
    device_exposure_end_datetime TIMESTAMP      NULL,
    device_type_concept_id      BIGINT          NOT NULL,
    unique_device_id            VARCHAR(50)     NULL,
    production_id               VARCHAR(50)     NULL,
    quantity                    NUMERIC         NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    device_source_value         VARCHAR(50)     NULL,
    device_source_concept_id    BIGINT          NULL,
    unit_concept_id             BIGINT          NULL,
    unit_source_value           VARCHAR(50)     NULL,
    quantity_source_value       NUMERIC         NULL,
    CONSTRAINT pk_device_exposure PRIMARY KEY (device_exposure_id)
);

-- ============================================================
-- NOTE
-- ============================================================
CREATE TABLE IF NOT EXISTS note (
    note_id                     BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    note_date                   DATE            NOT NULL,
    note_datetime               TIMESTAMP       NULL,
    note_type_concept_id        BIGINT          NOT NULL,
    note_class_concept_id       BIGINT          NOT NULL,
    note_title                  VARCHAR(250)    NULL,
    note_text                   TEXT            NOT NULL,
    encoding_concept_id         BIGINT          NOT NULL,
    language_concept_id         BIGINT          NOT NULL,
    provider_id                 BIGINT          NULL,
    visit_occurrence_id         BIGINT          NULL,
    visit_detail_id             BIGINT          NULL,
    note_source_value           VARCHAR(50)     NULL,
    note_event_id               BIGINT          NULL,
    note_event_field_concept_id BIGINT          NULL,
    CONSTRAINT pk_note PRIMARY KEY (note_id)
);

-- ============================================================
-- COST
-- ============================================================
CREATE TABLE IF NOT EXISTS cost (
    cost_id                     BIGINT          NOT NULL,
    cost_event_id               BIGINT          NOT NULL,
    cost_domain_id              VARCHAR(20)     NOT NULL,
    cost_type_concept_id        BIGINT          NOT NULL,
    currency_concept_id         BIGINT          NULL,
    total_charge                NUMERIC         NULL,
    total_cost                  NUMERIC         NULL,
    total_paid                  NUMERIC         NULL,
    paid_by_payer               NUMERIC         NULL,
    paid_by_patient             NUMERIC         NULL,
    paid_patient_copay          NUMERIC         NULL,
    paid_patient_coinsurance    NUMERIC         NULL,
    paid_patient_deductible     NUMERIC         NULL,
    paid_by_primary             NUMERIC         NULL,
    paid_ingredient_cost        NUMERIC         NULL,
    paid_dispensing_fee         NUMERIC         NULL,
    payer_plan_period_id        BIGINT          NULL,
    amount_allowed              NUMERIC         NULL,
    revenue_code_concept_id     BIGINT          NULL,
    revenue_code_source_value   VARCHAR(50)     NULL,
    drg_concept_id              BIGINT          NULL,
    drg_source_value            VARCHAR(3)      NULL,
    CONSTRAINT pk_cost PRIMARY KEY (cost_id)
);

-- ============================================================
-- DRUG_ERA
-- ============================================================
CREATE TABLE IF NOT EXISTS drug_era (
    drug_era_id                 BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    drug_concept_id             BIGINT          NOT NULL,
    drug_era_start_date         DATE            NOT NULL,
    drug_era_end_date           DATE            NOT NULL,
    drug_exposure_count         INTEGER         NULL,
    gap_days                    INTEGER         NULL,
    CONSTRAINT pk_drug_era PRIMARY KEY (drug_era_id)
);

-- ============================================================
-- DOSE_ERA
-- ============================================================
CREATE TABLE IF NOT EXISTS dose_era (
    dose_era_id                 BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    drug_concept_id             BIGINT          NOT NULL,
    unit_concept_id             BIGINT          NOT NULL,
    dose_value                  NUMERIC         NOT NULL,
    dose_era_start_date         DATE            NOT NULL,
    dose_era_end_date           DATE            NOT NULL,
    CONSTRAINT pk_dose_era PRIMARY KEY (dose_era_id)
);

-- ============================================================
-- CONDITION_ERA
-- ============================================================
CREATE TABLE IF NOT EXISTS condition_era (
    condition_era_id            BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    condition_concept_id        BIGINT          NOT NULL,
    condition_era_start_date    DATE            NOT NULL,
    condition_era_end_date      DATE            NOT NULL,
    condition_occurrence_count  INTEGER         NULL,
    CONSTRAINT pk_condition_era PRIMARY KEY (condition_era_id)
);

-- ============================================================
-- EPISODE
-- ============================================================
CREATE TABLE IF NOT EXISTS episode (
    episode_id                  BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    episode_concept_id          BIGINT          NOT NULL,
    episode_start_date          DATE            NOT NULL,
    episode_start_datetime      TIMESTAMP       NULL,
    episode_end_date            DATE            NULL,
    episode_end_datetime        TIMESTAMP       NULL,
    episode_parent_id           BIGINT          NULL,
    episode_number              INTEGER         NULL,
    episode_object_concept_id   BIGINT          NOT NULL,
    episode_type_concept_id     BIGINT          NOT NULL,
    episode_source_value        VARCHAR(50)     NULL,
    episode_source_concept_id   BIGINT          NULL,
    CONSTRAINT pk_episode PRIMARY KEY (episode_id)
);

-- ============================================================
-- EPISODE_EVENT
-- ============================================================
CREATE TABLE IF NOT EXISTS episode_event (
    episode_id                  BIGINT          NOT NULL,
    event_id                    BIGINT          NOT NULL,
    episode_event_field_concept_id BIGINT       NOT NULL,
    CONSTRAINT pk_episode_event PRIMARY KEY (episode_id, event_id)
);

-- ============================================================
-- FACT_RELATIONSHIP
-- ============================================================
CREATE TABLE IF NOT EXISTS fact_relationship (
    domain_concept_id_1         BIGINT          NOT NULL,
    fact_id_1                   BIGINT          NOT NULL,
    domain_concept_id_2         BIGINT          NOT NULL,
    fact_id_2                   BIGINT          NOT NULL,
    relationship_concept_id     BIGINT          NOT NULL
);

-- ============================================================
-- LOCATION
-- ============================================================
CREATE TABLE IF NOT EXISTS location (
    location_id                 BIGINT          NOT NULL,
    address_1                   VARCHAR(50)     NULL,
    address_2                   VARCHAR(50)     NULL,
    city                        VARCHAR(50)     NULL,
    state                       VARCHAR(2)      NULL,
    zip                         VARCHAR(9)      NULL,
    county                      VARCHAR(20)     NULL,
    location_source_value       VARCHAR(50)     NULL,
    country_concept_id          BIGINT          NULL,
    country_source_value        VARCHAR(80)     NULL,
    latitude                    NUMERIC         NULL,
    longitude                   NUMERIC         NULL,
    CONSTRAINT pk_location PRIMARY KEY (location_id)
);

-- ============================================================
-- CARE_SITE
-- ============================================================
CREATE TABLE IF NOT EXISTS care_site (
    care_site_id                BIGINT          NOT NULL,
    care_site_name              VARCHAR(255)    NULL,
    place_of_service_concept_id BIGINT          NULL,
    location_id                 BIGINT          NULL,
    care_site_source_value      VARCHAR(50)     NULL,
    place_of_service_source_value VARCHAR(50)   NULL,
    CONSTRAINT pk_care_site PRIMARY KEY (care_site_id)
);

-- ============================================================
-- PROVIDER
-- ============================================================
CREATE TABLE IF NOT EXISTS provider (
    provider_id                 BIGINT          NOT NULL,
    provider_name               VARCHAR(255)    NULL,
    npi                         VARCHAR(20)     NULL,
    dea                         VARCHAR(20)     NULL,
    specialty_concept_id        BIGINT          NULL,
    care_site_id                BIGINT          NULL,
    year_of_birth               INTEGER         NULL,
    gender_concept_id           BIGINT          NULL,
    provider_source_value       VARCHAR(50)     NULL,
    specialty_source_value      VARCHAR(50)     NULL,
    specialty_source_concept_id BIGINT          NULL,
    gender_source_value         VARCHAR(50)     NULL,
    gender_source_concept_id    BIGINT          NULL,
    CONSTRAINT pk_provider PRIMARY KEY (provider_id)
);

-- ============================================================
-- PAYER_PLAN_PERIOD
-- ============================================================
CREATE TABLE IF NOT EXISTS payer_plan_period (
    payer_plan_period_id        BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    payer_plan_period_start_date DATE           NOT NULL,
    payer_plan_period_end_date  DATE            NOT NULL,
    payer_concept_id            BIGINT          NULL,
    payer_source_value          VARCHAR(50)     NULL,
    payer_source_concept_id     BIGINT          NULL,
    plan_concept_id             BIGINT          NULL,
    plan_source_value           VARCHAR(50)     NULL,
    plan_source_concept_id      BIGINT          NULL,
    sponsor_concept_id          BIGINT          NULL,
    sponsor_source_value        VARCHAR(50)     NULL,
    sponsor_source_concept_id   BIGINT          NULL,
    family_source_value         VARCHAR(50)     NULL,
    stop_reason_concept_id      BIGINT          NULL,
    stop_reason_source_value    VARCHAR(50)     NULL,
    stop_reason_source_concept_id BIGINT        NULL,
    CONSTRAINT pk_payer_plan_period PRIMARY KEY (payer_plan_period_id)
);

-- ============================================================
-- VISIT_DETAIL
-- ============================================================
CREATE TABLE IF NOT EXISTS visit_detail (
    visit_detail_id             BIGINT          NOT NULL,
    person_id                   BIGINT          NOT NULL,
    visit_detail_concept_id     BIGINT          NOT NULL,
    visit_detail_start_date     DATE            NOT NULL,
    visit_detail_start_datetime TIMESTAMP       NULL,
    visit_detail_end_date       DATE            NOT NULL,
    visit_detail_end_datetime   TIMESTAMP       NULL,
    visit_detail_type_concept_id BIGINT         NOT NULL,
    provider_id                 BIGINT          NULL,
    care_site_id                BIGINT          NULL,
    visit_detail_source_value   VARCHAR(50)     NULL,
    visit_detail_source_concept_id BIGINT       NULL,
    admitted_from_concept_id    BIGINT          NULL,
    admitted_from_source_value  VARCHAR(50)     NULL,
    discharged_to_source_value  VARCHAR(50)     NULL,
    discharged_to_concept_id    BIGINT          NULL,
    preceding_visit_detail_id   BIGINT          NULL,
    parent_visit_detail_id      BIGINT          NULL,
    visit_occurrence_id         BIGINT          NOT NULL,
    CONSTRAINT pk_visit_detail PRIMARY KEY (visit_detail_id)
);

-- ============================================================
-- CONCEPT
-- ============================================================
CREATE TABLE IF NOT EXISTS concept (
    concept_id                  BIGINT          NOT NULL,
    concept_name                VARCHAR(255)    NOT NULL,
    domain_id                   VARCHAR(20)     NOT NULL,
    vocabulary_id               VARCHAR(20)     NOT NULL,
    concept_class_id            VARCHAR(20)     NOT NULL,
    standard_concept            VARCHAR(1)      NULL,
    concept_code                VARCHAR(50)     NOT NULL,
    valid_start_date            DATE            NOT NULL,
    valid_end_date              DATE            NOT NULL,
    invalid_reason              VARCHAR(1)      NULL,
    CONSTRAINT pk_concept PRIMARY KEY (concept_id)
);

-- ============================================================
-- VOCABULARY
-- ============================================================
CREATE TABLE IF NOT EXISTS vocabulary (
    vocabulary_id               VARCHAR(20)     NOT NULL,
    vocabulary_name             VARCHAR(255)    NOT NULL,
    vocabulary_reference        VARCHAR(255)    NULL,
    vocabulary_version          VARCHAR(255)    NULL,
    vocabulary_concept_id       BIGINT          NOT NULL,
    CONSTRAINT pk_vocabulary PRIMARY KEY (vocabulary_id)
);

-- ============================================================
-- DOMAIN
-- ============================================================
CREATE TABLE IF NOT EXISTS domain (
    domain_id                   VARCHAR(20)     NOT NULL,
    domain_name                 VARCHAR(255)    NOT NULL,
    domain_concept_id           BIGINT          NOT NULL,
    CONSTRAINT pk_domain PRIMARY KEY (domain_id)
);

-- ============================================================
-- CONCEPT_CLASS
-- ============================================================
CREATE TABLE IF NOT EXISTS concept_class (
    concept_class_id            VARCHAR(20)     NOT NULL,
    concept_class_name          VARCHAR(255)    NOT NULL,
    concept_class_concept_id    BIGINT          NOT NULL,
    CONSTRAINT pk_concept_class PRIMARY KEY (concept_class_id)
);

-- ============================================================
-- CONCEPT_RELATIONSHIP
-- ============================================================
CREATE TABLE IF NOT EXISTS concept_relationship (
    concept_id_1                BIGINT          NOT NULL,
    concept_id_2                BIGINT          NOT NULL,
    relationship_id             VARCHAR(20)     NOT NULL,
    valid_start_date            DATE            NOT NULL,
    valid_end_date              DATE            NOT NULL,
    invalid_reason              VARCHAR(1)      NULL,
    CONSTRAINT pk_concept_relationship PRIMARY KEY (concept_id_1, concept_id_2, relationship_id)
);

-- ============================================================
-- RELATIONSHIP
-- ============================================================
CREATE TABLE IF NOT EXISTS relationship (
    relationship_id             VARCHAR(20)     NOT NULL,
    relationship_name           VARCHAR(255)    NOT NULL,
    is_hierarchical             VARCHAR(1)      NOT NULL,
    defines_ancestry            VARCHAR(1)      NOT NULL,
    reverse_relationship_id     VARCHAR(20)     NOT NULL,
    relationship_concept_id     BIGINT          NOT NULL,
    CONSTRAINT pk_relationship PRIMARY KEY (relationship_id)
);

-- ============================================================
-- CONCEPT_SYNONYM
-- ============================================================
CREATE TABLE IF NOT EXISTS concept_synonym (
    concept_id                  BIGINT          NOT NULL,
    concept_synonym_name        VARCHAR(1000)   NOT NULL,
    language_concept_id         BIGINT          NOT NULL,
    CONSTRAINT pk_concept_synonym PRIMARY KEY (concept_id, concept_synonym_name, language_concept_id)
);

-- ============================================================
-- CONCEPT_ANCESTOR
-- ============================================================
CREATE TABLE IF NOT EXISTS concept_ancestor (
    ancestor_concept_id         BIGINT          NOT NULL,
    descendant_concept_id       BIGINT          NOT NULL,
    min_levels_of_separation    INTEGER         NOT NULL,
    max_levels_of_separation    INTEGER         NOT NULL,
    CONSTRAINT pk_concept_ancestor PRIMARY KEY (ancestor_concept_id, descendant_concept_id)
);

-- ============================================================
-- SOURCE_TO_CONCEPT_MAP
-- ============================================================
CREATE TABLE IF NOT EXISTS source_to_concept_map (
    source_code                 VARCHAR(50)     NOT NULL,
    source_concept_id           BIGINT          NOT NULL,
    source_vocabulary_id        VARCHAR(20)     NOT NULL,
    source_code_description     VARCHAR(255)    NULL,
    target_concept_id           BIGINT          NOT NULL,
    target_vocabulary_id        VARCHAR(20)     NOT NULL,
    valid_start_date            DATE            NOT NULL,
    valid_end_date              DATE            NOT NULL,
    invalid_reason              VARCHAR(1)      NULL,
    CONSTRAINT pk_source_to_concept_map PRIMARY KEY (source_code, source_vocabulary_id, target_concept_id)
);

-- ============================================================
-- DRUG_STRENGTH
-- ============================================================
CREATE TABLE IF NOT EXISTS drug_strength (
    drug_concept_id             BIGINT          NOT NULL,
    ingredient_concept_id       BIGINT          NOT NULL,
    amount_value                NUMERIC         NULL,
    amount_unit_concept_id      BIGINT          NULL,
    numerator_value             NUMERIC         NULL,
    numerator_unit_concept_id   BIGINT          NULL,
    denominator_value           NUMERIC         NULL,
    denominator_unit_concept_id BIGINT          NULL,
    box_size                    INTEGER         NULL,
    valid_start_date            DATE            NOT NULL,
    valid_end_date              DATE            NOT NULL,
    invalid_reason              VARCHAR(1)      NULL,
    CONSTRAINT pk_drug_strength PRIMARY KEY (drug_concept_id, ingredient_concept_id)
);

-- ============================================================
-- COHORT (OHDSI standard)
-- ============================================================
CREATE TABLE IF NOT EXISTS cohort (
    cohort_definition_id        BIGINT          NOT NULL,
    subject_id                  BIGINT          NOT NULL,
    cohort_start_date           DATE            NOT NULL,
    cohort_end_date             DATE            NOT NULL,
    CONSTRAINT pk_cohort PRIMARY KEY (cohort_definition_id, subject_id)
);

-- ============================================================
-- COHORT_DEFINITION
-- ============================================================
CREATE TABLE IF NOT EXISTS cohort_definition (
    cohort_definition_id        BIGINT          NOT NULL,
    cohort_definition_name      VARCHAR(255)    NOT NULL,
    cohort_definition_description TEXT          NULL,
    definition_type_concept_id  BIGINT          NOT NULL,
    cohort_definition_syntax    TEXT            NULL,
    subject_concept_id          BIGINT          NOT NULL,
    cohort_initiation_date      DATE            NULL,
    CONSTRAINT pk_cohort_definition PRIMARY KEY (cohort_definition_id)
);

-- ============================================================
-- Indexes for common query patterns (Integrum V2)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_person_gender ON person (gender_concept_id);
CREATE INDEX IF NOT EXISTS idx_person_year_of_birth ON person (year_of_birth);

CREATE INDEX IF NOT EXISTS idx_observation_period_person ON observation_period (person_id);

CREATE INDEX IF NOT EXISTS idx_visit_person ON visit_occurrence (person_id);
CREATE INDEX IF NOT EXISTS idx_visit_concept ON visit_occurrence (visit_concept_id);
CREATE INDEX IF NOT EXISTS idx_visit_start ON visit_occurrence (visit_start_date);

CREATE INDEX IF NOT EXISTS idx_condition_person ON condition_occurrence (person_id);
CREATE INDEX IF NOT EXISTS idx_condition_concept ON condition_occurrence (condition_concept_id);
CREATE INDEX IF NOT EXISTS idx_condition_start ON condition_occurrence (condition_start_date);
CREATE INDEX IF NOT EXISTS idx_condition_source ON condition_occurrence (condition_source_value);

CREATE INDEX IF NOT EXISTS idx_drug_person ON drug_exposure (person_id);
CREATE INDEX IF NOT EXISTS idx_drug_concept ON drug_exposure (drug_concept_id);
CREATE INDEX IF NOT EXISTS idx_drug_start ON drug_exposure (drug_exposure_start_date);
CREATE INDEX IF NOT EXISTS idx_drug_source ON drug_exposure (drug_source_value);

CREATE INDEX IF NOT EXISTS idx_measurement_person ON measurement (person_id);
CREATE INDEX IF NOT EXISTS idx_measurement_concept ON measurement (measurement_concept_id);
CREATE INDEX IF NOT EXISTS idx_measurement_date ON measurement (measurement_date);
CREATE INDEX IF NOT EXISTS idx_measurement_source ON measurement (measurement_source_value);

CREATE INDEX IF NOT EXISTS idx_observation_person ON observation (person_id);
CREATE INDEX IF NOT EXISTS idx_observation_concept ON observation (observation_concept_id);
CREATE INDEX IF NOT EXISTS idx_observation_date ON observation (observation_date);
CREATE INDEX IF NOT EXISTS idx_observation_source ON observation (observation_source_value);

CREATE INDEX IF NOT EXISTS idx_cohort_definition ON cohort (cohort_definition_id);
CREATE INDEX IF NOT EXISTS idx_cohort_subject ON cohort (subject_id);
CREATE INDEX IF NOT EXISTS idx_cohort_start ON cohort (cohort_start_date);

CREATE INDEX IF NOT EXISTS idx_concept_code ON concept (concept_code);
CREATE INDEX IF NOT EXISTS idx_concept_domain ON concept (domain_id);
CREATE INDEX IF NOT EXISTS idx_concept_vocab ON concept (vocabulary_id);
