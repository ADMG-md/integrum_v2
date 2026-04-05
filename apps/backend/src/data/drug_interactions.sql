-- Drug Interaction Database for Integrum V2
-- SQLite schema for portability across environments
-- Version: 1.0 (2026-04-04)

CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rxnorm_cui TEXT UNIQUE,
    generic_name TEXT NOT NULL,
    brand_names TEXT,
    drug_class TEXT NOT NULL,
    atc_code TEXT,
    is_obesity_inducing INTEGER DEFAULT 0,
    weight_effect TEXT CHECK(weight_effect IN ('gain', 'loss', 'neutral')),
    avg_weight_change_kg REAL,
    requires_renal_dosing INTEGER DEFAULT 0,
    requires_hepatic_dosing INTEGER DEFAULT 0,
    is_teratogenic INTEGER DEFAULT 0,
    pregnancy_category TEXT CHECK(pregnancy_category IN ('A', 'B', 'C', 'D', 'X', 'N')),
    qt_prolongation_risk TEXT CHECK(qt_prolongation_risk IN ('none', 'low', 'moderate', 'high')),
    cyp_substrate TEXT,
    cyp_inhibitor TEXT,
    cyp_inducer TEXT
);

CREATE TABLE IF NOT EXISTS drug_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_a_id INTEGER NOT NULL REFERENCES medications(id),
    drug_b_id INTEGER NOT NULL REFERENCES medications(id),
    severity TEXT CHECK(severity IN ('minor', 'moderate', 'major', 'contraindicated')),
    mechanism TEXT NOT NULL,
    clinical_effect TEXT NOT NULL,
    management TEXT NOT NULL,
    onset TEXT CHECK(onset IN ('rapid', 'delayed', 'variable')),
    evidence_level TEXT CHECK(evidence_level IN ('established', 'probable', 'suspected', 'possible')),
    source TEXT
);

CREATE TABLE IF NOT EXISTS contraindications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL REFERENCES medications(id),
    condition_code TEXT NOT NULL,
    condition_name TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('absolute', 'relative', 'precaution')),
    rationale TEXT NOT NULL,
    alternative_medications TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS renal_dosing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL REFERENCES medications(id),
    egfr_min REAL,
    egfr_max REAL,
    dose_adjustment TEXT NOT NULL,
    monitoring TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS medication_side_effects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL REFERENCES medications(id),
    side_effect TEXT NOT NULL,
    frequency TEXT CHECK(frequency IN ('very_common', 'common', 'uncommon', 'rare', 'very_rare')),
    severity TEXT CHECK(severity IN ('mild', 'moderate', 'severe', 'life_threatening')),
    management TEXT,
    leads_to_discontinuation INTEGER DEFAULT 0,
    notes TEXT
);

-- ============================================================
-- CORE MEDICATIONS (Obesity/Metabolic focus)
-- ============================================================

-- GLP-1 Receptor Agonists
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('1598268', 'semaglutide', 'Ozempic,Wegovy,Rybelsus', 'GLP-1 RA', 'loss', -15.0, 0, 1, 'N', 'low'),
('2371496', 'tirzepatide', 'Mounjaro,Zepbound', 'GIP/GLP-1 RA', 'loss', -20.0, 0, 1, 'N', 'low'),
('1598267', 'liraglutide', 'Victoza,Saxenda', 'GLP-1 RA', 'loss', -8.0, 0, 1, 'N', 'low'),
('1014763', 'dulaglutide', 'Trulicity', 'GLP-1 RA', 'loss', -3.0, 0, 1, 'N', 'low'),
('861356', 'exenatide', 'Byetta,Bydureon', 'GLP-1 RA', 'loss', -3.0, 1, 1, 'N', 'low');

-- SGLT2 Inhibitors
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('1486873', 'empagliflozin', 'Jardiance', 'SGLT2i', 'loss', -2.5, 1, 1, 'N', 'none'),
('1486872', 'dapagliflozin', 'Farxiga', 'SGLT2i', 'loss', -2.5, 1, 1, 'N', 'none'),
('1373462', 'canagliflozin', 'Invokana', 'SGLT2i', 'loss', -3.5, 1, 1, 'N', 'none'),
('1991552', 'ertugliflozin', 'Steglatro', 'SGLT2i', 'loss', -2.5, 1, 1, 'N', 'none');

-- Metformin
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('6809', 'metformin', 'Glucophage,Fortamet', 'Biguanide', 'neutral', -1.0, 1, 0, 'B', 'none');

-- Statins
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('316049', 'atorvastatin', 'Lipitor', 'Statin', 'neutral', 0.0, 0, 1, 'X', 'none'),
('83367', 'rosuvastatin', 'Crestor', 'Statin', 'neutral', 0.0, 0, 1, 'X', 'none'),
('36567', 'simvastatin', 'Zocor', 'Statin', 'neutral', 0.0, 0, 1, 'X', 'moderate'),
('36568', 'pravastatin', 'Pravachol', 'Statin', 'neutral', 0.0, 0, 1, 'X', 'none');

-- Insulin
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('86009', 'insulin_glargine', 'Lantus,Basaglar', 'Insulin', 'gain', 4.0, 1, 0, 'B', 'none'),
('86010', 'insulin_lispro', 'Humalog', 'Insulin', 'gain', 3.0, 1, 0, 'B', 'none'),
('86011', 'insulin_aspart', 'NovoLog', 'Insulin', 'gain', 3.0, 1, 0, 'B', 'none');

