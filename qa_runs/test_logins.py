#!/usr/bin/env python3
"""Test login with known credentials."""
import urllib.request
import json

BASE_URL = "http://localhost:8000"

def test_login(email, password):
    url = f"{BASE_URL}/api/auth/login"
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            print(f"  ✅ {email} (pwd={password}): {resp.status} OK")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  ❌ {email} (pwd={password}): {e.code} {body[:100]}")
        return False
    except Exception as e:
        print(f"  💥 {email}: {e}")
        return False

# Test various credential combos
logins = [
    # From the env vars specified in the skill
    ("superadmin@knowledgefactory.io", "Super@12345"),
    ("admin@knowledgefactory.io", "admin123"),
    ("admin@test.com", "admin123"),
    ("hr@test.com", "Hr@12345"),
    ("hr@knowledgefactory.io", "Hr@12345"),
    ("interviewer@test.com", "Interviewer@12345"),
    ("interviewer@knowledgefactory.io", "Interviewer@12345"),
    ("candidate@test.com", "Candidate@12345"),
    # Try candidate accounts - might use different auth flow
    ("alice@test.com", "Candidate@12345"),
    ("bob@test.com", "Candidate@12345"),
]

print("Testing login combinations:\n")
for email, pwd in logins:
    test_login(email, pwd)
