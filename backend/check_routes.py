"""Quick check that the app imports and routes are registered."""
from app.main import app
print(f'App imports OK')
print(f'Routes registered: {len(app.routes)}')
for r in app.routes:
    if hasattr(r, 'methods') and hasattr(r, 'path'):
        print(f'  {r.methods} {r.path}')