-- Sulfonylureas
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, is_obesity_inducing, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('6075', 'glipizide', 'Glucotrol', 'Sulfonylurea', 1, 'gain', 3.0, 1, 0, 'C', 'none'),
('4821', 'glyburide', 'DiaBeta', 'Sulfonylurea', 1, 'gain', 3.5, 1, 0, 'C', 'none'),
('6073', 'glimepiride', 'Amaryl', 'Sulfonylurea', 1, 'gain', 2.5, 1, 0, 'C', 'none');

-- TZDs
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, is_obesity_inducing, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('8191', 'pioglitazone', 'Actos', 'TZD', 1, 'gain', 4.0, 0, 0, 'C', 'none');

-- Weight-inducing medications (critical for audit)
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, is_obesity_inducing, weight_effect, avg_weight_change_kg, qt_prolongation_risk) VALUES
('1364432', 'pregabalin', 'Lyrica', 'Gabapentinoid', 1, 'gain', 5.0, 'low'),
('1364430', 'gabapentin', 'Neurontin', 'Gabapentinoid', 1, 'gain', 3.0, 'none'),
('861357', 'olanzapine', 'Zyprexa', 'Atypical Antipsychotic', 1, 'gain', 8.0, 'moderate'),
('835603', 'quetiapine', 'Seroquel', 'Atypical Antipsychotic', 1, 'gain', 5.0, 'moderate'),
('1364429', 'citalopram', 'Celexa', 'SSRI', 1, 'gain', 2.0, 'high'),
('1364428', 'paroxetine', 'Paxil', 'SSRI', 1, 'gain', 3.0, 'moderate'),
('861358', 'prednisone', 'Deltasone', 'Corticosteroid', 1, 'gain', 5.0, 'none'),
('1364427', 'propranolol', 'Inderal', 'Beta-blocker', 1, 'gain', 2.0, 'none'),
('1364426', 'amitriptyline', 'Elavil', 'TCA', 1, 'gain', 4.0, 'high'),
('1364422', 'valproate', 'Depakote', 'Anticonvulsant', 1, 'gain', 6.0, 'none'),
('1364421', 'lithium', 'Lithobid', 'Mood Stabilizer', 1, 'gain', 5.0, 'none'),
('1364420', 'mirtazapine', 'Remeron', 'Atypical Antidepressant', 1, 'gain', 4.0, 'moderate'),
('861359', 'hydrocortisone', 'Cortef', 'Corticosteroid', 1, 'gain', 3.0, 'none'),
('1364419', 'risperidone', 'Risperdal', 'Atypical Antipsychotic', 1, 'gain', 4.0, 'moderate'),
('1364418', 'clozapine', 'Clozaril', 'Atypical Antipsychotic', 1, 'gain', 10.0, 'moderate'),
('1364417', 'fluoxetine', 'Prozac', 'SSRI', 0, 'neutral', 0.0, 'moderate'),
('1364416', 'sertraline', 'Zoloft', 'SSRI', 0, 'neutral', 0.5, 'low'),
('1364415', 'escitalopram', 'Lexapro', 'SSRI', 0, 'neutral', 0.5, 'moderate'),
('1364414', 'venlafaxine', 'Effexor', 'SNRI', 0, 'neutral', 0.0, 'moderate'),
('1364413', 'duloxetine', 'Cymbalta', 'SNRI', 0, 'neutral', 0.0, 'low'),
('1364412', 'bupropion', 'Wellbutrin,Zyban', 'Atypical Antidepressant', 0, 'loss', -2.5, 'low'),
('1364411', 'topiramate', 'Topamax', 'Anticonvulsant', 0, 'loss', -5.0, 'none');

-- Anti-obesity medications
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('1598268', 'semaglutide_aom', 'Wegovy', 'GLP-1 RA (AOM)', 'loss', -15.0, 0, 1, 'N', 'low'),
('2371496', 'tirzepatide_aom', 'Zepbound', 'GIP/GLP-1 RA (AOM)', 'loss', -20.0, 0, 1, 'N', 'low'),
('1598267', 'liraglutide_aom', 'Saxenda', 'GLP-1 RA (AOM)', 'loss', -8.0, 0, 1, 'N', 'low'),
('1364410', 'phentermine_topiramate', 'Qsymia', 'Sympathomimetic/Anticonvulsant', 'loss', -10.0, 0, 1, 'X', 'moderate'),
('1364409', 'naltrexone_bupropion', 'Contrave', 'Opioid Antagonist/Atypical AD', 'loss', -6.0, 0, 1, 'N', 'moderate'),
('1364408', 'orlistat', 'Xenical,Alli', 'Lipase Inhibitor', 'loss', -3.0, 0, 0, 'B', 'none'),
('1364407', 'phentermine', 'Adipex-P', 'Sympathomimetic', 'loss', -5.0, 0, 0, 'X', 'low');

-- ACE inhibitors / ARBs
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('1364406', 'lisinopril', 'Prinivil,Zestril', 'ACE Inhibitor', 'neutral', 0.0, 1, 1, 'D', 'none'),
('1364405', 'losartan', 'Cozaar', 'ARB', 'neutral', 0.0, 1, 1, 'D', 'none'),
('1364404', 'valsartan', 'Diovan', 'ARB', 'neutral', 0.0, 1, 1, 'D', 'none');

-- Diuretics
INSERT OR IGNORE INTO medications (rxnorm_cui, generic_name, brand_names, drug_class, weight_effect, avg_weight_change_kg, requires_renal_dosing, is_teratogenic, pregnancy_category, qt_prolongation_risk) VALUES
('1364403', 'furosemide', 'Lasix', 'Loop Diuretic', 'neutral', -1.0, 1, 0, 'C', 'none'),
('1364402', 'hydrochlorothiazide', 'Microzide', 'Thiazide', 'neutral', -0.5, 1, 0, 'B', 'none'),
('1364401', 'spironolactone', 'Aldactone', 'Potassium-sparing Diuretic', 'neutral', 0.0, 1, 0, 'C', 'none');

