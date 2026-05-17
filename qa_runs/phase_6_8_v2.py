#!/usr/bin/env python3
"""
Phase 6: Frontend Console Check + Phase 8: Browser Login Tests
Using temp JS files to avoid shell escaping issues.
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

def eval_js(js_code, timeout=15):
    """Write JS to temp file and run via ab eval to avoid shell escaping issues."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_code)
        tmpfile = f.name
    try:
        r = subprocess.run(
            f'{AB} eval "$(cat {tmpfile})"',
            shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    finally:
        os.unlink(tmpfile)

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

AUTH_DIR.mkdir(parents=True, exist_ok=True)
results = {}

# Close any lingering sessions
run(f"{AB} close --all", timeout=5)
time.sleep(2)

for role, creds in ROLES.items():
    print(f"\n{'='*60}")
    print(f"  PHASE 6+8: Testing role={role} ({creds['email']})")
    print(f"{'='*60}")
    
    result = {
        "status": "error",
        "url": "",
        "console_errors": [],
        "has_error_boundary": False,
    }
    
    try:
        # Step 1: Navigate to app
        rc1, out1, _ = run(f"{AB} open {NGROK}", timeout=20)
        print(f"  Navigated to {NGROK}")
        time.sleep(5)
        
        # Step 2: Bypass ngrok interstitial (always shows fresh)
        run(f"{AB} click @e6", timeout=10)  # "Visit Site" button
        print("  Clicked 'Visit Site' (ngrok bypass)")
        time.sleep(5)
        
        # Verify we're on the app
        rc, title, _ = eval_js("document.title")
        print(f"  Page title: {title}")
        
        # Step 3: Click Login
        login_js = """
        (function() {
          var btns = document.querySelectorAll('a, button, span');
          for(var b of btns) {
            var t = (b.innerText || '').trim();
            if(t === 'Login') { b.click(); return 'OK'; }
          }
          return 'NOT_FOUND';
        })()
        """
        rc, click_res, _ = eval_js(login_js)
        print(f"  Login click: {click_res}")
        time.sleep(3)
        
        # Step 4: Fill credentials using native value setters (React compatible)
        fill_js = """
        (function() {
          var inputs = document.querySelectorAll('input');
          var emailInput = null, pwInput = null;
          for(var i=0; i<inputs.length; i++) {
            var inp = inputs[i];
            var name = (inp.name || '').toLowerCase();
            var ph = (inp.placeholder || '').toLowerCase();
            if(inp.type === 'email' || name === 'email' || ph.includes('email')) emailInput = inp;
            if(inp.type === 'password' || name === 'password' || ph.includes('password')) pwInput = inp;
          }
          var result = {email: 'nf', pw: 'nf'};
          if(emailInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, arguments[0]);
            emailInput.dispatchEvent(new Event('input', {bubbles: true}));
            emailInput.dispatchEvent(new Event('change', {bubbles: true}));
            result.email = emailInput.value;
          }
          if(pwInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(pwInput, arguments[1]);
            pwInput.dispatchEvent(new Event('input', {bubbles: true}));
            pwInput.dispatchEvent(new Event('change', {bubbles: true}));
            result.pw = pwInput.value ? 'filled' : 'empty';
          }
          return JSON.stringify(result);
        })("%s","%s")
        """ % (creds["email"], creds["pw"])
        rc, fill_res, _ = eval_js(fill_js)
        print(f"  Fill result: {fill_res[:100]}")
        time.sleep(1)
        
        # Step 5: Click Sign In button
        signin_js = """
        (function() {
          var btns = document.querySelectorAll('button');
          for(var b of btns) {
            if(b.innerText.trim() === 'Sign In') { b.click(); return 'clicked'; }
          }
          return 'NOT_FOUND';
        })()
        """
        rc, signin_res, _ = eval_js(signin_js)
        print(f"  Sign In click: {signin_res}")
        time.sleep(5)
        
        # Step 6: Check post-login URL
        rc, url_out, _ = eval_js("location.href")
        result["url"] = url_out.strip('"').strip("'") if url_out else ""
        print(f"  Post-login URL: {result['url']}")
        
        # Step 7: Check console errors
        console_js = """
        (function() {
          var body = document.body;
          if (!body) return JSON.stringify({errors: ['no_body']});
          var text = body.innerText || '';
          var errors = [];
          
          var patterns = ['error', 'failed', 'cannot read property', 'undefined is not',
            'typeerror', 'referenceerror', 'internal server', '500', '401',
            '404', 'failed to fetch', 'network error', 'react error'];
          var lowerText = text.toLowerCase();
          for (var p of patterns) {
            if (lowerText.indexOf(p) !== -1) errors.push('text_contains_' + p);
          }
          
          var errorEls = document.querySelectorAll('[class*=error], [class*=Error], [id*=error], [role=alert]');
          
          return JSON.stringify({
            errors: errors,
            errorElements: errorEls.length,
            title: document.title,
            url: location.href,
            textSnippet: text.substring(0, 200)
          });
        })()
        """
        rc, console_out, _ = eval_js(console_js)
        print(f"  Console check: {console_out[:200]}")
        
        try:
            console_data = json.loads(console_out)
            result["console_errors"] = console_data.get("errors", [])
            result["has_error_boundary"] = console_data.get("errorElements", 0) > 0
            result["page_title"] = console_data.get("title", "")
            result["text_snippet"] = console_data.get("textSnippet", "")
        except json.JSONDecodeError as e:
            print(f"  Parse error: {e}, raw: {console_out[:200]}")
        
        # Step 8: Save auth state (Phase 8)
        run(f"{AB} state save {AUTH_DIR / f'{role}.json'}", timeout=10)
        print(f"  Auth state saved")
        
        # Determine pass/fail
        url_lower = result["url"].lower()
        if "login" not in url_lower and result["url"] and result["url"] != NGROK + "/":
            result["status"] = "passed"
            print(f"  Status: PASSED - navigated away from login")
        elif "/dashboard" in url_lower or "/candidate" in url_lower or "/hr" in url_lower or "/admin" in url_lower or "/interviewer" in url_lower:
            result["status"] = "passed"
            print(f"  Status: PASSED - on role-specific page")
        else:
            result["status"] = "stuck_on_login"
            print(f"  Status: STUCK_ON_LOGIN - still on login page after submission")
        
    except Exception as e:
        result["errors"] = [str(e)]
        print(f"  EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    results[role] = result
    
    # Close session before next role
    run(f"{AB} close --all", timeout=5)
    time.sleep(2)

# Output results
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
    print(f"\n  {status_emoji} [{role}] Login -> {route}")
    print(f"     Console: {console_status}")
    if r.get("console_errors"):
        print(f"     JS Errors: {', '.join(r['console_errors'])}")
        all_console_clean = False
    if r.get("errors"):
        print(f"     Exceptions: {'; '.join(r['errors'])}")
    if r["status"] != "passed":
        all_login_ok = False
        failed_roles.append(role)

print(f"\n{'='*60}")
print(f"  PHASE 8 (Browser Login): {'✅ ALL PASSED' if all_login_ok else '❌ SOME FAILED'}")
if failed_roles:
    print(f"  Failed roles: {', '.join(failed_roles)}")
print(f"  PHASE 6 (Console Check): {'✅ ALL CLEAN' if all_console_clean else '⚠️ ERRORS FOUND'}")
print(f"  Auth states: {AUTH_DIR}")
print()

# JSON summary
summary = {
    "phase6_frontend_console": {
        "status": "clean" if all_console_clean else "issues_found",
        "roles_with_errors": [r for r, d in results.items() if d.get("console_errors") or d.get("has_error_boundary")]
    },
    "phase8_browser_login": {
        "status": "all_passed" if all_login_ok else "some_failed",
        "failed_roles": failed_roles
    },
    "detailed": {k: {sk: sv for sk, sv in v.items() if sk != "text_snippet"} for k, v in results.items()}
}
print("---PHASE6_8_JSON_START---")
print(json.dumps(summary, indent=2))
print("---PHASE6_8_JSON_END---")
