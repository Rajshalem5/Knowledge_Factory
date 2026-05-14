#!/usr/bin/env python3
"""Login all roles via API and save tokens - with corrected HR password."""
import json, os

try:
    import requests
except ImportError:
    os.system(f"{__import__('sys').executable} -m pip install requests -q")
    import requests

BASE = "http://localhost:8000"
ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "password": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "password": "admin123"},
    "hr": {"email": "hr@test.com", "password": "Test@123"},
    "interviewer": {"email": "interviewer@test.com", "password": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "password": "Candidate@12345"},
}

results = {}
all_ok = True
role_info = {}
for role, creds in ROLES.items():
    resp = requests.post(f"{BASE}/api/auth/login", json=creds, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        results[role] = {
            "token": data["access_token"],
            "user_email": data["user"]["email"],
            "user_role": data["user"]["role"],
        }
        role_info[role] = (data["user"]["role"], data["user"]["email"])
        print(f"OK:{role}:{data['user']['role']}:{data['user']['email']}")
    else:
        results[role] = {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        print(f"FAIL:{role}:HTTP {resp.status_code}")
        all_ok = False

# Save tokens
os.makedirs("/opt/hermes_shared_memory/projects/Knowledge_Factory/auth/tokens", exist_ok=True)
with open("/opt/hermes_shared_memory/projects/Knowledge_Factory/auth/tokens/current.json", "w") as f:
    json.dump(results, f)

print(f"\nALL_OK={all_ok}")
print(f"Roles: {json.dumps(role_info)}")