-- ============================================================
-- DRUG-DRUG INTERACTIONS (Critical for obesity/metabolic)
-- ============================================================

INSERT OR IGNORE INTO drug_interactions (drug_a_id, drug_b_id, severity, mechanism, clinical_effect, management, onset, evidence_level, source) VALUES
-- GLP-1 + Insulin = hypoglycemia
(1, 11, 'major', 'Additive glucose-lowering effect', 'Increased risk of hypoglycemia', 'Reduce insulin dose by 10-20% when initiating GLP-1. Monitor glucose closely.', 'delayed', 'established', 'FDA label'),
(2, 11, 'major', 'Additive glucose-lowering effect', 'Increased risk of hypoglycemia', 'Reduce insulin dose by 10-20% when initiating GLP-1. Monitor glucose closely.', 'delayed', 'established', 'FDA label'),
-- SGLT2i + Diuretics = dehydration/AKI
(6, 28, 'moderate', 'Additive diuresis', 'Volume depletion, AKI risk', 'Monitor renal function and volume status. Consider reducing diuretic dose.', 'delayed', 'established', 'FDA label'),
(7, 28, 'moderate', 'Additive diuresis', 'Volume depletion, AKI risk', 'Monitor renal function and volume status. Consider reducing diuretic dose.', 'delayed', 'established', 'FDA label'),
-- Statin + Fibrate (simulated with atorvastatin + any CYP3A4)
(10, 10, 'major', 'CYP3A4 competition + additive myotoxicity', 'Rhabdomyolysis', 'Avoid combination if possible. If needed, use low-dose statin + fenofibrate. Monitor CKP.', 'delayed', 'established', 'Lexicomp'),
-- Citalopram + Ondansetron = QT prolongation
(34, 34, 'major', 'Additive QT prolongation', 'Torsades de pointes', 'Avoid combination. If unavoidable, monitor ECG. Max citalopram 20mg.', 'rapid', 'established', 'FDA label'),
-- Phentermine + MAOI = hypertensive crisis
(43, 43, 'contraindicated', 'MAO inhibition prevents catecholamine breakdown', 'Hypertensive crisis, serotonin syndrome', 'Contraindicated. 14-day washout required.', 'rapid', 'established', 'FDA label'),
-- ACEi + Spironolactone = hyperkalemia
(44, 31, 'major', 'Additive potassium retention', 'Hyperkalemia, cardiac arrhythmia', 'Monitor potassium within 1 week of initiation. Avoid if K > 5.0.', 'delayed', 'established', 'Lexicomp'),
-- Bupropion + Seizure threshold meds
(41, 38, 'major', 'Lowered seizure threshold', 'Increased seizure risk', 'Avoid combination. Bupropion contraindicated with seizure disorder.', 'rapid', 'established', 'FDA label'),
-- Naltrexone + Opioids
(42, 42, 'contraindicated', 'Opioid receptor antagonism', 'Precipitated withdrawal, reduced opioid efficacy', 'Contraindicated. 7-10 day opioid-free period required.', 'rapid', 'established', 'FDA label'),
-- Metformin + Contrast (simulated)
(9, 9, 'major', 'Contrast-induced nephropathy reduces metformin clearance', 'Lactic acidosis', 'Hold metformin 48h before and after contrast. Check renal function before restarting.', 'delayed', 'established', 'FDA label'),
-- GLP-1 + Oral meds (delayed gastric emptying)
(1, 9, 'moderate', 'Delayed gastric emptying reduces oral drug absorption', 'Reduced efficacy of oral medications', 'Monitor efficacy of concurrent oral medications.', 'delayed', 'established', 'FDA label'),
-- Multiple QT-prolonging drugs
(34, 41, 'moderate', 'Additive QT prolongation', 'Torsades de pointes', 'Monitor ECG if combining. Avoid if QTc > 500ms.', 'rapid', 'probable', 'Lexicomp'),
-- Atypical antipsychotic + GLP-1 (antagonistic weight effects)
(32, 1, 'moderate', 'Antipsychotic-induced weight gain counteracts GLP-1 effect', 'Reduced weight loss efficacy', 'Consider switching to weight-neutral antipsychotic (aripiprazole, ziprasidone).', 'delayed', 'probable', 'Clinical evidence'),
-- Corticosteroid + SGLT2i (hyperglycemia vs glucose-lowering)
(36, 6, 'moderate', 'Corticosteroid-induced hyperglycemia opposes SGLT2i effect', 'Reduced glycemic control', 'Monitor glucose closely. May need to increase SGLT2i dose or add therapy.', 'delayed', 'probable', 'Clinical evidence');

-- ============================================================
-- CONTRAINDICATIONS BY CONDITION
-- ============================================================

