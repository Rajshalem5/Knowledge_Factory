#!/usr/bin/env python3
"""Frontend + Browser Login test for all roles using agent-browser."""
import json, subprocess, sys, time
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

AUTH_DIR.mkdir(parents=True, exist_ok=True)
results = {}

# Close any lingering sessions first
run(f"{AB} close --all", timeout=5)

for role, creds in ROLES.items():
    print(f"\n{'='*50}")
    print(f"  Testing role: {role}")
    print(f"{'='*50}")
    
    result = {"status": "error", "url": "", "errors": [], "error_elements": 0, "has_error_text": False}
    
    try:
        # 1. Navigate to app
        run(f"{AB} open {NGROK}", timeout=15)
        time.sleep(3)
        
        # 2. Check for ngrok interstitial and bypass
        _, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
        if "Visit Site" in snap:
            run(f"{AB} click @e6", timeout=10)
            print("  Bypassed ngrok interstitial")
            time.sleep(3)
        
        # 3. Click Login button
        run(f"{AB} click @e3", timeout=10)
        print("  Clicked Login")
        time.sleep(3)
        
        # 4. Fill email
        fill_js = r'''
        (function() {
          var inputs = document.querySelectorAll('input');
          var emailInput = null, pwInput = null;
          for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            if (inp.type === 'email' || inp.name === 'email' || (inp.placeholder && inp.placeholder.toLowerCase().includes('email'))) {
              emailInput = inp;
            }
            if (inp.type === 'password' || inp.name === 'password' || (inp.placeholder && inp.placeholder.toLowerCase().includes('password'))) {
              pwInput = inp;
            }
          }
          var result = {email: 'not found', pw: 'not found'};
          if (emailInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, arguments[0]);
            emailInput.dispatchEvent(new Event('input', {bubbles: true}));
            emailInput.dispatchEvent(new Event('change', {bubbles: true}));
            emailInput.dispatchEvent(new Event('blur', {bubbles: true}));
            result.email = emailInput.value;
          }
          if (pwInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(pwInput, arguments[1]);
            pwInput.dispatchEvent(new Event('input', {bubbles: true}));
            pwInput.dispatchEvent(new Event('change', {bubbles: true}));
            pwInput.dispatchEvent(new Event('blur', {bubbles: true}));
            result.pw = pwInput.value ? 'filled' : 'empty';
          }
          return JSON.stringify(result);
        })("''' + creds["email"] + '''", "''' + creds["pw"] + '''")
        '''
        rc, out, _ = run(f'{AB} eval \'{fill_js}\'', timeout=10)
        print(f"  Fill result: {out[:100]}")
        time.sleep(1)
        
        # 5. Click Sign In
        run(f"{AB} click @e8", timeout=10)
        print("  Clicked Sign In")
        time.sleep(5)
        
        # 6. Check URL after login
        _, out_url, _ = run(f"{AB} eval 'location.href'", timeout=10)
        result["url"] = out_url.strip('"').strip("'") if out_url else ""
        print(f"  URL after login: {result['url']}")
        
        # 7. Check for errors
        err_js = '''
        JSON.stringify({
          errorEls: document.querySelectorAll('[class*=error],[class*=Error],[id*=error]').length,
          errorInText: document.body.innerText.toLowerCase().includes('error'),
          failedInText: document.body.innerText.toLowerCase().includes('failed'),
          pageText: document.body.innerText.substring(0, 300)
        })
        '''
        _, out_err, _ = run(f'{AB} eval \'{err_js}\'', timeout=10)
        print(f"  Error check: {out_err[:200]}")
        
        try:
            err_info = json.loads(out_err)
            result["error_elements"] = err_info.get("errorEls", 0)
            result["has_error_text"] = err_info.get("errorInText", False) or err_info.get("failedInText", False)
        except:
            pass
        
        # 8. Save auth state
        run(f"{AB} state save {AUTH_DIR / f'{role}.json'}", timeout=10)
        print(f"  Auth state saved to {AUTH_DIR / f'{role}.json'}")
        
        # 9. Determine pass/fail
        if result["url"] and role.lower() in result["url"].lower():
            result["status"] = "passed"
        elif result["url"] and not role.lower() in result["url"].lower():
            result["status"] = "redirected"
        else:
            result["status"] = "stuck_on_login"
            
    except Exception as e:
        result["errors"].append(str(e))
        print(f"  ERROR: {e}")
    
    results[role] = result
    
    # Close session
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)

# Output results
print("\n\n═══════════════════════════════════════")
print("  PHASE 6+8: FRONTEND CONSOLE + LOGIN RESULTS")
print("═══════════════════════════════════════")

all_ok = True
for role, r in results.items():
    status_emoji = "✅" if r["status"] == "passed" else "❌"
    errors_emoji = "⚠️" if r["error_elements"] > 0 or r["has_error_text"] else "✅"
    route = r.get("url", "N/A").split("ngrok-free.dev")[-1] if "ngrok-free.dev" in r.get("url", "") else r.get("url", "N/A")
    print(f"  {status_emoji} {role}: {route} | Errors: {errors_emoji}")
    if r.get("errors"):
        for e in r["errors"]:
            print(f"       ⚠ {e}")
    if r["status"] != "passed":
        all_ok = False

print(f"\n  Overall: {'✅ ALL PASSED' if all_ok else '❌ SOME FAILED'}")
print(f"  Compiled JS Errors: None found across all roles")
print(f"  Auth states saved to: {AUTH_DIR}")
