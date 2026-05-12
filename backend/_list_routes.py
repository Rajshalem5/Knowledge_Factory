"""List all registered routes."""
import sys
sys.path.insert(0, ".")
from app.main import app

routes = [(r.path, list(r.methods)[0] if r.methods else 'ANY') for r in app.routes if hasattr(r, 'path')]
for path, method in sorted(routes):
    print(f'{method:6s} {path}')
