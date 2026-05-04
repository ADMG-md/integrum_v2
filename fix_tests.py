import os
import re

tests_dir = 'apps/backend/tests/unit/engines'

for root, _, files in os.walk(tests_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as file:
                content = file.read()
            
            # The pattern is:
            # metabolic_panel=MetabolicPanelSchema(),
            # cardio_panel=cp,
            # We should replace it with:
            # metabolic_panel=cp,
            new_content = re.sub(
                r'metabolic_panel=MetabolicPanelSchema\(\),\s*cardio_panel=cp,',
                'metabolic_panel=cp,',
                content
            )
            
            # Also handle:
            # metabolic_panel=MetabolicPanelSchema(),
            # cardio_panel=MetabolicPanelSchema(
            new_content = re.sub(
                r'metabolic_panel=MetabolicPanelSchema\(\),\s*cardio_panel=MetabolicPanelSchema\(',
                'metabolic_panel=MetabolicPanelSchema(',
                new_content
            )
            
            # What if `cardio_panel=cp` alone exists? Replace with `metabolic_panel=cp`
            # Be careful not to create duplicates if `metabolic_panel` is already there.
            # But the two regexes above should cover most _make_encounter functions.

            if new_content != content:
                with open(filepath, 'w') as file:
                    file.write(new_content)

