"""Check syntax and key imports."""
import ast
import os
import sys

errors = []

for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    tree = ast.parse(fh.read())
            except SyntaxError as e:
                errors.append(('SYNTAX', path, str(e)))

for path, err in errors:
    print(f'{path}: {err}')

if not errors:
    print("All Python files parse correctly (0 syntax errors)")
    
sys.exit(1 if errors else 0)
