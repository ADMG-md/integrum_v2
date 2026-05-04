#!/usr/bin/env python3
"""
Batch update engines to use confidence standards (H-04).

Usage:
    python3 scripts/batch_update_confidence.py

This script updates all engine files to:
1. Import confidence_standards module (after all existing imports)
2. Replace magic number confidence values with CONFIDENCE_VALUES[ConfidenceLevel.X]
"""

import re
from pathlib import Path

# Engine confidence tier mapping
ENGINES_TIER_MAP = {
    # Tier 1: ESTABLISHED_GUIDELINE
    "cancer_screening.py": "ESTABLISHED_GUIDELINE",
    "glp1_monitor.py": "ESTABLISHED_GUIDELINE",
    "metformin_b12.py": "ESTABLISHED_GUIDELINE",
    "vitamin_d.py": "ESTABLISHED_GUIDELINE",
    "womens_health.py": "ESTABLISHED_GUIDELINE",
    "mens_health.py": "ESTABLISHED_GUIDELINE",
    "hypertension.py": "ESTABLISHED_GUIDELINE",
    "fried_frailty.py": "ESTABLISHED_GUIDELINE",
    "charlson.py": "ESTABLISHED_GUIDELINE",
    "kfre.py": "ESTABLISHED_GUIDELINE",
    
    # Tier 2: VALIDATED_BIOMARKER
    "sarcopenia.py": "VALIDATED_BIOMARKER",
    "functional_sarcopenia.py": "VALIDATED_BIOMARKER",
    "anthropometry.py": "VALIDATED_BIOMARKER",
    "endocrine.py": "VALIDATED_BIOMARKER",
    "fatty_liver.py": "VALIDATED_BIOMARKER",
    "nafld_fibrosis.py": "VALIDATED_BIOMARKER",
    "visceral_adiposity.py": "VALIDATED_BIOMARKER",
    "sleep_apnea.py": "VALIDATED_BIOMARKER",
    "apob_ratio.py": "VALIDATED_BIOMARKER",
    "lipid_risk.py": "VALIDATED_BIOMARKER",
    
    # Tier 3: PEER_REVIEWED
    "tyg_bmi.py": "PEER_REVIEWED",
    "cardiometabolic.py": "PEER_REVIEWED",
    "hemodynamics.py": "PEER_REVIEWED",
    "body_comp_trend.py": "PEER_REVIEWED",
    "sglt2i_benefit.py": "PEER_REVIEWED",
    "glp1_titration.py": "PEER_REVIEWED",
    "pharma.py": "PEER_REVIEWED",
    "pharma_precision.py": "PEER_REVIEWED",
    "precision_nutrition.py": "PEER_REVIEWED",
    "lifestyle.py": "PEER_REVIEWED",
    "pediatric_nutrition.py": "PEER_REVIEWED",
    
    # Tier 4: INDIRECT_EVIDENCE
    "bio_age.py": "INDIRECT_EVIDENCE",
    "psychometabolic_axis.py": "INDIRECT_EVIDENCE",
    "metabolomics.py": "INDIRECT_EVIDENCE",
    "ace_integration.py": "INDIRECT_EVIDENCE",
    "readiness.py": "INDIRECT_EVIDENCE",
    
    # Tier 5: PROXY_MARKER
    "pharmacogenomics.py": "PROXY_MARKER",
    "drug_interaction.py": "PROXY_MARKER",
    "lab_suggestion.py": "PROXY_MARKER",
    "guidelines.py": "PROXY_MARKER",
    "cvd_reclassifier.py": "PROXY_MARKER",
}

IMPORT_LINE = '\nfrom src.engines.confidence_standards import CONFIDENCE_VALUES, ConfidenceLevel\n'

def update_engine_file(filepath: Path, tier: str) -> bool:
    """Update an engine file to use confidence standards."""
    content = filepath.read_text()
    
    # Check if already updated
    if 'CONFIDENCE_VALUES' in content:
        return False
    
    # Find where to insert the import (after all imports, before class definition)
    # Pattern: find the last line that starts with 'from ' or 'import ' or is part of a multi-line import
    lines = content.split('\n')
    insert_index = 0
    in_multiline_import = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track multi-line imports (parentheses)
        if '(' in stripped and not stripped.startswith('class ') and not stripped.startswith('def '):
            in_multiline_import = True
        
        if in_multiline_import:
            if ')' in stripped:
                in_multiline_import = False
            insert_index = i + 1
            continue
        
        if stripped.startswith('from ') or stripped.startswith('import '):
            insert_index = i + 1
        elif stripped == '' and insert_index == i:
            # Skip blank lines between imports
            continue
        elif stripped.startswith('class ') or stripped.startswith('def '):
            # Stop at class/function definition
            break
    
    # Insert the import
    lines.insert(insert_index, IMPORT_LINE.rstrip())
    content = '\n'.join(lines)
    
    # Replace confidence values based on tier
    # Pattern: confidence=0.XX or confidence = 0.XX
    confidence_level = f"ConfidenceLevel.{tier}"
    
    # Replace patterns like confidence=0.95, confidence = 0.90, etc.
    # But NOT confidence=0.0 (which is for error/missing data)
    content = re.sub(
        r'confidence\s*=\s*0\.(?!0\b)\d+',
        f'confidence=CONFIDENCE_VALUES[{confidence_level}]',
        content
    )
    
    filepath.write_text(content)
    return True

def main():
    specialty_dir = Path(__file__).parent.parent / 'src' / 'engines' / 'specialty'
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for filename, tier in ENGINES_TIER_MAP.items():
        filepath = specialty_dir / filename
        if not filepath.exists():
            print(f"SKIP (not found): {filename}")
            skipped_count += 1
            continue
        
        try:
            if update_engine_file(filepath, tier):
                print(f"UPDATED: {filename} -> {tier}")
                updated_count += 1
            else:
                print(f"SKIP (already updated): {filename}")
                skipped_count += 1
        except Exception as e:
            print(f"ERROR: {filename} -> {e}")
            error_count += 1
    
    print(f"\nDone! Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}")

if __name__ == '__main__':
    main()
