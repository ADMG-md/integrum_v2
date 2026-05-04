with open('apps/backend/tests/conftest.py', 'r') as f:
    content = f.read()

content = content.replace(",\n,", ",")

with open('apps/backend/tests/conftest.py', 'w') as f:
    f.write(content)
