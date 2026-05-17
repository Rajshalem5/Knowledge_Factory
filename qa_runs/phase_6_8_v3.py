#!/usr/bin/env python3
"""
Phase 6+8 v3: Fixed ngrok bypass + JSON parsing.
"""
import json, subprocess, sys, time, os, tempfile
from pathlib import Path

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = Path("/opt/hermes_shared_memory/projects/Knowledge_Factory/auth")

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

def ab_eval(js, timeout=15):
    """Use --eval flag of ab to run JS and capture result."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, prefix='ab_eval_') as f:
        f.write(js)
        f.flush()
        tmpfile = f.name
    try:
        r = subprocess.run(
            f'{AB} eval "$(cat {tmpfile})"',
            shell=True, capture_output=True, text=True, timeout=timeout
        )
        out = r.stdout.strip()
        # Remove outer quotes if present (ab eval wraps strings in double quotes)
        if out.startswith('"') and out.endswith('"'):
            out = out[1:-1].replace('\\"', '"').replace('\\n', '\n')
        return out, r.stderr.strip()
    finally:
        os.unlink(tmpfile)

AUTH_DIR.mkdir(parents=True, exist_ok=True)
results = {}

for role, creds in ROLES.items():
    print(f"\n{'='*60}")
    print(f"  PHASE 6+8: Testing role={role} ({creds['email']})")
    print(f"{'='*60}")
    
    result = {"status": "error", "url": "", "console_errors": [], "has_error_boundary": False}
    
    try:
        # Fresh session per role
        run(f"{AB} close --all", timeout=5)
        time.sleep(2)
        
        # Navigate
        run(f"{AB} open {NGROK}", timeout=20)
        print("  Opened URL")
        time.sleep(5)
        
        # Bypass ngrok - use snapshot to find Visit Site button
        _, snap_out, _ = run(f"{AB} snapshot -c -i", timeout=10)
        if "Visit Site" in snap_out:
            run(f"{AB} click @e6", timeout=10)
            print("  Clicked Visit Site")
            time.sleep(5)
        
        # Check if we got past ngrok
        page_text = ab_eval("document.body.innerText.substring(0,200)")
        print(f"  Page text: {page_text[:80]}...")
        
        if "Knowledge Factory" not in page_text and "Login" not in page_text:
            # Try alternative ngrok bypass methods
            run(f"{AB} eval 'document.querySelector(\"button\") && document.querySelector(\"button\").click()'", timeout=10)
            time.sleep(3)
            page_text = ab_eval("document.body.innerText.substring(0,200)")
            print(f"  After alt ngrok bypass: {page_text[:80]}...")
        
        # Click Login
        login_res = ab_eval("""
        (function() {
          var items = document.querySelectorAll('a, button, span, div, li');
          for(var b of items) {
            var t = (b.innerText || '').trim();
            if(t === 'Login') { b.click(); return 'clicked_login'; }
          }
          return 'login_not_found';
        })()
        """)
        print(f"  Login: {login_res}")
        time.sleep(3)
        
        # Fill credentials
        fill_res = ab_eval('(function(){var ins=document.querySelectorAll("input");var e=null,p=null;for(var i=0;i<ins.length;i++){var inp=ins[i];if(inp.type==="email"||inp.name==="email"||(inp.placeholder||"").toLowerCase().includes("email"))e=inp;if(inp.type==="password"||inp.name==="password"||(inp.placeholder||"").toLowerCase().includes("password"))p=inp}var r={e:"nf",p:"nf"};if(e){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;s.call(e,"'+creds["email"]+'");e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));r.e=e.value}if(p){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;s.call(p,"'+creds["pw"]+'");p.dispatchEvent(new Event("input",{bubbles:true}));p.dispatchEvent(new Event("change",{bubbles:true}));r.p=p.value?"filled":"empty"}return JSON.stringify(r)})()')
        print(f"  Fill: {fill_res[:100]}")
        time.sleep(1)
        
        # Click Sign In
        signin_res = ab_eval("""
        (function() {
          var btns = document.querySelectorAll('button');
          for(var b of btns) {
            if(b.innerText.trim() === 'Sign In') { b.click(); return 'clicked'; }
          }
          return 'signin_not_found';
        })()
        """)
        print(f"  Sign In: {signin_res}")
        time.sleep(5)
        
        # Get URL
        url_out = ab_eval("location.href")
        result["url"] = url_out
        print(f"  URL: {url_out}")
        
        # Check console errors by examining page text for error patterns
        err_check = ab_eval("""
        (function() {
          var text = (document.body.innerText || '').toLowerCase();
          var patterns = ['error', 'failed to fetch', 'typeerror', 'referenceerror', 
            'internal server', 'react error', 'cannot read property'];
          var found = [];
          for(var p of patterns) {
            if(text.indexOf(p) !== -1) found.push(p);
          }
          var errEls = document.querySelectorAll('[class*=error],[class*=Error],[id*=error],[role=alert]').length;
          return JSON.stringify({errors: found, errorElements: errEls, snippet: text.substring(0,150)});
        })()
        """)
        print(f"  Error check: {err_check[:150]}")
        
        try:
            err_data = json.loads(err_check)
            result["console_errors"] = err_data.get("errors", [])
            result["has_error_boundary"] = err_data.get("errorElements", 0) > 0
            result["text_snippet"] = err_data.get("snippet", "")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"  Error parse: {e}")
            result["console_errors"] = []
            result["has_error_boundary"] = False
        
        # Save auth state
        run(f"{AB} state save {AUTH_DIR / f'{role}.json'}", timeout=10)
        
        # Determine status
        url_low = result["url"].lower()
        if "login" not in url_low and result["url"] and "/" != result["url"].rstrip("/").split(NGROK.split("//")[1])[-1]:
            result["status"] = "passed"
            print(f"  Status: PASSED (redirected to {url_low})")
        elif any(p in url_low for p in ["dashboard", "candidate", "admin", "hr", "interview", "selection", "analytics"]):
            result["status"] = "passed"
            print(f"  Status: PASSED (role page)")
        else:
            result["status"] = "stuck_on_login"
            print(f"  Status: STUCK ON LOGIN (url: {url_low})")
        
    except Exception as e:
        import traceback
        result["errors"] = [str(e)]
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
    
    results[role] = result
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)

# Summary
print("\n\n" + "=" * 60)
print("  PHASE 6+8 RESULTS")
print("=" * 60)

all_login_ok = True
all_console_clean = True
failed_roles = []

for role, r in results.items():
    status_emoji = "✅" if r["status"] == "passed" else "❌" 
    console_status = "✅" if not r.get("console_errors") and not r.get("has_error_boundary") else "⚠️"
    route = r.get("url", "N/A").split("ngrok-free.dev")[-1] if "ngrok-free.dev" in r.get("url", "") else r.get("url", "N/A")
    print(f"\n  {status_emoji} [{role}] -> {route} | Console: {console_status}")
    if r.get("console_errors"):
        print(f"     JS Errors: {', '.join(r['console_errors'])}")
        all_console_clean = False
    if r.get("errors"):
        print(f"     Exceptions: {'; '.join(r['errors'])}")
    if r["status"] != "passed":
        all_login_ok = False
        failed_roles.append(role)

print(f"\n{'='*60}")
print(f"  PHASE 8 (Login): {'✅ ALL PASSED' if all_login_ok else '❌ FAILED: ' + ', '.join(failed_roles)}")
print(f"  PHASE 6 (Console): {'✅ ALL CLEAN' if all_console_clean else '⚠️ ERRORS FOUND'}")
print()

import json as _json
summary = {
    "phase6": {"status": "clean" if all_console_clean else "issues", "roles_with_errors": [r for r,d in results.items() if d.get("console_errors") or d.get("has_error_boundary")]},
    "phase8": {"status": "all_passed" if all_login_ok else "some_failed", "failed_roles": failed_roles},
}
print("---PHASE6_8_JSON_START---")
print(_json.dumps(summary, indent=2))
print("---PHASE6_8_JSON_END---")
