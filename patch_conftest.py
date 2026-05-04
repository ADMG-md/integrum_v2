import re

with open('apps/backend/tests/conftest.py', 'r') as f:
    content = f.read()

# Fix imports
content = content.replace("    MetabolicPanelSchema,\n    MetabolicPanelSchema,", "    MetabolicPanelSchema,")

# Remove cardio_panel=MetabolicPanelSchema() in empty_encounter
content = content.replace("        cardio_panel=MetabolicPanelSchema(),\n", "")

# Merge cardio_panel in minimal_encounter
content = content.replace("        ),\n        cardio_panel=MetabolicPanelSchema(", ",")

# Merge cardio_panel in full_encounter
# The pattern is `        ),\n        cardio_panel=MetabolicPanelSchema(` which is replaced with `,`
# Wait, let's verify if that works for all.
with open('apps/backend/tests/conftest.py', 'w') as f:
    f.write(content)