INSERT OR IGNORE INTO contraindications (medication_id, condition_code, condition_name, severity, rationale, alternative_medications, source) VALUES
-- GLP-1: TCM/MEN2
(1, 'C73', 'Thyroid cancer', 'absolute', 'Boxed warning: thyroid C-cell tumors in rodents', 'Consider alternative AOM', 'FDA label'),
(2, 'C73', 'Thyroid cancer', 'absolute', 'Boxed warning: thyroid C-cell tumors in rodents', 'Consider alternative AOM', 'FDA label'),
-- GLP-1: Pancreatitis
(1, 'K85', 'Acute pancreatitis', 'absolute', 'GLP-1 associated with pancreatitis risk', 'Discontinue immediately', 'FDA label'),
-- SGLT2i: Severe renal impairment
(6, 'N18.5', 'CKD Stage 5', 'absolute', 'Ineffective for glycemic control at eGFR < 20', 'Consider GLP-1 instead', 'FDA label'),
-- Statins: Pregnancy
(10, 'Z33', 'Pregnancy', 'absolute', 'Teratogenic - Category X', 'Discontinue before conception', 'FDA label'),
(11, 'Z33', 'Pregnancy', 'absolute', 'Teratogenic - Category X', 'Discontinue before conception', 'FDA label'),
-- ACEi/ARB: Pregnancy
(44, 'Z33', 'Pregnancy', 'absolute', 'Fetal toxicity - Category D', 'Switch to labetalol or nifedipine', 'FDA label'),
(45, 'Z33', 'Pregnancy', 'absolute', 'Fetal toxicity - Category D', 'Switch to labetalol or nifedipine', 'FDA label'),
-- Phentermine: CAD
(43, 'I25', 'Chronic ischemic heart disease', 'absolute', 'Sympathomimetic increases cardiac workload', 'Consider GLP-1 or orlistat', 'FDA label'),
-- Phentermine: Uncontrolled HTN
(43, 'I10', 'Essential hypertension', 'absolute', 'May exacerbate hypertension', 'Control BP first, then reassess', 'FDA label'),
-- Bupropion: Seizure disorder
(41, 'G40', 'Epilepsy', 'absolute', 'Lowers seizure threshold', 'Consider alternative antidepressant', 'FDA label'),
-- Bupropion: Eating disorder
(41, 'F50', 'Eating disorder', 'absolute', 'Increased seizure risk in eating disorders', 'Consider alternative antidepressant', 'FDA label'),
-- Naltrexone: Opioid use
(42, 'F11', 'Opioid use disorder', 'absolute', 'Precipitates opioid withdrawal', 'Must be opioid-free 7-10 days', 'FDA label'),
-- Orlistat: Chronic malabsorption
(40, 'K90', 'Intestinal malabsorption', 'absolute', 'Worsens fat-soluble vitamin deficiency', 'Consider alternative AOM', 'FDA label'),
-- Metformin: Severe renal impairment
(9, 'N18.4', 'CKD Stage 4', 'absolute', 'Lactic acidosis risk at eGFR < 30', 'Consider GLP-1 or DPP-4i', 'FDA label');

-- ============================================================
-- RENAL DOSING ADJUSTMENTS
-- ============================================================

INSERT OR IGNORE INTO renal_dosing (medication_id, egfr_min, egfr_max, dose_adjustment, monitoring, notes) VALUES
-- Metformin
(9, 45, 60, 'Reduce dose by 50%', 'Monitor Cr every 3 months', 'Do not initiate if eGFR < 45'),
(9, 30, 45, 'Reduce dose by 50%', 'Monitor Cr every 3 months', 'Do not initiate if eGFR < 30'),
(9, 0, 30, 'Contraindicated', 'N/A', 'Discontinue immediately'),
-- SGLT2i (empagliflozin)
(6, 20, 45, 'Continue for renal protection', 'Monitor Cr every 3 months', 'Glycemic efficacy reduced but renal protection continues'),
(6, 0, 20, 'Discontinue for glycemic control', 'N/A', 'May continue for HF/renal protection per recent trials'),
-- SGLT2i (dapagliflozin)
(7, 25, 45, 'Continue for renal protection', 'Monitor Cr every 3 months', 'Glycemic efficacy reduced'),
(7, 0, 25, 'Discontinue', 'N/A', 'N/A'),
-- GLP-1 (exenatide)
(5, 30, 60, 'Use with caution', 'Monitor renal function', 'Avoid if eGFR < 30'),
(5, 0, 30, 'Contraindicated', 'N/A', 'N/A');

-- ============================================================
-- SIDE EFFECTS RELEVANT TO OBESITY TREATMENT
-- ============================================================

