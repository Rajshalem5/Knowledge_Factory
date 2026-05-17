#!/usr/bin/env python3
"""Test role-based API access for all roles."""
import json, urllib.request, urllib.error

roles = {
    'superadmin': ('superadmin@knowledgefactory.io', 'Super@12345'),
    'hr': ('hr@knowledgefactory.io', 'Hr@12345'),
    'interviewer': ('interviewer@test.com', 'Interviewer@12345'),
    'candidate': ('candidate@test.com', 'Candidate@12345'),
    'admin': ('admin@knowledgefactory.io', 'admin123'),
}

tokens = {}
for role, (email, pw) in roles.items():
    data = json.dumps({'email': email, 'password': pw}).encode()
    req = urllib.request.Request('http://localhost:8000/api/auth/login', data=data,
                                  headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            token = body.get('access_token', body.get('token', ''))
            tokens[role] = token
    except Exception as e:
        print(f"  ❌ {role}: {e}")

for role, token in tokens.items():
    headers = {'Authorization': f'Bearer {token}'}
    print(f"\n  --- {role} ---")
    
    # Candidates
    req = urllib.request.Request('http://localhost:8000/api/candidates', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            count = len(data) if isinstance(data, list) else len(data.get('candidates', data.get('data', [])))
            print(f"    ✅ /api/candidates -> {count} items")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:100]
        print(f"    {'⚠️' if e.code == 403 else '❌'} /api/candidates -> {e.code}: {body}")
    
    # Analytics funnel
    req = urllib.request.Request('http://localhost:8000/api/analytics/funnel', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"    ✅ /api/analytics/funnel -> OK")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:100]
        print(f"    {'⚠️' if e.code == 403 else '❌'} /api/analytics/funnel -> {e.code}: {body}")
    
    # Auth me
    req = urllib.request.Request('http://localhost:8000/api/auth/me', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"    ✅ /api/auth/me -> {data.get('role', '?')}")
    except Exception as e:
        print(f"    ❌ /api/auth/me -> {e}")

print("\n  Done!")
