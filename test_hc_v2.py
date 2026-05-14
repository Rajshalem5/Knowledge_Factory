#!/usr/bin/env python3
"""Check current uvicorn process and restart if needed, then test hiring cycles."""
import requests, json, os, sys, time, subprocess

BASE = "http://localhost:8000"

# Check if backend is running
r = requests.get(f"{BASE}/health", timeout=5)
print(f"Health: {r.status_code} - {r.json()}")

# Login admin
r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
if r.status_code != 200:
    print(f"Login FAILED: {r.status_code} - {r.text[:100]}")
    sys.exit(1)
token = r.json().get("access_token")
print(f"Admin login: OK")

# Test hiring cycles
r = requests.get(f"{BASE}/api/hiring-cycles/", headers={"Authorization": f"Bearer {token}"})
print(f"\nHiring cycles: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Count: {len(data) if isinstance(data, list) else 'non-list'}")
    if isinstance(data, list) and data:
        print(f"  First: {json.dumps(data[0], indent=2, default=str)[:400]}")
    elif isinstance(data, list):
        print("  Empty list")
    else:
        print(f"  Response type: {type(data).__name__}")
        print(f"  Content: {json.dumps(data, default=str)[:300]}")
elif r.status_code == 500:
    print(f"  500 ERROR - trace:")
    # Try to get traceback from the response
    print(f"  Body: {r.text[:500]}")
    
    # Let's try importing the module directly to find the error
    print("\n  Trying to reproduce the error...")
else:
    print(f"  Status: {r.status_code} - {r.text[:200]}")