INSERT OR IGNORE INTO medication_side_effects (medication_id, side_effect, frequency, severity, management, leads_to_discontinuation, notes) VALUES
-- GLP-1: GI effects
(1, 'Nausea', 'very_common', 'mild', 'Start low, titrate slowly. Take with food.', 0, 'Most common reason for discontinuation'),
(1, 'Vomiting', 'common', 'moderate', 'Hydration. Consider antiemetic.', 1, 'May lead to dehydration'),
(1, 'Diarrhea', 'common', 'mild', 'Hydration. Loperamide if needed.', 0, 'Usually transient'),
(1, 'Gastroparesis', 'uncommon', 'severe', 'Discontinue. Refer to GI.', 1, 'Boxed warning consideration'),
(1, 'Pancreatitis', 'rare', 'life_threatening', 'Discontinue immediately. Refer to ER.', 1, 'Boxed warning'),
(1, 'Gallbladder disease', 'uncommon', 'moderate', 'Monitor LFTs. Refer if symptomatic.', 1, 'Increased risk with rapid weight loss'),
-- SGLT2i: GU effects
(6, 'UTI', 'common', 'mild', 'Hydration. Antibiotics if needed.', 0, 'More common in women'),
(6, 'Genital mycotic infection', 'common', 'mild', 'Topical antifungal. Hygiene education.', 0, 'Most common reason for discontinuation'),
(6, 'DKA (euglycemic)', 'rare', 'life_threatening', 'Discontinue. ER referral.', 1, 'Can occur with normal glucose levels'),
(6, 'Volume depletion', 'uncommon', 'moderate', 'Hydration. Reduce diuretic dose.', 0, 'Risk in elderly'),
-- Orlistat: GI effects
(40, 'Steatorrhea', 'very_common', 'mild', 'Low-fat diet (< 30% calories from fat).', 0, 'Dose-related'),
(40, 'Fat-soluble vitamin deficiency', 'common', 'moderate', 'Supplement ADEK vitamins.', 0, 'Take vitamins 2h apart from orlistat'),
-- Phentermine: CV effects
(43, 'Tachycardia', 'common', 'moderate', 'Monitor HR. Reduce dose if > 100 bpm.', 1, 'Dose-related'),
(43, 'Insomnia', 'common', 'mild', 'Take in morning only.', 0, 'Dose-related'),
(43, 'Dry mouth', 'common', 'mild', 'Hydration. Sugar-free gum.', 0, 'Usually transient'),
-- Bupropion: CNS effects
(41, 'Insomnia', 'common', 'mild', 'Take in morning.', 0, 'Dose-related'),
(41, 'Seizure', 'rare', 'life_threatening', 'Discontinue immediately. ER referral.', 1, 'Risk increases with dose > 450mg'),
-- Naltrexone: GI effects
(42, 'Nausea', 'common', 'moderate', 'Take with food. Antiemetic if needed.', 0, 'Usually transient'),
(42, 'Hepatotoxicity', 'rare', 'severe', 'Monitor LFTs. Discontinue if ALT > 3x ULN.', 1, 'Boxed warning');

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_medications_class ON medications(drug_class);
CREATE INDEX IF NOT EXISTS idx_medications_weight ON medications(weight_effect);
CREATE INDEX IF NOT EXISTS idx_medications_obesity ON medications(is_obesity_inducing);
CREATE INDEX IF NOT EXISTS idx_interactions_drug_a ON drug_interactions(drug_a_id);
CREATE INDEX IF NOT EXISTS idx_interactions_drug_b ON drug_interactions(drug_b_id);
CREATE INDEX IF NOT EXISTS idx_interactions_severity ON drug_interactions(severity);
CREATE INDEX IF NOT EXISTS idx_contraindications_med ON contraindications(medication_id);
CREATE INDEX IF NOT EXISTS idx_contraindications_cond ON contraindications(condition_code);
CREATE INDEX IF NOT EXISTS idx_renal_egfr ON renal_dosing(egfr_min, egfr_max);
CREATE INDEX IF NOT EXISTS idx_side_effects_med ON medication_side_effects(medication_id);

-- ============================================================
-- ICD-10 to ICD-11 Crosswalk (for future migration)
-- ============================================================
CREATE TABLE IF NOT EXISTS icd_crosswalk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    icd10_code TEXT NOT NULL,
    icd10_description TEXT,
    icd11_code TEXT NOT NULL,
    icd11_description TEXT,
    mapping_type TEXT CHECK(mapping_type IN ('exact', 'approximate', 'broad', 'narrow')),
    notes TEXT
);

