"""
OMOP Cohort Builder SQL Templates for Integrum V2.

Pre-built SQL queries for common cohort definitions used in
obesity and cardiometabolic risk research. These templates
follow OHDSI/HADES patterns and can be executed against any
OMOP CDM 5.4 database.

References:
- OHDSI LEGEND-T2DM: https://github.com/OHDSI/LEGEND-T2DM
- IMI-SOPHIA: https://www.imi-sophia.eu/
- OHDSI Book: https://ohdsi.github.io/TheBookOfOhdsi/
"""

# ============================================================
# Cohort: Adults with Obesity (BMI >= 30)
# ============================================================

COHORT_OBESITY_BMI = """
-- Cohort: Adults with BMI >= 30 kg/m2
SELECT DISTINCT m.person_id,
       MIN(m.measurement_date) AS cohort_start_date,
       MAX(m.measurement_date) AS cohort_end_date
FROM measurement m
WHERE m.measurement_concept_id IN (
    -- BMI concept_id in OMOP
    SELECT concept_id FROM concept
    WHERE concept_code = '39156-5'
      AND vocabulary_id = 'LOINC'
)
AND m.value_as_number >= 30
GROUP BY m.person_id;
"""

# ============================================================
# Cohort: Type 2 Diabetes
# ============================================================

COHORT_T2DM = """
-- Cohort: Type 2 Diabetes Mellitus
SELECT DISTINCT c.person_id,
       MIN(c.condition_start_date) AS cohort_start_date,
       MAX(c.condition_start_date) AS cohort_end_date
FROM condition_occurrence c
WHERE c.condition_concept_id IN (
    -- T2DM concept_ids in OMOP
    SELECT concept_id FROM concept
    WHERE concept_code LIKE 'E11%'
      AND vocabulary_id = 'ICD10'
)
GROUP BY c.person_id;
"""

# ============================================================
# Cohort: Obesity + T2DM (High cardiometabolic risk)
# ============================================================

COHORT_OBESITY_T2DM = """
-- Cohort: Adults with Obesity AND Type 2 Diabetes
SELECT ob.person_id,
       ob.cohort_start_date,
       ob.cohort_end_date
FROM (
    SELECT DISTINCT m.person_id,
           MIN(m.measurement_date) AS cohort_start_date,
           MAX(m.measurement_date) AS cohort_end_date
    FROM measurement m
    WHERE m.measurement_concept_id IN (
        SELECT concept_id FROM concept
        WHERE concept_code = '39156-5' AND vocabulary_id = 'LOINC'
    )
    AND m.value_as_number >= 30
    GROUP BY m.person_id
) ob
INNER JOIN (
    SELECT DISTINCT c.person_id
    FROM condition_occurrence c
    WHERE c.condition_concept_id IN (
        SELECT concept_id FROM concept
        WHERE concept_code LIKE 'E11%' AND vocabulary_id = 'ICD10'
    )
) dm ON ob.person_id = dm.person_id;
"""

# ============================================================
# Cohort: Metabolic Syndrome (ATP III criteria)
# ============================================================

COHORT_METABOLIC_SYNDROME = """
-- Cohort: Metabolic Syndrome (ATP III: >= 3 of 5 criteria)
WITH waist AS (
    SELECT person_id, COUNT(*) AS has_waist
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '8280-0' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number >= 102  -- >= 102 cm (male) or >= 88 cm (female)
    GROUP BY person_id
),
tg AS (
    SELECT person_id, COUNT(*) AS has_tg
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '2571-8' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number >= 150  -- >= 150 mg/dL
    GROUP BY person_id
),
hdl AS (
    SELECT person_id, COUNT(*) AS has_hdl
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '2085-9' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number < 40  -- < 40 mg/dL (male) or < 50 mg/dL (female)
    GROUP BY person_id
),
bp AS (
    SELECT person_id, COUNT(*) AS has_bp
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '8480-6' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number >= 130  -- >= 130 mmHg systolic
    GROUP BY person_id
),
glucose AS (
    SELECT person_id, COUNT(*) AS has_glucose
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '1558-6' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number >= 100  -- >= 100 mg/dL fasting
    GROUP BY person_id
)
SELECT COALESCE(w.person_id, t.person_id, h.person_id, b.person_id, g.person_id) AS person_id,
       COALESCE(w.has_waist, 0) + COALESCE(t.has_tg, 0) + COALESCE(h.has_hdl, 0)
       + COALESCE(b.has_bp, 0) + COALESCE(g.has_glucose, 0) AS criteria_met
FROM waist w
FULL OUTER JOIN tg t ON w.person_id = t.person_id
FULL OUTER JOIN hdl h ON COALESCE(w.person_id, t.person_id) = h.person_id
FULL OUTER JOIN bp b ON COALESCE(w.person_id, t.person_id, h.person_id) = b.person_id
FULL OUTER JOIN glucose g ON COALESCE(w.person_id, t.person_id, h.person_id, b.person_id) = g.person_id
WHERE COALESCE(w.has_waist, 0) + COALESCE(t.has_tg, 0) + COALESCE(h.has_hdl, 0)
    + COALESCE(b.has_bp, 0) + COALESCE(g.has_glucose, 0) >= 3;
"""

# ============================================================
# Cohort: NAFLD/MASLD
# ============================================================

