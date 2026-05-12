"""Test candidate listing and auth endpoints against running dev server."""
import sys, json, os

import httpx

BASE = "http://localhost:8000"

# ── Auth Tests ────────────────────────────────────────────────────────

test_accounts = [
    ("superadmin@knowledgefactory.io", "Super@12345", "SUPERADMIN"),
    ("admin@knowledgefactory.io", "admin123", "ADMIN"),
    ("hr@knowledgefactory.io", "Hr@12345", "HR"),
    ("interviewer@knowledgefactory.io", "Interview@12345", "INTERVIEWER"),
    ("admin@test.com", "Test@123", "ADMIN"),
    ("hr@test.com", "Test@123", "HR"),
    ("interviewer@test.com", "Test@123", "INTERVIEWER"),
    ("alice@test.com", "Candidate@123", "CANDIDATE"),
]

all_ok = True
tokens = {}
for email, password, expected_role in test_accounts:
    r = httpx.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
    ok = r.status_code == 200
    if ok:
        data = r.json()
        actual_role = data.get("user", {}).get("role", "")
        role_ok = actual_role == expected_role
        print(f"  LOGIN {email:40} | {'PASS' if ok else 'FAIL'} | role={actual_role:15} | {'✓' if role_ok else '✗ role mismatch'}")
        if role_ok:
            tokens[email] = data["access_token"]
        else:
            all_ok = False
    else:
        print(f"  LOGIN {email:40} | FAIL | {r.text[:80]}")
        all_ok = False

# ── Candidate Listing ─────────────────────────────────────────────────

admin_token = tokens.get("admin@knowledgefactory.io")
if admin_token:
    r = httpx.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"\n  GET /api/candidates/ (admin): {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", data.get("candidates", []))
        print(f"    Count: {len(items)}")
        all_ok = True
    else:
        print(f"    Error: {r.text[:200]}")
        all_ok = False

hr_token = tokens.get("hr@knowledgefactory.io")
if hr_token:
    r = httpx.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {hr_token}"})
    print(f"  GET /api/candidates/ (hr): {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", data.get("candidates", []))
        print(f"    Count: {len(items)}")
    else:
        print(f"    Error: {r.text[:200]}")
        all_ok = False

# ── Candidate Me ──────────────────────────────────────────────────────
candidate_token = tokens.get("alice@test.com")
if candidate_token:
    r = httpx.get(f"{BASE}/api/candidates/me", headers={"Authorization": f"Bearer {candidate_token}"})
    print(f"  GET /api/candidates/me: {r.status_code}")
    if r.status_code == 200:
        print(f"    Name: {r.json().get('name')}")
    else:
        print(f"    Error: {r.text[:200]}")
        all_ok = False

print(f"\n{'='*50}")
print(f"OVERALL: {'ALL PASS' if all_ok else 'SOME FAILED'}")