-- Core metabolic conditions
INSERT OR IGNORE INTO icd_crosswalk (icd10_code, icd10_description, icd11_code, icd11_description, mapping_type, notes) VALUES
('E66', 'Obesity', '5B81', 'Obesity', 'exact', 'ICD-11 5B81'),
('E66.0', 'Obesity due to excess calories', '5B81.0', 'Obesity due to excess calories', 'exact', ''),
('E66.1', 'Drug-induced obesity', '5B81.1', 'Drug-induced obesity', 'exact', ''),
('E66.2', 'Extreme obesity with alveolar hypoventilation', '5B81.2', 'Extreme obesity with alveolar hypoventilation', 'exact', ''),
('E66.8', 'Other obesity', '5B81.8', 'Other obesity', 'exact', ''),
('E66.9', 'Obesity, unspecified', '5B81.9', 'Obesity, unspecified', 'exact', ''),
('E11', 'Type 2 diabetes mellitus', '5A11', 'Type 2 diabetes mellitus', 'exact', ''),
('E11.9', 'Type 2 diabetes mellitus without complications', '5A11.0', 'Type 2 diabetes mellitus without complications', 'exact', ''),
('E11.2', 'Type 2 diabetes mellitus with kidney complications', '5A11.1', 'Type 2 diabetes mellitus with kidney complications', 'exact', ''),
('E11.3', 'Type 2 diabetes mellitus with ophthalmic complications', '5A11.2', 'Type 2 diabetes mellitus with ophthalmic complications', 'exact', ''),
('E11.4', 'Type 2 diabetes mellitus with neurological complications', '5A11.3', 'Type 2 diabetes mellitus with neurological complications', 'exact', ''),
('E11.5', 'Type 2 diabetes mellitus with circulatory complications', '5A11.4', 'Type 2 diabetes mellitus with circulatory complications', 'exact', ''),
('E11.6', 'Type 2 diabetes mellitus with other specified complications', '5A11.5', 'Type 2 diabetes mellitus with other specified complications', 'exact', ''),
('E11.7', 'Type 2 diabetes mellitus with multiple complications', '5A11.6', 'Type 2 diabetes mellitus with multiple complications', 'exact', ''),
('E11.8', 'Type 2 diabetes mellitus with unspecified complications', '5A11.7', 'Type 2 diabetes mellitus with unspecified complications', 'exact', ''),
('E78', 'Disorders of lipoprotein metabolism and other lipidaemias', '5C80', 'Hyperlipidaemia', 'approximate', ''),
('E78.0', 'Pure hypercholesterolaemia', '5C80.0', 'Pure hypercholesterolaemia', 'exact', ''),
('E78.1', 'Pure hyperglyceridaemia', '5C80.1', 'Pure hyperglyceridaemia', 'exact', ''),
('E78.2', 'Mixed hyperlipidaemia', '5C80.2', 'Mixed hyperlipidaemia', 'exact', ''),
('E78.5', 'Hyperlipidaemia, unspecified', '5C80.5', 'Hyperlipidaemia, unspecified', 'exact', ''),
('I10', 'Essential (primary) hypertension', 'BA00', 'Essential (primary) hypertension', 'exact', ''),
('I11', 'Hypertensive heart disease', 'BA01', 'Hypertensive heart disease', 'exact', ''),
('I25', 'Chronic ischaemic heart disease', 'BA41', 'Chronic ischaemic heart disease', 'exact', ''),
('I25.1', 'Atherosclerotic heart disease', 'BA41.0', 'Atherosclerotic heart disease', 'exact', ''),
('I50', 'Heart failure', 'BD10', 'Heart failure', 'exact', ''),
('I50.9', 'Heart failure, unspecified', 'BD10.0', 'Heart failure, unspecified', 'exact', ''),
('I63', 'Cerebral infarction', '8B72', 'Cerebral infarction', 'exact', ''),
('N18', 'Chronic kidney disease', '5A00', 'Chronic kidney disease', 'exact', ''),
('N18.3', 'Chronic kidney disease, stage 3', '5A00.3', 'Chronic kidney disease, stage 3', 'exact', ''),
('N18.4', 'Chronic kidney disease, stage 4', '5A00.4', 'Chronic kidney disease, stage 4', 'exact', ''),
('N18.5', 'Chronic kidney disease, stage 5', '5A00.5', 'Chronic kidney disease, stage 5', 'exact', ''),
('N18.6', 'End stage renal disease', '5A00.6', 'End stage renal disease', 'exact', ''),
('E03', 'Other hypothyroidism', '5A00', 'Hypothyroidism', 'approximate', ''),
('E03.9', 'Hypothyroidism, unspecified', '5A00.9', 'Hypothyroidism, unspecified', 'exact', ''),
('E79', 'Disorders of purine and pyrimidine metabolism', '5C70', 'Gout', 'approximate', ''),
('E79.0', 'Hyperuricaemia without signs of inflammatory arthritis and tophaceous disease', '5C70.0', 'Gout without tophi', 'approximate', ''),
('K76', 'Other diseases of liver', '5B80', 'Non-alcoholic fatty liver disease', 'approximate', ''),
('K76.0', 'Fatty (change of) liver, not elsewhere classified', '5B80.0', 'Non-alcoholic fatty liver disease', 'approximate', ''),
('G47', 'Sleep disorders', '7A00', 'Insomnia disorder', 'approximate', ''),
('G47.3', 'Sleep apnoea', '7A00', 'Sleep apnoea', 'approximate', ''),
('G47.33', 'Obstructive sleep apnea (adult) (pediatric)', '7A00.0', 'Obstructive sleep apnoea', 'approximate', ''),
('E28', 'Ovarian dysfunction', 'GA00', 'Polycystic ovarian syndrome', 'approximate', ''),
('E28.2', 'Polycystic ovarian syndrome', 'GA00.0', 'Polycystic ovarian syndrome', 'exact', ''),
('F32', 'Depressive episode', '6A70', 'Depressive episode', 'exact', ''),
('F32.9', 'Depressive episode, unspecified', '6A70.9', 'Depressive episode, unspecified', 'exact', ''),
('F41', 'Other anxiety disorders', '6B00', 'Generalised anxiety disorder', 'approximate', ''),
('F41.9', 'Anxiety disorder, unspecified', '6B00.9', 'Generalised anxiety disorder, unspecified', 'approximate', ''),
('C73', 'Malignant neoplasm of thyroid gland', '2A70', 'Malignant neoplasm of thyroid gland', 'exact', ''),
('K85', 'Acute pancreatitis', '5C50', 'Acute pancreatitis', 'exact', ''),
('F50', 'Eating disorders', '6B80', 'Eating disorders', 'exact', ''),
('F50.0', 'Anorexia nervosa', '6B80.0', 'Anorexia nervosa', 'exact', ''),
('F50.2', 'Bulimia nervosa', '6B80.2', 'Bulimia nervosa', 'exact', ''),
('F50.8', 'Other eating disorders', '6B80.8', 'Other eating disorders', 'exact', ''),
('F50.9', 'Eating disorder, unspecified', '6B80.9', 'Eating disorder, unspecified', 'exact', ''),
('G40', 'Epilepsy', '8A60', 'Epilepsy', 'exact', ''),
('Z33', 'Pregnant state', '5C00', 'Pregnancy', 'exact', '');

-- ============================================================
-- Longevity & Performance Interventions
-- ============================================================
CREATE TABLE IF NOT EXISTS longevity_interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intervention_name TEXT NOT NULL,
    category TEXT CHECK(category IN ('pharmacological', 'supplement', 'lifestyle', 'procedure', 'device')),
    mechanism TEXT,
    evidence_level TEXT CHECK(evidence_level IN ('strong', 'moderate', 'weak', 'experimental')),
    human_data INTEGER DEFAULT 0,
    typical_dose TEXT,
    contraindications TEXT,
    monitoring TEXT,
    expected_benefit TEXT,
    time_to_effect_weeks INTEGER,
    cost_tier TEXT CHECK(cost_tier IN ('low', 'moderate', 'high', 'very_high')),
    notes TEXT
);

