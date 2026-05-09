"""Check backend imports."""
import sys
sys.path.insert(0, '.')
try:
    from app.main import app
    print('Backend imports OK')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