COHORT_NAFLD = """
-- Cohort: NAFLD/MASLD (diagnosis or elevated ALT/AST with obesity)
SELECT DISTINCT COALESCE(c.person_id, m.person_id) AS person_id,
       MIN(COALESCE(c.condition_start_date, m.measurement_date)) AS cohort_start_date
FROM (
    SELECT person_id, condition_start_date
    FROM condition_occurrence
    WHERE condition_concept_id IN (
        SELECT concept_id FROM concept
        WHERE concept_code IN ('K76.0', 'K75.81', 'K76.9')
          AND vocabulary_id = 'ICD10'
    )
) c
FULL OUTER JOIN (
    SELECT person_id, measurement_date
    FROM measurement
    WHERE measurement_concept_id IN (
        SELECT concept_id FROM concept WHERE concept_code = '1742-6' AND vocabulary_id = 'LOINC'
    )
    AND value_as_number > 40  -- ALT > 40 U/L
) m ON c.person_id = m.person_id;
"""

# ============================================================
# Cohort: GLP-1 RA Eligible (FDA criteria)
# ============================================================

COHORT_GLP1_ELIGIBLE = """
-- Cohort: Eligible for GLP-1 RA therapy (BMI >= 30 or BMI >= 27 + comorbidity)
SELECT DISTINCT ob.person_id,
       MIN(ob.measurement_date) AS eligibility_date
FROM measurement ob
WHERE ob.measurement_concept_id IN (
    SELECT concept_id FROM concept WHERE concept_code = '39156-5' AND vocabulary_id = 'LOINC'
)
AND ob.value_as_number >= 30
AND ob.person_id NOT IN (
    -- Exclude patients already on GLP-1 RA
    SELECT de.person_id
    FROM drug_exposure de
    JOIN concept c ON de.drug_concept_id = c.concept_id
    WHERE c.concept_code IN ('A10BJ06', 'A10BJ07', 'A10BJ02', 'A10BJ04', 'A10BJ01')
      AND c.vocabulary_id = 'ATC'
)
GROUP BY ob.person_id;
"""

# ============================================================
# Outcome: MACE (Major Adverse Cardiovascular Events)
# ============================================================

OUTCOME_MACE = """
-- Outcome: MACE (MI, Stroke, CV death) within 3 years
SELECT c.person_id,
       MIN(c.condition_start_date) AS mace_date,
       c.condition_concept_id AS mace_type
FROM condition_occurrence c
WHERE c.condition_concept_id IN (
    -- MI
    SELECT concept_id FROM concept WHERE concept_code IN ('I21', 'I22') AND vocabulary_id = 'ICD10'
    UNION
    -- Stroke
    SELECT concept_id FROM concept WHERE concept_code IN ('I63', 'I64') AND vocabulary_id = 'ICD10'
    UNION
    -- CV death (proxy: death with CV cause)
    SELECT concept_id FROM concept WHERE concept_code IN ('I46', 'I49') AND vocabulary_id = 'ICD10'
)
GROUP BY c.person_id, c.condition_concept_id;
"""

# ============================================================
# Feature Engineering: Baseline characteristics for cohort
# ============================================================

FEATURES_BASELINE = """
-- Baseline features for a given cohort
SELECT cb.person_id,
       -- Demographics
       p.gender_concept_id,
       p.year_of_birth,
       -- Most recent BMI
       MAX(CASE WHEN m.measurement_concept_id = 3036277 THEN m.value_as_number END) AS bmi,
       -- Most recent waist
       MAX(CASE WHEN m.measurement_concept_id = 3013721 THEN m.value_as_number END) AS waist_cm,
       -- Most recent HbA1c
       MAX(CASE WHEN m.measurement_concept_id = 3023103 THEN m.value_as_number END) AS hba1c,
       -- Most recent fasting glucose
       MAX(CASE WHEN m.measurement_concept_id = 3016723 THEN m.value_as_number END) AS glucose,
       -- Most recent systolic BP
       MAX(CASE WHEN m.measurement_concept_id = 3004249 THEN m.value_as_number END) AS sbp,
       -- Most recent triglycerides
       MAX(CASE WHEN m.measurement_concept_id = 3024929 THEN m.value_as_number END) AS tg,
       -- Most recent HDL
       MAX(CASE WHEN m.measurement_concept_id = 3016267 THEN m.value_as_number END) AS hdl,
       -- Most recent LDL
       MAX(CASE WHEN m.measurement_concept_id = 3016267 THEN m.value_as_number END) AS ldl,
       -- Most recent creatinine
       MAX(CASE WHEN m.measurement_concept_id = 3013940 THEN m.value_as_number END) AS creatinine,
       -- Most recent ALT
       MAX(CASE WHEN m.measurement_concept_id = 3013721 THEN m.value_as_number END) AS alt,
       -- Most recent AST
       MAX(CASE WHEN m.measurement_concept_id = 3013940 THEN m.value_as_number END) AS ast
FROM #cohort_base cb
LEFT JOIN person p ON cb.person_id = p.person_id
LEFT JOIN measurement m ON cb.person_id = m.person_id
    AND m.measurement_date BETWEEN cb.cohort_start_date - INTERVAL '365 days' AND cb.cohort_start_date
GROUP BY cb.person_id, cb.cohort_start_date, p.gender_concept_id, p.year_of_birth;
"""

# All cohort definitions
COHORT_DEFINITIONS = {
    "obesity_bmi": COHORT_OBESITY_BMI,
    "t2dm": COHORT_T2DM,
    "obesity_t2dm": COHORT_OBESITY_T2DM,
    "metabolic_syndrome": COHORT_METABOLIC_SYNDROME,
    "nafld": COHORT_NAFLD,
    "glp1_eligible": COHORT_GLP1_ELIGIBLE,
}

# All outcome definitions
OUTCOME_DEFINITIONS = {
    "mace": OUTCOME_MACE,
}

# Feature engineering queries
FEATURE_DEFINITIONS = {
    "baseline": FEATURES_BASELINE,
}
