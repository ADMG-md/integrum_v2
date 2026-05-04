import os
import re

tests_dir = 'apps/backend/tests/'
engines_dir = 'apps/backend/src/engines/'

def fix_file(filepath):
    with open(filepath, 'r') as file:
        content = file.read()
    
    # 1. Replace cardio_panel=MetabolicPanelSchema(...) with nothing if metabolic_panel exists
    # It's easier to just match:
    # metabolic_panel=MetabolicPanelSchema(A),
    # cardio_panel=MetabolicPanelSchema(B)
    # and replace with:
    # metabolic_panel=MetabolicPanelSchema(A, B)
    # Wait, A or B might have newlines.
    
    # Regex to match:
    # metabolic_panel=MetabolicPanelSchema((.*?)),\s*cardio_panel=MetabolicPanelSchema\((.*?)\)
    # using re.DOTALL
    new_content = re.sub(
        r'metabolic_panel=MetabolicPanelSchema\((.*?)\),\s*cardio_panel=MetabolicPanelSchema\((.*?)\)',
        lambda m: 'metabolic_panel=MetabolicPanelSchema(' + 
                  (m.group(1) + ', ' + m.group(2) if m.group(1).strip() and m.group(2).strip() 
                   else m.group(1) + m.group(2)) + ')',
        content,
        flags=re.DOTALL
    )
    
    # Fix duplicated imports
    new_content = new_content.replace(
        "    MetabolicPanelSchema,\n    MetabolicPanelSchema,",
        "    MetabolicPanelSchema,"
    )

    # 2. Fix tsh_uIU_ml to tsh_u_iu_ml
    new_content = new_content.replace('tsh_uIU_ml', 'tsh_u_iu_ml')
    
    if new_content != content:
        with open(filepath, 'w') as file:
            file.write(new_content)

for d in [tests_dir, engines_dir]:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.py'):
                fix_file(os.path.join(root, f))
