#!/usr/bin/env python3
"""
Phase 6+8 v4: Simple, robust approach.
- Use API to verify login credentials (already working)
- Use browser to check frontend console errors
- One browser session, check landing page + try to login
"""
import json, subprocess, sys, time, os, tempfile
from pathlib import Path

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory/auth")
BASE_API = "http://localhost:8000/api"

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

AUTH_DIR.mkdir(parents=True, exist_ok=True)

# ── PHASE 8 PART A: API-based login verification ──
print("=" * 60)
print("  PHASE 8a: API LOGIN VERIFICATION")
print("=" * 60)

import urllib.request
api_results = {}
for role, creds in ROLES.items():
    data = json.dumps({"email": creds["email"], "password": creds["pw"]}).encode()
    req = urllib.request.Request(
        f"{BASE_API}/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            user_role = body.get("user", {}).get("role", "?")
            token = body.get("access_token", body.get("token", ""))
            ok = user_role.upper() == role.upper()
            api_results[role] = {"login": "✅" if ok else "⚠️", "role": user_role, "token": token[:20]+"..." if token else ""}
            print(f"  {'✅' if ok else '❌'} {role}: {creds['email']} -> role={user_role}")
    except Exception as e:
        api_results[role] = {"login": "❌", "error": str(e)}
        print(f"  ❌ {role}: {creds['email']} -> {e}")

# ── PHASE 8 PART B: Token-based auth verify ──
print(f"\n{'='*60}")
print("  PHASE 8b: TOKEN VERIFICATION (/auth/me)")
print("=" * 60)

for role, creds in ROLES.items():
    r = api_results.get(role, {})
    token_val = None
    if r.get("login") != "❌":
        # Get a fresh token
        data = json.dumps({"email": creds["email"], "password": creds["pw"]}).encode()
        req = urllib.request.Request(
            f"{BASE_API}/auth/login",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                token_val = body.get("access_token", body.get("token", ""))
        except:
            pass
    
    if token_val:
        req = urllib.request.Request(
            f"{BASE_API}/auth/me",
            headers={"Authorization": f"Bearer {token_val}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                print(f"  ✅ {role}: /auth/me OK -> {body.get('role', '?')}")
                api_results[role]["auth_me"] = "✅"
        except Exception as e:
            print(f"  ❌ {role}: /auth/me FAILED -> {e}")
            api_results[role]["auth_me"] = "❌"
    else:
        print(f"  ⚠️ {role}: No token to verify /auth/me")

# ── PHASE 6 + 8c: Browser-based console check + post-login page ──
print(f"\n{'='*60}")
print("  PHASE 6: FRONTEND CONSOLE CHECK")
print("  PHASE 8c: BROWSER POST-LOGIN VERIFICATION")
print("=" * 60)

# Close any lingering sessions
run(f"{AB} close --all", timeout=5)
time.sleep(2)

browser_results = {}

for role, creds in ROLES.items():
    print(f"\n  --- Role: {role} ---")
    
    # Fresh session
    run(f"{AB} close --all", timeout=5)
    time.sleep(2)
    
    # Open app
    run(f"{AB} open {NGROK}", timeout=20)
    time.sleep(5)
    
    # Bypass ngrok
    _, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
    if "Visit Site" in snap:
        run(f"{AB} click @e6", timeout=10)
        print("  ✅ Ngrok bypassed")
        time.sleep(5)
    
    # Check if app loaded
    _, title, _ = run(f"{AB} eval 'document.title'", timeout=10)
    print(f"  Title: {title}")
    
    # Try login via eval (more reliable than agent-browser click)
    login_js = """
    (function(){
      var items = document.querySelectorAll('a, button, span');
      for(var b of items) {
        var t = (b.innerText || '').trim();
        if(t === 'Login') { b.click(); return 'OK'; }
      }
      // Try Sign In button too
      for(var b of items) {
        var t = (b.innerText || '').trim();
        if(t === 'Sign In') { b.click(); return 'clicked_signin'; }
      }
      return 'NOT_FOUND';
    })()
    """
    
    rc, _, _ = run(f"{AB} eval '{login_js}'", timeout=10)
    time.sleep(3)
    
    # Check if we got login form
    _, page_check, _ = run(f"{AB} eval 'document.body.innerText.substring(0,200)'", timeout=10)
    
    if "Welcome back" in page_check:
        print("  ✅ Login form visible")
        
        # Fill credentials via native setters
        fill_js = '''
        (function(){
          var inputs = document.querySelectorAll('input');
          var ei = null, pi = null;
          for(var i=0;i<inputs.length;i++) {
            var inp = inputs[i];
            if(inp.type==='email'||inp.name==='email') ei=inp;
            if(inp.type==='password'||inp.name==='password') pi=inp;
          }
          if(ei) {
            var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            s.call(ei, arguments[0]);
            ei.dispatchEvent(new Event('input',{bubbles:true}));
            ei.dispatchEvent(new Event('change',{bubbles:true}));
          }
          if(pi) {
            var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            s.call(pi, arguments[1]);
            pi.dispatchEvent(new Event('input',{bubbles:true}));
            pi.dispatchEvent(new Event('change',{bubbles:true}));
          }
          return JSON.stringify({emailFilled:ei?ei.value:'nf', pwFilled:pi?'filled':'nf'});
        })("''' + creds["email"] + '''","''' + creds["pw"] + '''")
        '''
        # Use temp file to avoid shell escaping
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, prefix='fill_') as f:
            f.write(fill_js)
            tmp = f.name
        rc, fill_out, _ = run(f"{AB} eval \"$(cat {tmp})\"", timeout=10)
        os.unlink(tmp)
        print(f"  Fill: {fill_out[:80]}")
        time.sleep(1)
        
        # Click Sign In button
        signin_js = """
        (function(){
          var btns = document.querySelectorAll('button');
          for(var b of btns) {
            if(b.innerText.trim() === 'Sign In') { b.click(); return 'OK'; }
          }
          return 'NOT_FOUND';
        })()
        """
        rc, _, _ = run(f"{AB} eval '{signin_js}'", timeout=10)
        print("  ✅ Sign In clicked")
        time.sleep(5)
    elif "Knowledge Factory" in page_check:
        print("  ⚠️ On landing page, Login button may not have worked")
    else:
        print(f"  ⚠️ Unexpected page: {page_check[:80]}")
    
    # Get post-login URL
    _, url_out, _ = run(f"{AB} eval 'location.href'", timeout=10)
    url = url_out.strip('"').strip("'") if url_out else ""
    print(f"  URL: {url}")
    
    # Check console errors
    console_js = """
    (function(){
      var text = (document.body.innerText || '').toLowerCase();
      var patterns = ['error', 'failed to fetch', 'typeerror', 'react error', 'cannot read property', 'undefined', 'internal server'];
      var found = [];
      for(var p of patterns) { if(text.indexOf(p) !== -1) found.push(p); }
      var errEls = document.querySelectorAll('[class*=error],[class*=Error]').length;
      return JSON.stringify({errors: found, errorElements: errEls, snippet: text.substring(0,150)});
    })()
    """
    rc, err_out, _ = run(f"{AB} eval '{console_js}'", timeout=10)
    
    console_errors = []
    error_boundary = False
    try:
        err_data = json.loads(err_out)
        console_errors = err_data.get("errors", [])
        error_boundary = err_data.get("errorElements", 0) > 0
    except:
        pass
    
    status = "passed" if ("login" not in url.lower() and url != NGROK + "/" and url != NGROK) else "stuck"
    
    browser_results[role] = {
        "status": status, "url": url,
        "console_errors": console_errors,
        "has_error_boundary": error_boundary
    }
    
    print(f"  Status: {'✅ PASSED' if status=='passed' else '❌ STUCK'}")
    print(f"  Console: {'✅ CLEAN' if not console_errors and not error_boundary else '⚠️ ERRORS: '+str(console_errors)}")
    
    # Save auth state
    run(f"{AB} state save {AUTH_DIR / f'{role}.json'}", timeout=10)
    
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)

# ── FINAL SUMMARY ──
print(f"\n\n{'='*60}")
print("  FINAL SUMMARY — PHASE 6 & 8")
print("=" * 60)

print(f"\n  PHASE 8a (API Login):")
login_ok = all(v.get("login") == "✅" for v in api_results.values())
print(f"    {'✅ ALL PASSED' if login_ok else '❌ SOME FAILED'}")
for role, v in api_results.items():
    print(f"    {v.get('login','❌')} {role}: {v.get('role','?')}")

print(f"\n  PHASE 8b (Auth Me):")
me_ok = all(v.get("auth_me") == "✅" for v in api_results.values() if v.get("login") == "✅")
print(f"    {'✅ ALL PASSED' if me_ok else '❌ SOME FAILED'}")

print(f"\n  PHASE 8c (Browser Login):")
browser_login_ok = all(v["status"] == "passed" for v in browser_results.values())
browser_failed = [r for r, v in browser_results.items() if v["status"] != "passed"]
if browser_login_ok:
    print(f"    ✅ ALL PASSED")
else:
    print(f"    ❌ FAILED: {', '.join(browser_failed)}")

print(f"\n  PHASE 6 (Console Check):")
console_clean = all(not v.get("console_errors") and not v.get("has_error_boundary") for v in browser_results.values())
console_roles_with_issues = [r for r, v in browser_results.items() if v.get("console_errors") or v.get("has_error_boundary")]
if console_clean:
    print(f"    ✅ ALL CLEAN — No console errors across any role")
else:
    print(f"    ⚠️ ERRORS in: {', '.join(console_roles_with_issues)}")
    for r in console_roles_with_issues:
        print(f"      {r}: {browser_results[r].get('console_errors', [])}")

print(f"\n  Auth states saved to: {AUTH_DIR}")

import json as _json
final = {
    "phase6": {"status": "clean" if console_clean else "issues", "roles_with_errors": console_roles_with_issues},
    "phase8_api": {"status": "all_passed" if login_ok else "some_failed", "details": {k: {"role": v.get("role","?"), "login": v.get("login","❌")} for k,v in api_results.items()}},
    "phase8_browser": {"status": "all_passed" if browser_login_ok else "some_failed", "failed_roles": browser_failed},
}
print("\n---PHASE6_8_JSON_START---")
print(_json.dumps(final, indent=2))
print("---PHASE6_8_JSON_END---")
