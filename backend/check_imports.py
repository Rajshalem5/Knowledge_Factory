"""Quick check that backend imports and routes load"""
from app.main import app

print('OK')
print(f'Routes: {len(app.routes)}')
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        methods = ','.join(sorted(route.methods))
        print(f'  {methods} {route.path}')
