"""
Static Knowledge Base for Drug-Drug and Drug-Condition Interactions.
Extracted from clinical evidence for SaMD pure engine execution.
SOURCE: Integrum V1 Database Seed (2026-04-03)
"""

from typing import Dict, Any, List

# Core medication metadata (Obesity/Metabolic focus)
MEDICATIONS: Dict[str, Dict[str, Any]] = {
    "semaglutide": {
        "id": 1, "class": "GLP-1 RA", "weight_effect": "loss", "avg_loss": -15.0, 
        "renal_dosing": False, "teratogenic": True, "preg_cat": "N", "qt_risk": "low"
    },
    "tirzepatide": {
        "id": 2, "class": "GIP/GLP-1 RA", "weight_effect": "loss", "avg_loss": -20.0, 
        "renal_dosing": False, "teratogenic": True, "preg_cat": "N", "qt_risk": "low"
    },
    "metformin": {
        "id": 9, "class": "Biguanide", "weight_effect": "neutral", "avg_loss": -1.0, 
        "renal_dosing": True, "teratogenic": False, "preg_cat": "B", "qt_risk": "none"
    },
    "empagliflozin": {
        "id": 6, "class": "SGLT2i", "weight_effect": "loss", "avg_loss": -2.5, 
        "renal_dosing": True, "teratogenic": True, "preg_cat": "N", "qt_risk": "none"
    },
    "bupropion": {
        "id": 41, "class": "Atypical AD", "weight_effect": "loss", "avg_loss": -2.5, 
        "renal_dosing": False, "teratogenic": False, "preg_cat": "C", "qt_risk": "low"
    },
    "insulin_glargine": {
        "id": 11, "class": "Insulin", "weight_effect": "gain", "avg_loss": 4.0, 
        "renal_dosing": True, "teratogenic": False, "preg_cat": "B", "qt_risk": "none"
    },
    "atorvastatin": {
        "id": 10, "class": "Statin", "weight_effect": "neutral", "avg_loss": 0.0, 
        "renal_dosing": False, "teratogenic": True, "preg_cat": "X", "qt_risk": "none"
    },
    # More medications can be added here following the same pattern
}

# Mapping generic medicine keys to their internal database IDs for fast lookup
MED_NAME_TO_ID = {name: data["id"] for name, data in MEDICATIONS.items()}
ID_TO_MED_NAME = {data["id"]: name for name, data in MEDICATIONS.items()}

# Drug-Drug Interactions Matrix
# (Drug_A_ID, Drug_B_ID) -> {severity, mechanism, effect, management, evidence_level}
INTERACTIONS: Dict[tuple[int, int], Dict[str, str]] = {
    (1, 11): { # GLP1 + Insulin
        "severity": "major", "mechanism": "Additive glucose-lowering", 
        "effect": "Hypoglycemia risk", "management": "Reduce insulin 10-20%. Monitor glucose.",
        "evidence": "established", "source": "FDA Label"
    },
    (2, 11): { # Tirzepatide + Insulin
        "severity": "major", "mechanism": "Additive glucose-lowering", 
        "effect": "Hypoglycemia risk", "management": "Reduce insulin 10-20%. Monitor glucose.",
        "evidence": "established", "source": "FDA Label"
    },
    (6, 28): { # SGLT2i + Diuretics (28: generic diuretic placeholder)
        "severity": "moderate", "mechanism": "Additive diuresis", 
        "effect": "Volume depletion/AKI", "management": "Monitor renal function. Consider dose reduction.",
        "evidence": "established", "source": "FDA Label"
    },
}

# Contraindications by Condition (Condition Code -> List of med_ids)
CONTRAINDICATIONS: Dict[str, List[Dict[str, str]]] = {
    "C73": [ # Thyroid cancer
        {"med_id": 1, "severity": "absolute", "rationale": "Boxed warning: thyroid C-cell tumors", "alt": "Wait for oncologist clearance"},
        {"med_id": 2, "severity": "absolute", "rationale": "Boxed warning: thyroid C-cell tumors", "alt": "Wait for oncologist clearance"},
    ],
    "N18.4": [ # CKD Stage 4
        {"med_id": 9, "severity": "absolute", "rationale": "Lactic acidosis risk (eGFR < 30)", "alt": "Consider GLP-1 or DPP-4i"},
    ],
    "Z33": [ # Pregnancy
        {"med_id": 10, "severity": "absolute", "rationale": "Teratogenic - Category X", "alt": "Discontinue immediately"},
    ]
}

# Renal Adjustments (Med_ID -> List of ranges)
RENAL_DOSING: Dict[int, List[Dict[str, Any]]] = {
    9: [ # Metformin
        {"min": 45, "max": 60, "adjustment": "Reduce 50%", "notes": "Monitor Cr Q3M"},
        {"min": 30, "max": 45, "adjustment": "Reduce 50%", "notes": "Do not initiate if eGFR < 45"},
        {"min": 0, "max": 30, "adjustment": "Contraindicated", "notes": "Discontinue immediately"},
    ]
}
