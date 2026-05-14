#!/usr/bin/env python3
"""Test login with seed.py credentials."""
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
            j = json.loads(body)
            role = j.get("role", "?")
            print(f"  ✅ {email} (pwd='{password}'): OK role={role}")
            return (True, j.get("access_token", ""), role)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  ❌ {email} (pwd='{password}'): {e.code}")
        return (False, None, None)
    except Exception as e:
        print(f"  💥 {email}: {e}")
        return (False, None, None)

print("=== Testing seed.py passwords ===\n")

# Staff from seed.py
test_login("superadmin@knowledgefactory.io", "Super@12345")
test_login("admin@knowledgefactory.io", "admin123")
test_login("hr@knowledgefactory.io", "Hr@12345")
test_login("interviewer@knowledgefactory.io", "Interview@12345")

# Candidates from seed.py  
test_login("alice@test.com", "Candidate@123")
test_login("bob@test.com", "Candidate@123")
test_login("charlie@test.com", "Candidate@123")
test_login("divya@test.com", "Candidate@123")
test_login("esha@test.com", "Candidate@123")

# Also test the candidate@test.com which exists in candidates table
# This was registered via the registration form
# Try common registration passwords
test_login("candidate@test.com", "Test@12345")
test_login("candidate@test.com", "Candidate@123")
test_login("candidate@test.com", "Candidate@12345")

print("\n=== Testing @test.com staff (with seed passwords) ===")
test_login("admin@test.com", "admin123")
test_login("hr@test.com", "Hr@12345")
test_login("interviewer@test.com", "Interview@12345")
