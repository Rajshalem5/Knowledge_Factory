#!/usr/bin/env python3
"""Automated login for all roles using ab eval, and check for console errors."""
import subprocess, json, sys, time, os

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"

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

def login_role(role, creds):
    print(f"\n{'='*60}")
    print(f"  LOGIN: {role} ({creds['email']})")
    print(f"{'='*60}")
    
    # Close any existing session
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)
    
    # Open the app
    rc, out, _ = run(f"{AB} open {NGROK}", timeout=20)
    print(f"  Open: {'OK' if rc == 0 else 'FAIL'}")
    time.sleep(2)
    
    # Check for ngrok interstitial
    rc, out, _ = run(f"{AB} eval \"document.body.innerText.substring(0,200)\"", timeout=10)
    if "about to visit" in out.lower():
        print("  Ngrok interstitial - clicking Visit Site")
        run(f"{AB} click @e6", timeout=10)
        time.sleep(2)
    
    # Click Login button
    rc, out, _ = run(f"{AB} snapshot -c", timeout=10)
    if "Login" in out:
        rc2, _, _ = run(f"{AB} click @e3", timeout=10)
        print(f"  Click Login: {'OK' if rc2 == 0 else 'FAIL'}")
        time.sleep(2)
    elif "Welcome back" in out:
        print("  Already on login page")
    else:
        # Try Sign In button
        rc2, _, _ = run(f"{AB} click @e15", timeout=10)
        print(f"  Click Sign In: {'OK' if rc2 == 0 else 'FAIL'}")
        time.sleep(2)
    
    # Fill credentials via eval
    js = f"""
    var emailInput = document.getElementById('email');
    var passwordInput = document.getElementById('password');
    if (!emailInput) {{
        // Try alternative selectors
        emailInput = document.querySelector('input[type="email"]');
        passwordInput = document.querySelector('input[type="password"]');
    }}
    if (emailInput && passwordInput) {{
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(emailInput, '{creds["email"]}');
        emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        setter.call(passwordInput, '{creds["pw"]}');
        passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        var form = document.querySelector('form');
        var btn = form ? form.querySelector('button[type="submit"]') : null;
        if (btn) {{ btn.click(); 'clicked submit'; }}
        else if (form) {{ form.requestSubmit(); 'submitted form'; }}
        else {{ 'no form found'; }}
    }} else {{
        'inputs not found: email=' + !!emailInput + ' password=' + !!passwordInput;
    }}
    """
    rc, out, _ = run(f"""{AB} eval '{js}'""", timeout=10)
    print(f"  Submit: {out[:100]}")
    time.sleep(3)
    
    # Check result
    rc, out, _ = run(f"{AB} eval \"document.body.innerText.substring(0,3000)\"", timeout=10)
    
    # Determine if login succeeded
    dashboard_indicators = ["Dashboard", "Candidates", "TOTAL", "Users & Roles", "Selection", "Analytics"]
    login_fail_indicators = ["Sign in to your account", "Welcome back"]
    
    is_logged_in = any(ind in out for ind in dashboard_indicators)
    is_on_login = any(ind in out for ind in login_fail_indicators) and not is_logged_in
    
    result = "✅ LOGGED IN" if is_logged_in else ("❌ STILL ON LOGIN" if is_on_login else "⚠️ UNKNOWN")
    print(f"  Result: {result}")
    print(f"  Page preview: {out[:200]}...")
    
    # Check console errors
    rc, err_out, _ = run(f"{AB} eval \"JSON.stringify({{errorElems: Array.from(document.querySelectorAll('[class*=error],[role=alert]')).map(function(e){{return e.innerText}}).filter(Boolean), pageTitle: document.title}})\"", timeout=10)
    
    errors_found = []
    if err_out:
        try:
            err_data = json.loads(err_out)
            errors_found = err_data.get('errorElems', [])
            print(f"  Console errors: {len(errors_found)}")
        except:
            pass
    
    # Save screenshot
    screenshot_path = f"{AUTH_DIR}/{role}_dashboard.png"
    run(f"{AB} screenshot {screenshot_path}", timeout=10)
    print(f"  Screenshot: {screenshot_path}")
    
    # Save auth state
    rc, state_out, _ = run(f"{AB} eval \"var s={{localStorage:{{}},cookies:document.cookie,url:window.location.href}}; for(var i=0;i<localStorage.length;i++){{var k=localStorage.key(i);s.localStorage[k]=localStorage.getItem(k);}} JSON.stringify(s)\"", timeout=10)
    if state_out:
        state_path = f"{AUTH_DIR}/{role}_state.json"
        with open(state_path, 'w') as f:
            # Try to parse and pretty-print
            try:
                d = json.loads(state_out)
                json.dump(d, f, indent=2)
            except:
                f.write(state_out)
        print(f"  State saved: {state_path}")
    
    # Close session
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)
    
    return {
        "role": role,
        "logged_in": is_logged_in,
        "errors": errors_found,
        "screenshot": screenshot_path
    }

results = []
for role, creds in ROLES.items():
    r = login_role(role, creds)
    results.append(r)

print(f"\n{'='*60}")
print(f"  SUMMARY")
print(f"{'='*60}")
for r in results:
    status = "✅" if r["logged_in"] else "❌"
    errs = f" ({len(r['errors'])} console errors)" if r["errors"] else ""
    print(f"  {status} {r['role']}{errs}")

# Overall
all_ok = all(r["logged_in"] for r in results)
print(f"\n  All roles logged in: {'✅ YES' if all_ok else '❌ NO'}")
print(f"  Total console errors across all roles: {sum(len(r['errors']) for r in results)}")

# Save results
with open(f"{AUTH_DIR}/login_results.json", 'w') as f:
    json.dump(results, f, indent=2)
print(f"  Results saved to {AUTH_DIR}/login_results.json")
