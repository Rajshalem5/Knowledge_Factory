#!/usr/bin/env python3
"""Quick verify hiring cycles fix"""
import requests, json

BASE = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"

# Login admin
r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
token = r.json().get("access_token")
print(f"Admin login: {r.status_code}, token: {token[:20]}...")

# Test hiring cycles
r = requests.get(f"{BASE}/api/hiring-cycles/", headers={"Authorization": f"Bearer {token}"})
print(f"\nHiring cycles: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Count: {len(data) if isinstance(data, list) else 'non-list'}")
    if isinstance(data, list) and data:
        print(f"  First: {json.dumps(data[0], indent=2, default=str)[:300]}")
    elif isinstance(data, list):
        print("  Empty list")
    else:
        print(f"  Response: {json.dumps(data, default=str)[:300]}")
else:
    print(f"  FAILED: {r.text[:200]}")
