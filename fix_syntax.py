import os
import re

tests_dir = 'apps/backend/tests/'

for root, _, files in os.walk(tests_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as file:
                content = file.read()
            
            new_content = re.sub(r',\s*,', ',', content)
            
            if new_content != content:
                with open(filepath, 'w') as file:
                    file.write(new_content)
