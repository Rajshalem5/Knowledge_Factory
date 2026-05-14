#!/usr/bin/env python3
"""Check Divya's current status and try assessment."""
import urllib.request, json, time

BASE = "http://localhost:8000"
def api(method, path, body=None, token=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            b = resp.read().decode()
            return resp.status, json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        b = e.read().decode() if e.fp else "{}"
        try: return e.code, json.loads(b)
        except: return e.code, {"detail": b}
    except Exception as e:
        return 0, {"error": str(e)}

# Login
s, d = api("POST", "/api/auth/login", {"email":"divya@test.com","password":"Candidate@123"})
tok = d.get("access_token","")
print(f"Login: {s}, token={'yes' if tok else 'no'}")
if not tok:
    exit()

# /me
s, d = api("GET", "/api/candidates/me", token=tok)
print(f"Status: {d.get('status','?')}")
print(f"All: {json.dumps(d, indent=2)[:500]}")

# Try assessment start
s, d = api("POST", "/api/assessment/start", {"round":"ROUND_2"}, token=tok)
print(f"\nAssessment start: {s}")
print(f"Detail: {d}")

# Try starting an assessment for ROUND_3 
s, d = api("POST", "/api/assessment/start", {"round":"ROUND_3"}, token=tok)
print(f"\nAssessment start ROUND_3: {s}")
print(f"Detail: {d}")

# Check all her assessments via admin
s2, d2 = api("POST", "/api/auth/login", {"email":"admin@knowledgefactory.io","password":"admin123"})
admin_tok = d2.get("access_token","")
if admin_tok:
    # Get divya's candidate id
    cid = d.get("id","")
    if cid:
        s3, d3 = api("GET", f"/api/candidates/{cid}", token=admin_tok)
        print(f"\nAdmin view candidate: {s3}")
        print(f"  Status: {d3.get('status','')}")
        print(f"  Full: {json.dumps(d3, indent=2)[:300]}")
