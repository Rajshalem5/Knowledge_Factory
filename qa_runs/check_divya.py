#!/usr/bin/env python3
"""Check Divya's assessment status."""
import urllib.request, json

BASE_URL = "http://localhost:8000"

def login():
    s,d = _req("POST", "/api/auth/login", {"email":"divya@test.com","password":"Candidate@123"})
    return d.get("access_token","")

def _req(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode()) if resp.read() else {}
    except urllib.error.HTTPError as e:
        b = e.read().decode() if e.fp else "{}"
        try: return e.code, json.loads(b)
        except: return e.code, {"detail": b}
    except Exception as e:
        return 0, {"error": str(e)}

token = login()
print(f"Divya token: {'yes' if token else 'no'}")

# Check Divya's profile
s,d = _req("GET", "/api/candidates/me", token=token)
print(f"Candidate /me: {s}")
if s == 200:
    print(f"  ID: {d.get('id','')}")
    print(f"  Status: {d.get('status','')}")
    print(f"  Name: {d.get('name','')}")

# Try starting ROUND_2 assessment
s,d = _req("POST", "/api/assessment/start", {"round":"ROUND_2"}, token=token)
print(f"\nAssessment start: {s}")
print(f"  Detail: {d.get('detail','')}")
print(f"  Full: {d}")

# Check if there's already an active assessment
s,d = _req("GET", "/api/assessment/", token=token)
print(f"\nAssessment list: {s}")
print(f"  {d}")

# Try from admin perspective to see candidate assessments
s2,d2 = _req("POST", "/api/auth/login", {"email":"admin@knowledgefactory.io","password":"admin123"})
admin_token = d2.get("access_token","")
s3,d3 = _req("GET", "/api/candidates/?status=ROUND1_PASSED", token=admin_token)
print(f"\nCandidates with ROUND1_PASSED: {s3}")
if s3 == 200:
    cl = d3.get("data") or d3.get("candidates") or d3
    if isinstance(cl, list):
        for c in cl:
            if c.get('email','').startswith('divya'):
                print(f"  {c.get('email')}: status={c.get('status')}, id={c.get('id')}")
