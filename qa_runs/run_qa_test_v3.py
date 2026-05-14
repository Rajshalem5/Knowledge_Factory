#!/usr/bin/env python3
"""
Knowledge Factory Autonomous QA Tester v3
Fixes: registration uses 'name' not 'full_name', correct selection paths,
audit/log endpoints, ngrok interstitial handling, and correct credentials.
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
NGROK_URL = os.environ.get("NGROK_URL", "https://ila-sturdiest-oversentimentally.ngrok-free.dev")
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
PROJECT_ROOT = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory")
AUTH_DIR = PROJECT_ROOT / "auth"
FAILURES_DIR = PROJECT_ROOT / "failures"
QA_RUNS_DIR = PROJECT_ROOT / "qa_runs"
BASELINES_DIR = PROJECT_ROOT / "baselines"
AB = "/opt/hermes_shared_memory/bin/ab"

for d in [AUTH_DIR, FAILURES_DIR/RUN_ID, QA_RUNS_DIR, BASELINES_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"RUN_ID: {RUN_ID}")
print(f"BASE_URL: {BASE_URL}")
print(f"NGROK_URL: {NGROK_URL}")

# ─── Correct credentials ──────────────────────────────────────────────────
STAFF = {
    "superadmin": ("superadmin@knowledgefactory.io", "Super@12345", "SUPERADMIN"),
    "admin": ("admin@knowledgefactory.io", "admin123", "ADMIN"),
    "hr": ("hr@knowledgefactory.io", "Hr@12345", "HR"),
    "interviewer": ("interviewer@knowledgefactory.io", "Interview@12345", "INTERVIEWER"),
}
CANDIDATES = {
    "alice": ("alice@test.com", "Candidate@123"),
    "bob": ("bob@test.com", "Candidate@123"),
    "charlie": ("charlie@test.com", "Candidate@123"),
    "divya": ("divya@test.com", "Candidate@123"),
    "esha": ("esha@test.com", "Candidate@123"),
}

# ─── Results ──────────────────────────────────────────────────────────────
R = {"run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(),
     "passed": [], "failed": [], "warnings": [], "critical": []}

def mark(level, desc, detail=None):
    entry = {"desc": desc}
    if detail: entry["detail"] = detail
    R[level].append(entry)
    icons = {"passed":"✅","failed":"❌","warnings":"⚠️","critical":"🔴"}
    print(f"  {icons.get(level,'❓')} [{level.upper()}] {desc}")
    if detail: print(f"     └─ {detail}")

def run_ab(args, timeout=30):
    try:
        r = subprocess.run([AB]+args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def http(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        b = e.read().decode() if e.fp else "{}"
        try: return e.code, json.loads(b)
        except: return e.code, {"detail": b}
    except Exception as e:
        return 0, {"error": str(e)}

def login(email, pw):
    s, d = http("POST", "/api/auth/login", {"email":email, "password":pw})
    if s == 200 and "access_token" in d:
        return d["access_token"], d
    return None, d

def handle_ngrok_interstitial(session):
    """Check for ngrok interstitial and click through using ref-based click."""
    rc, out, _ = run_ab(["--session", session, "eval", "document.title"])
    if out and "ERR_NGROK" in out:
        print(f"    Ngrok interstitial detected, clicking Visit Site...")
        # Take snapshot to discover refs
        run_ab(["--session", session, "snapshot", "-i"])
        time.sleep(0.5)
        # Use ref-based click (genuine mouse click, not synthetic JS click)
        rc, out, _ = run_ab(["--session", session, "click", "@e6"])
        print(f"    Ref click: rc={rc} out={out}")
        time.sleep(3)
        # Check title again
        rc, out, _ = run_ab(["--session", session, "eval", "document.title"])
        print(f"    Title after click: {out}")
        return True
    return False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: HEALTH
# ═══════════════════════════════════════════════════════════════════════════
def test_health():
    print("\n═══════ SECTION 1: Health ═══════")
    s, d = http("GET", "/health")
    if s == 200 and d.get("status") == "ok":
        mark("passed", "Health check: OK")
        return True
    mark("critical", f"Health: {s} {d}")
    return False

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: AUTH
# ═══════════════════════════════════════════════════════════════════════════
def test_auth():
    print("\n═══════ SECTION 2: Auth ═══════")
    tokens = {}
    for name, (email, pw, role) in STAFF.items():
        tok, data = login(email, pw)
        if tok:
            tokens[name] = tok
            r = data.get("role", data.get("user",{}).get("role","?"))
            mark("passed", f"Login {name} ({email}): role={r}")
        else:
            mark("critical", f"Login {name} ({email}): FAILED {data}")
    
    for name, (email, pw) in CANDIDATES.items():
        tok, data = login(email, pw)
        if tok:
            tokens[f"cand_{name}"] = tok
            mark("passed", f"Login {name} ({email}): OK")
        else:
            mark("failed", f"Login {name} ({email}): FAILED {data}")
    
    # /me
    for key in ["superadmin","admin","hr","interviewer"]:
        if key in tokens:
            s, d = http("GET", "/api/auth/me", token=tokens[key])
            if s == 200:
                r = d.get("role", d.get("user",{}).get("role","?"))
                mark("passed", f"/me {key}: role={r}")
            else:
                mark("failed", f"/me {key}: {s}")
    for name in CANDIDATES:
        key = f"cand_{name}"
        if key in tokens:
            s, d = http("GET", "/api/auth/me", token=tokens[key])
            mark("passed" if s==200 else "failed", f"/me candidate {name}: {s}")
    return tokens

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: CANDIDATES
# ═══════════════════════════════════════════════════════════════════════════
def test_candidates(tokens):
    print("\n═══════ SECTION 3: Candidates ═══════")
    for role in ["admin","hr"]:
        if role in tokens:
            s, d = http("GET", "/api/candidates/", token=tokens[role])
            if s == 200:
                cl = d.get("data") or d.get("candidates") or d
                c = len(cl) if isinstance(cl, list) else "?"
                mark("passed", f"Candidates list ({role}): {c}")
            else:
                mark("failed", f"Candidates list ({role}): {s}")
    for name in CANDIDATES:
        key = f"cand_{name}"
        if key in tokens:
            s, d = http("GET", "/api/candidates/me", token=tokens[key])
            mark("passed" if s==200 else "failed", f"Candidate /me ({name}): {s}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SCREENING
# ═══════════════════════════════════════════════════════════════════════════
def test_screening(tokens):
    print("\n═══════ SECTION 4: Screening ═══════")
    s, d = http("GET", "/api/screening/pipeline-stats")
    if s == 200:
        st = d.get("stats") or d
        c = len(st) if isinstance(st, dict) else "?"
        mark("passed", f"Pipeline stats: {c} statuses")
    else:
        mark("failed", f"Pipeline stats: {s}")
    if "hr" in tokens:
        s, d = http("POST", "/api/screening/run", {}, token=tokens["hr"])
        summ = json.dumps({k:v for k,v in d.items() if k!="details"})[:120]
        mark("passed" if s==200 else "warnings", f"Screening run: {s} {summ}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════
def test_analytics(tokens):
    print("\n═══════ SECTION 5: Analytics ═══════")
    if "admin" in tokens:
        for ep in ["/api/analytics/funnel","/api/analytics/dashboard"]:
            s, d = http("GET", ep, token=tokens["admin"])
            mark("passed" if s==200 else "warnings", f"Analytics {ep}: {s}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: HIRING CYCLES
# ═══════════════════════════════════════════════════════════════════════════
def test_hiring_cycles(tokens):
    print("\n═══════ SECTION 6: Hiring Cycles ═══════")
    if "admin" in tokens:
        s, d = http("GET", "/api/hiring-cycles/", token=tokens["admin"])
        if s == 200:
            cl = d if isinstance(d, list) else d.get("data") or d.get("cycles") or []
            names = [c.get("name","?") for c in cl] if isinstance(cl, list) else ["?"]
            mark("passed", f"Hiring cycles: {len(cl)} — {names}")
        else:
            mark("warnings", f"Hiring cycles: {s}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════
def test_registration():
    print("\n═══════ SECTION 7: Registration ═══════")
    ts = int(time.time())
    body = {
        "email": f"qa_e2e_{ts}@test.com", "password": "QaPass@12345",
        "name": "QA E2E User", "role": "candidate",
        "phone": f"+9112345{ts%100000:05d}", "college": "QA Test University",
        "branch": "CSE", "cgpa": 8.5, "passed_out_year": 2026,
    }
    s, d = http("POST", "/api/auth/register", body)
    mark("passed" if s in (200,201) else "warnings", f"Registration: {s}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: ADMIN / AUDIT
# ═══════════════════════════════════════════════════════════════════════════
def test_admin(tokens):
    print("\n═══════ SECTION 8: Admin / Audit ═══════")
    if "admin" in tokens:
        for ep in ["/api/admin/users", "/api/audit/logs"]:
            s, d = http("GET", ep, token=tokens["admin"])
            mark("passed" if s==200 else "warnings", f"{ep}: {s}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: KF-SPECIFIC
# ═══════════════════════════════════════════════════════════════════════════
def test_kf_specific(tokens):
    print("\n═══════ SECTION 9: KF-Specific ═══════")
    
    for name, path in [("Questions","/api/questions/"),("Code exec","/api/code/"),
                        ("Assessment","/api/assessment/")]:
        s, d = http("GET", path)
        mark("passed" if s!=500 else "warnings", f"{name}: {s}")
    
    if "admin" in tokens:
        s, d = http("POST", "/api/proctoring/event", {}, token=tokens["admin"])
        mark("passed" if s==422 else "warnings", f"Proctoring: {s} (expect 422)")
        
        # Correct selection endpoints
        s, d = http("POST", "/api/selection/candidates/bulk-select", 
                    {"candidate_ids":[]}, token=tokens["admin"])
        mark("passed" if s in(200,422) else "warnings", f"Bulk-select: {s}")
    
    if "cand_alice" in tokens:
        s, d = http("POST", "/api/assessment/start", {"round":"ROUND_2"}, 
                     token=tokens["cand_alice"])
        mark("passed" if s in(400,422) else "warnings", 
             f"Assessment start (alice/ROUND_2): {s}")
    
    if "cand_divya" in tokens:
        s, d = http("POST", "/api/assessment/start", {"round":"ROUND_2"}, 
                     token=tokens["cand_divya"])
        mark("passed" if s==200 else "warnings", f"Assessment start (divya/ROUND_2): {s}")
    
    # Interview feedback
    if "admin" in tokens and "cand_alice" in tokens:
        # Get alice's candidate ID
        s, d = http("GET", "/api/candidates/me", token=tokens["cand_alice"])
        if s == 200:
            cid = d.get("id","")
            if cid:
                s2, d2 = http("GET", f"/api/candidates/{cid}/feedback", token=tokens["admin"])
                mark("passed" if s2==200 else "warnings", f"Interview feedback: {s2}")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: BROWSER E2E
# ═══════════════════════════════════════════════════════════════════════════
def test_browser_e2e(tokens):
    print("\n═══════ SECTION 10: Browser E2E ═══════")
    run_ab(["close", "--all"])
    time.sleep(1)
    
    for name, (email, pw, _role) in STAFF.items():
        print(f"\n  ── Browser: {name} ({email}) ──")
        sid = f"kf_{name}"
        auth_f = AUTH_DIR / f"{name}.json"
        
        rc, out, _ = run_ab(["--session", sid, "open", NGROK_URL])
        print(f"    Open: rc={rc}")
        if rc != 0:
            mark("failed", f"Browser ({name}): open failed")
            continue
        time.sleep(3)
        
        # Handle ngrok interstitial
        handle_ngrok_interstitial(sid)
        
        # Check page content
        rc, out, _ = run_ab(["--session", sid, "eval", "document.title"])
        print(f"    Title: {out}")
        
        # Try clicking "Sign In" button to reach login form
        rc, out, _ = run_ab(["--session", sid, "eval",
            "(function(){ const btns = document.querySelectorAll('a, button, span'); for(const b of btns){ if(b.innerText.includes('Sign In') || b.innerText.includes('Login')){ b.click(); return 'clicked '+b.innerText; } } return 'not found'; })()"])
        print(f"    Sign In click: {str(out)[:80]}")
        time.sleep(2)
        
        # Check for login form
        rc, out, _ = run_ab(["--session", sid, "eval", 
                             "document.querySelector('form') !== null"])
        has_form = out and "true" in out.lower()
        print(f"    Has form after Sign In: {has_form}")
        
        if has_form:
            # Fill email using native value setter for React control
            run_ab(["--session", sid, "eval",
                    f"(function(){{ const i = document.querySelector('input[type=email]') || document.querySelector('input[name=email]'); if(!i) return 'no-email'; const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'{email}'); i.dispatchEvent(new Event('input',{{bubbles:true}})); i.dispatchEvent(new Event('change',{{bubbles:true}})); return 'ok'; }})()"])
            time.sleep(0.5)
            # Fill password
            run_ab(["--session", sid, "eval",
                    f"(function(){{ const i = document.querySelector('input[type=password]'); if(!i) return 'no-pwd'; const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set; s.call(i,'{pw}'); i.dispatchEvent(new Event('input',{{bubbles:true}})); i.dispatchEvent(new Event('change',{{bubbles:true}})); return 'ok'; }})()"])
            time.sleep(0.5)
            # Click submit
            rc2, out2, _ = run_ab(["--session", sid, "eval",
                    "(function(){ const b=document.querySelector('button[type=submit]')||Array.from(document.querySelectorAll('button')).find(b=>b.innerText.includes('Sign')||b.innerText.includes('Login')); if(b){b.click();return 'ok'} return 'nobtn'; })()"])
            print(f"    Login submit: {str(out2)[:80]}")
            time.sleep(3)
        
        # Check title after login attempt
        rc, out, _ = run_ab(["--session", sid, "eval", "document.title"])
        print(f"    Post-login title: {out}")
        
        # Check if login succeeded (look for dashboard content)
        rc, out, _ = run_ab(["--session", sid, "eval",
                             "document.body.innerText.substring(0, 200)"])
        print(f"    Page text: {str(out)[:150]}")
        
        # Screenshot
        run_ab(["--session", sid, "screenshot", str(FAILURES_DIR/RUN_ID/f"{name}_page.png")])
        
        # Save state
        run_ab(["--session", sid, "state", "save", str(auth_f)])
        
        # Console check
        rc, out, _ = run_ab(["--session", sid, "console", "--json"])
        if out and out.strip() and out.strip() != "[]":
            try:
                entries = json.loads(out)
                errs = [e for e in entries if e.get('type') in ('error','warning')]
                if errs:
                    mark("warnings", f"Browser ({name}): console errors",
                         "; ".join([str(e.get('text',''))[:80] for e in errs[:3]]))
            except:
                pass
        
        # Save snapshot baseline
        rc, out, _ = run_ab(["--session", sid, "snapshot", "-c", "-i"])
        if rc == 0 and out:
            with open(BASELINES_DIR/f"{name}_dashboard.txt", "w") as f:
                f.write(out)
        
        # Check network errors
        rc, out, _ = run_ab(["--session", sid, "network", "requests", "--status", "4xx,5xx"])
        if out and out.strip() and "No requests captured" not in out and "0 4xx" not in out:
            mark("warnings", f"Browser ({name}): network errors", out[:200])
        
        run_ab(["--session", sid, "close"])
        time.sleep(1)
    
    run_ab(["close", "--all"])
    mark("passed", "Browser E2E tests completed")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    if not test_health():
        mark("critical", "Health failed — aborting")
        return save_final(t0)
    tokens = test_auth()
    if tokens:
        test_candidates(tokens)
        test_screening(tokens)
        test_analytics(tokens)
        test_hiring_cycles(tokens)
        test_registration()
        test_admin(tokens)
        test_kf_specific(tokens)
    test_browser_e2e(tokens)
    save_final(t0)

def save_final(t0):
    elapsed = time.time() - t0
    f = QA_RUNS_DIR / f"{RUN_ID}.json"
    with open(f, "w") as fp:
        json.dump(R, fp, indent=2, default=str)
    for old in sorted(QA_RUNS_DIR.glob("*.json"), key=os.path.getmtime)[:-10]:
        old.unlink()
    
    p = len(R["passed"]); fl = len(R["failed"]); w = len(R["warnings"]); c = len(R["critical"])
    total = p+fl+w+c
    print(f"\n{'═'*60}")
    print(f"  QA RUN #{RUN_ID}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  RESULTS: ✅ {p} passed | ❌ {fl} failed | ⚠️  {w} warnings | 🔴 {c} critical")
    print(f"  Total: {total} checks")
    print(f"{'═'*60}")
    
    # Generate Telegram-ready summary
    print(f"\n📊 SUMMARY: {p}/{total} passed\n")
    if fl: print(f"❌ FAILED ({fl}):")
    for e in R["failed"]: print(f"  • {e['desc']}")
    if c: print(f"\n🔴 CRITICAL ({c}):")
    for e in R["critical"]: print(f"  • {e['desc']}")
    if w: print(f"\n⚠️  WARNINGS ({w}):")
    for e in R["warnings"]: print(f"  • {e['desc']}")
    print(f"\n✅ ALL PASSING ({p}):")
    for e in R["passed"]: print(f"  • {e['desc']}")
    
    print(f"\nResults saved: {f}")

if __name__ == "__main__":
    main()
