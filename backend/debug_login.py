"""Reproduce and trace the 500 error on candidate login"""
import httpx
import traceback

BASE = "http://127.0.0.1:8001"

# Try candidate login
try:
    r = httpx.post(f"{BASE}/api/auth/login", json={
        "email": "pipeline-test@example.com", "password": "Test@123"
    })
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    traceback.print_exc()
