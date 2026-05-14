#!/usr/bin/env python3
"""Test login with various credentials to find the right ones."""
import json
import urllib.request
import urllib.error

BASE_URL = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"

def try_login(email, password):
    """Try to login and return result."""
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read().decode())
        token = body.get("access_token") or body.get("token") or ""
        return f"✅ 200 - Token starts: {token[:20]}..."
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:150]
        return f"❌ {e.code} - {body}"
    except Exception as e:
        return f"⚠️  Error: {e}"

# Combinations to try based on what's in the DB
combos = [
    # hr@test.com - exists in DB, password? Could be from create_test_users.py
    ("hr@test.com", "Hr@12345", "HR (skill doc password)"),
    ("hr@test.com", "Test@1234", "HR (create_test_users.py password)"),
    # interviewer@test.com - exists in DB, password?
    ("interviewer@test.com", "Interviewer@12345", "Interviewer (skill doc)"),
    ("interviewer@test.com", "Interview@12345", "Interviewer (seed.py variant)"),
    ("interviewer@test.com", "Test@1234", "Interviewer (generic test)"),
    # interviewer@knowledgefactory.io - from seed.py
    ("interviewer@knowledgefactory.io", "Interview@12345", "Interviewer (seed.py email)"),
    # hr@knowledgefactory.io - from seed.py
    ("hr@knowledgefactory.io", "Hr@12345", "HR (seed.py email/pass)"),
    # candidate@test.com - not in users table, may be in candidates
    ("candidate@test.com", "Candidate@12345", "Candidate (skill doc)"),
    ("candidate@test.com", "Test@1234", "Candidate (generic)"),
    # Try candidates from seed_db.py
    ("alice@test.com", "Candidate@123", "Alice (seed_db.py candidate)"),
    # admin variants
    ("admin@test.com", "Test@1234", "Admin (create_test_users.py)"),
    ("admin@test.com", "admin123", "Admin (seed.py)"),
]

print("=== Testing Login Credentials ===\n")
for email, password, label in combos:
    result = try_login(email, password)
    print(f"  [{label}] {email} / {password}")
    print(f"    → {result}")
    print()
