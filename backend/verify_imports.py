"""Verify backend imports compile correctly."""
import sys
sys.path.insert(0, '.')

try:
    from app.features.candidates.schemas import CandidateRead
    print('✓ CandidateRead schema imports OK')
except Exception as e:
    print(f'✗ CandidateRead schema failed: {e}')
    sys.exit(1)

try:
    from app.main import app
    print('✓ FastAPI app imports OK')
    print('Routes:')
    for route in app.routes:
        if hasattr(route, 'path') and '/api/' in route.path:
            methods = route.methods if hasattr(route, 'methods') else {'GET'}
            print(f'  {methods} {route.path}')
except Exception as e:
    print(f'✗ FastAPI app failed: {e}')
    sys.exit(1)

print('\n✓ All imports verified successfully!')
