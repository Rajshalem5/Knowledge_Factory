#!/usr/bin/env python3
"""Refresh auth tokens and save to auth state files."""
import json, os, subprocess

BASE = "http://localhost:8000"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"

logins = {
    "superadmin": ("admin@knowledgefactory.com", "Admin123!"),
    "admin": ("admin@knowledgefactory.com", "Admin123!"),
    "hr": ("hr@knowledgefactory.com", "HR123!"),
    "interviewer": ("interviewer@knowledgefactory.com", "Interview123!"),
    "candidate": ("candidate1@student.edu", "Candidate123!"),
}

for role, (email, password) in logins.items():
    cmd = f'curl -s -X POST {BASE}/api/auth/login -H "Content-Type: application/json" -d \'{{"email":"{email}","password":"{password}"}}\''
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    token = data.get("access_token", data.get("token", ""))
    role_data = data.get("user", {}).get("role", role.upper())
    
    state = {"token": token, "email": email, "role": role_data}
    with open(f"{AUTH_DIR}/{role}.json", "w") as f:
        json.dump(state, f)
    print(f"{role}: OK (token: {token[:20]}... role: {role_data})")

print("\nAll tokens refreshed!")