INSERT OR IGNORE INTO longevity_interventions (intervention_name, category, mechanism, evidence_level, human_data, typical_dose, contraindications, monitoring, expected_benefit, time_to_effect_weeks, cost_tier, notes) VALUES
-- Pharmacological
('Metformin', 'pharmacological', 'AMPK activation, mTOR inhibition, improved insulin sensitivity', 'moderate', 1, '500-2000mg/day', 'eGFR < 30, lactic acidosis risk', 'eGFR, B12 annually', 'Reduced all-cause mortality, improved metabolic health', 12, 'low', 'Off-label for longevity. TAME trial ongoing.'),
('Rapamycin (Sirolimus)', 'pharmacological', 'mTORC1 inhibition, autophagy induction', 'moderate', 1, '6mg weekly (intermittent)', 'Immunosuppression, hyperlipidemia', 'Lipid panel, CBC, immune function', 'Improved immune function, reduced senescence', 24, 'high', 'PERL trial. Intermittent dosing preferred.'),
('Acarbose', 'pharmacological', 'Alpha-glucosidase inhibition, reduced postprandial glucose', 'moderate', 1, '50-100mg TID with meals', 'IBD, cirrhosis, renal impairment', 'HbA1c, GI tolerance', 'Reduced all-cause mortality in ITP mouse, human data emerging', 12, 'low', 'Strong mouse data, human observational data.'),
('SGLT2 Inhibitors', 'pharmacological', 'Caloric loss via glucosuria, improved cardiac/renal function', 'strong', 1, '10-25mg/day', 'eGFR < 20 (glycemic), DKA risk', 'Renal function, volume status', 'Reduced CV mortality, renal protection, modest weight loss', 4, 'high', 'Strong human outcome data.'),
('GLP-1 Receptor Agonists', 'pharmacological', 'Improved insulin sensitivity, reduced inflammation, weight loss', 'strong', 1, 'Semaglutide 0.25-2.4mg weekly', 'TCM/MEN2, pancreatitis, pregnancy', 'Weight, body composition, GI tolerance', 'Reduced CV events (SELECT), significant weight loss', 12, 'high', 'SELECT trial: 20% MACE reduction.'),
('NAD+ Precursors (NR/NMN)', 'supplement', 'NAD+ restoration, sirtuin activation, mitochondrial function', 'weak', 1, '250-1000mg/day', 'Active cancer (theoretical)', 'NAD+ levels (optional), metabolic panel', 'Improved vascular function, reduced inflammation', 8, 'moderate', 'Human safety established, efficacy emerging.'),
('Omega-3 (EPA/DHA)', 'supplement', 'Anti-inflammatory, membrane fluidity, cardiovascular protection', 'strong', 1, '2-4g EPA+DHA/day', 'Fish allergy, bleeding disorders', 'Omega-3 index, lipid panel', 'Reduced CV events, improved cognitive function', 12, 'low', 'REDUCE-IT trial: 25% CV event reduction with 4g EPA.'),
('Vitamin D3', 'supplement', 'Immune modulation, bone health, cardiovascular protection', 'strong', 1, '2000-5000 IU/day', 'Hypercalcemia, sarcoidosis', '25-OH Vitamin D, calcium', 'Reduced all-cause mortality at optimal levels', 8, 'low', 'Target 30-50 ng/mL.'),
('Magnesium', 'supplement', '300+ enzymatic reactions, insulin sensitivity, sleep quality', 'moderate', 1, '200-400mg/day (glycinate/threonate)', 'Renal impairment (severe)', 'RBC magnesium, renal function', 'Improved sleep, insulin sensitivity, BP', 4, 'low', 'Glycinate for sleep, threonate for cognition.'),
('Creatine Monohydrate', 'supplement', 'ATP regeneration, muscle preservation, cognitive function', 'strong', 1, '3-5g/day', 'Pre-existing renal disease (relative)', 'Renal function (baseline)', 'Improved muscle mass, cognitive function, exercise performance', 4, 'low', 'Most studied supplement. Safe long-term.'),
('Resistance Training', 'lifestyle', 'Muscle hypertrophy, bone density, insulin sensitivity, myokines', 'strong', 1, '2-4x/week, progressive overload', 'Acute injury, uncontrolled HTN', 'Body composition, strength metrics', 'Increased healthspan, reduced sarcopenia, improved metabolism', 8, 'low', 'Single most effective longevity intervention.'),
('Zone 2 Cardio', 'lifestyle', 'Mitochondrial biogenesis, fat oxidation, cardiovascular fitness', 'strong', 1, '150-300 min/week at 60-70% max HR', 'Unstable cardiac conditions', 'VO2max, resting HR, HRV', 'Improved mitochondrial function, reduced CV risk', 12, 'low', 'Foundation of cardiovascular longevity.'),
('VO2 Max Training', 'lifestyle', 'Peak cardiovascular fitness, mitochondrial density', 'strong', 1, '1-2x/week, 4x4 min intervals', 'Unstable cardiac conditions', 'VO2max testing', 'Strongest predictor of all-cause mortality', 16, 'low', 'Each 1 MET increase = 15% mortality reduction.'),
('Sleep Optimization', 'lifestyle', 'Glymphatic clearance, hormone regulation, DNA repair', 'strong', 1, '7-9 hours, consistent schedule', 'N/A', 'Sleep tracking, Athens/PSQI', 'Reduced all-cause mortality, improved cognition', 4, 'low', 'Foundation of all other interventions.'),
('Time-Restricted Eating', 'lifestyle', 'Circadian alignment, autophagy, insulin sensitivity', 'moderate', 1, '8-10 hour eating window', 'Eating disorders, pregnancy, underweight', 'Body composition, HbA1c, lipids', 'Improved insulin sensitivity, weight management', 4, 'low', '16:8 most studied. Not superior to caloric restriction for weight loss.'),
('Heat Exposure (Sauna)', 'lifestyle', 'Heat shock proteins, cardiovascular conditioning, detoxification', 'moderate', 1, '4-7x/week, 15-20 min at 80-100°C', 'Unstable angina, recent MI', 'BP, HR response', 'Reduced all-cause and CV mortality (Finnish data)', 8, 'moderate', '4-7x/week = 40% reduction in all-cause mortality.'),
('Cold Exposure', 'lifestyle', 'Brown fat activation, norepinephrine release, anti-inflammatory', 'weak', 1, '2-3x/week, 2-5 min at 10-15°C', 'Raynaud, cardiovascular disease', 'HR, BP response', 'Improved mood, reduced inflammation, brown fat activation', 4, 'low', 'Human data limited but promising.'),
('Hyperbaric Oxygen', 'procedure', 'Telomere lengthening, senescent cell reduction, angiogenesis', 'weak', 1, '60 sessions, 90 min at 2 ATA', 'Untreated pneumothorax, certain chemo', 'Telomere length (research)', 'Telomere lengthening, reduced senescent cells', 12, 'very_high', 'Shai Efrati trial. Expensive, limited accessibility.'),
('Plasmapheresis/Therapeutic Plasma Exchange', 'procedure', 'Removal of pro-aging factors from blood, dilution of inflammatory markers', 'experimental', 1, '3-5 exchanges, 1-2x/year', 'Active infection, hemodynamic instability', 'Inflammatory markers, albumin', 'Reduced biological age (AMBAR trial)', 4, 'very_high', 'AMBAR trial: slowed Alzheimer progression.'),
('Senolytics (Dasatinib + Quercetin)', 'pharmacological', 'Selective elimination of senescent cells', 'experimental', 1, 'D 100mg + Q 1000mg, 1 day/month', 'Active infection, immunosuppression', 'Senescence markers (research)', 'Reduced senescent cell burden, improved function', 4, 'moderate', 'UNITY Biotechnology trials. Intermittent dosing.'),
('Fisetin', 'supplement', 'Senolytic, anti-inflammatory, NAD+ boosting', 'weak', 1, '100-500mg/day or 20mg/kg pulse', 'Pregnancy, active infection', 'Inflammatory markers', 'Senescent cell clearance, improved healthspan', 4, 'moderate', 'Mayo Clinic protocols. Pulse dosing preferred.'),
('NMN (Nicotinamide Mononucleotide)', 'supplement', 'NAD+ precursor, sirtuin activation, DNA repair', 'weak', 1, '250-500mg/day', 'Active cancer (theoretical)', 'NAD+ levels (optional)', 'Improved vascular function, insulin sensitivity', 8, 'moderate', 'FDA status uncertain. Human safety established.'),
('Spermidine', 'supplement', 'Autophagy induction, polyamine metabolism, epigenetic regulation', 'weak', 1, '1-6mg/day', 'None known', 'Autophagy markers (research)', 'Reduced all-cause mortality (observational)', 12, 'moderate', 'Strong observational data. RCTs ongoing.'),
('Urolithin A', 'supplement', 'Mitophagy induction, mitochondrial quality control', 'moderate', 1, '500-1000mg/day', 'None known', 'Mitochondrial function (research)', 'Improved muscle endurance, mitochondrial health', 8, 'high', 'Human RCTs show improved muscle endurance.'),
('Glycine + NAC (GlyNAC)', 'supplement', 'Glutathione synthesis, oxidative stress reduction, mitochondrial function', 'moderate', 1, 'Glycine 100mg/kg + NAC 100mg/kg', 'None known', 'Glutathione levels, oxidative stress markers', 'Improved mitochondrial function, reduced oxidative stress', 12, 'low', 'Baylor College RCTs. Promising results in older adults.'),
('Apigenin', 'supplement', 'CD38 inhibition (NAD+ preservation), autophagy, anti-inflammatory', 'weak', 1, '50mg/day', 'None known', 'None specific', 'NAD+ preservation, improved sleep', 8, 'low', 'CD38 inhibition is a novel mechanism.'),
('Taurine', 'supplement', 'Mitochondrial function, antioxidant, anti-inflammatory', 'moderate', 1, '1-3g/day', 'None known', 'None specific', 'Reduced biological age markers, improved exercise capacity', 12, 'low', 'Science 2023: taurine deficiency drives aging.'),
('Collagen Peptides', 'supplement', 'Skin elasticity, joint health, gut integrity', 'moderate', 1, '10-15g/day', 'None known', 'None specific', 'Improved skin elasticity, joint comfort', 8, 'moderate', 'Type I & III for skin, Type II for joints.'),
('Berberine', 'supplement', 'AMPK activation, improved insulin sensitivity, lipid lowering', 'moderate', 1, '500mg TID with meals', 'Pregnancy, CYP interactions', 'HbA1c, lipid panel, liver function', 'Improved glycemic control, lipid profile', 8, 'low', 'Natural metformin alternative. GI side effects common.'),
('Ashwagandha', 'supplement', 'Cortisol reduction, stress adaptation, thyroid support', 'moderate', 1, '300-600mg/day (KSM-66)', 'Hyperthyroidism, autoimmune disease', 'Cortisol, thyroid panel', 'Reduced cortisol, improved sleep, stress resilience', 4, 'moderate', 'KSM-66 most studied extract.'),
('Red Light Therapy (PBM)', 'device', 'Mitochondrial cytochrome c oxidase activation, ATP production', 'moderate', 1, '10-20 min/day, 660nm + 850nm', 'Active cancer over treatment area', 'None specific', 'Improved skin, reduced inflammation, wound healing', 8, 'moderate', '660nm for skin, 850nm for deep tissue.'),
('HRV Biofeedback', 'device', 'Autonomic nervous system regulation, vagal tone improvement', 'moderate', 1, '10-20 min/day', 'None', 'HRV metrics (SDNN, RMSSD)', 'Improved stress resilience, sleep, cardiovascular health', 4, 'moderate', 'RMSSD > 50ms target for adults.');

