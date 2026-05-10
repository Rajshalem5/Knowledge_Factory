"""Check that the app loads and all routes are registered."""
from app.main import app
print('App loaded OK')
print(f'Routes: {len([r for r in app.routes if hasattr(r, "methods")])}')
for r in app.routes:
    if hasattr(r, 'methods') and hasattr(r, 'path'):
        print(f'  {r.methods} {r.path}')
