"""Quick check which settings attributes exist."""
import os
os.chdir("/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")
import sys
sys.path.insert(0, ".")
from app.config import settings

for key in ['JWT_SECRET_KEY', 'AI_API_KEY', 'SANDBOX_URL', 'JWT_ACCESS_TTL_MINUTES', 
            'JWT_REFRESH_TTL_DAYS', 'AI_API_URL', 'AI_MODEL', 'JWT_PRIVATE_KEY', 'JWT_PUBLIC_KEY']:
    try:
        val = getattr(settings, key)
        print(f"{key} = {repr(val)}")
    except AttributeError as e:
        print(f"{key}: MISSING")
