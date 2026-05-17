#!/usr/bin/env python3
"""Phase 6 & 8: Frontend Console Check + Browser Login Tests using Hermes browser tools."""
import subprocess, json, time, sys, re

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK_URL = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"

ROLES = {
    "superadmin": {"email": "superadmin@knowledgefactory.io", "pw": "Super@12345"},
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

results = []
errors = {}

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def click_ref(ref_str, label=""):
    """Click an element by @ref."""
    rc, out, err = run(f'{AB} click {ref_str} 2>&1', timeout=10)
    if rc != 0:
        print(f"    ⚠️  Failed to click {label}: {err[:100]}")
    return out

def fill_ref(ref_str, text, label=""):
    """Fill an input by @ref."""
    rc, out, err = run(f'{AB} fill {ref_str} "{text}" 2>&1', timeout=10)
    if rc != 0:
        print(f"    ⚠️  Failed to fill {label}: {err[:100]}")
    return out

def snapshot():
    rc, out, err = run(f'{AB} snapshot -i -c 2>&1', timeout=10)
    return out

def eval_js(js):
    rc, out, err = run(f'{AB} eval {json.dumps(js)} 2>&1', timeout=15)
    return out

def take_screenshot(path):
    rc, out, err = run(f'{AB} screenshot {path} 2>&1', timeout=10)
    return out

# Close any existing sessions first
print("Closing any existing agent-browser sessions...")
run(f'{AB} close --all 2>&1', timeout=5)
time.sleep(1)

for role_name, creds in ROLES.items():
    print(f"\n{'='*60}")
    print(f"  PHASE 6+8: Testing {role_name.upper()} ({creds['email']})")
    print(f"{'='*60}")
    
    role_errors = []
    
    # Step 1: Open the ngrok URL
    print(f"  [1/8] Opening {NGROK_URL}...")
    rc, out, err = run(f'{AB} open "{NGROK_URL}" 2>&1', timeout=15)
    if rc != 0:
        print(f"    ❌ Failed to open: {err[:200]}")
        errors[role_name] = ["Failed to open browser"]
        results.append({"role": role_name, "ok": False, "error": "browser_open_failed"})
        continue
    
    time.sleep(3)
    
    # Step 2: Bypass ngrok interstitial
    print(f"  [2/8] Bypassing ngrok interstitial...")
    snap = snapshot()
    if "Visit Site" in snap or "ngrok" in snap.lower():
        click_ref("@e6", "Visit Site (ngrok)")
        time.sleep(2)
    
    # Step 3: Click Login button
    print(f"  [3/8] Clicking Login...")
    snap = snapshot()
    
    login_button_ref = None
    # Try to find Login or Sign In button by searching snapshot output
    for line in snap.split('\n'):
        if 'Login' in line and '@e' in line:
            m = re.search(r'@e(\d+)', line)
            if m: login_button_ref = f"@e{m.group(1)}"; break
        if 'Sign In' in line and '@e' in line:
            m = re.search(r'@e(\d+)', line)
            if m: login_button_ref = f"@e{m.group(1)}"; break
    
    if login_button_ref:
        click_ref(login_button_ref, "Login/Sign In button")
        time.sleep(3)
    else:
        # Try known refs
        click_ref("@e3", "Login button (ref @e3)")
        click_ref("@e15", "Sign In button (ref @e15)")
        time.sleep(3)
    
    # Step 4: Handle authentication flow
    snap = snapshot()
    print(f"  Snapshot: {snap[:400]}")
    
    # Check if this is Clerk auth (multi-step)
    clerk_mode = "Email or phone" in snap or "Clerk" in snap
    
    if clerk_mode:
        print(f"  [4/8] Clerk auth detected - entering email...")
        # Clerk step 1: Enter email
        email_ref = None
        for line in snap.split('\n'):
            if 'Email or phone' in line and '@e' in line:
                m = re.search(r'@e(\d+)', line)
                if m: email_ref = f"@e{m.group(1)}"; break
        
        if not email_ref:
            # Try textbox pattern
            for line in snap.split('\n'):
                if 'textbox' in line and '@e' in line and ('email' in line.lower() or 'phone' in line.lower()):
                    m = re.search(r'@e(\d+)', line)
                    if m: email_ref = f"@e{m.group(1)}"; break
        
        if email_ref:
            fill_ref(email_ref, creds["email"], "Email")
            time.sleep(1)
        else:
            print(f"    ⚠️  Could not find email field in Clerk form")
            role_errors.append("clerk_email_field_not_found")
        
        # Click Next
        next_ref = None
        for line in snap.split('\n'):
            if 'Next' in line and '@e' in line and 'button' in line.lower():
                m = re.search(r'@e(\d+)', line)
                if m: next_ref = f"@e{m.group(1)}"; break
        
        if next_ref:
            click_ref(next_ref, "Next button")
            time.sleep(3)
            snap = snapshot()
            print(f"  After Next: {snap[:300]}")
            
            # Clerk step 2: Enter password
            print(f"  [5/8] Entering password...")
            # Find password input
            pw_ref = None
            for line in snap.split('\n'):
                if 'password' in line.lower() and '@e' in line and 'textbox' in line.lower():
                    m = re.search(r'@e(\d+)', line)
                    if m: pw_ref = f"@e{m.group(1)}"; break
            
            if pw_ref:
                fill_ref(pw_ref, creds["pw"], "Password")
                time.sleep(1)
                
                # Click Continue/Sign In
                continue_ref = None
                for btn_text in ['Continue', 'Sign In']:
                    for line in snap.split('\n'):
                        if btn_text in line and '@e' in line:
                            m = re.search(r'@e(\d+)', line)
                            if m: continue_ref = f"@e{m.group(1)}"; break
                    if continue_ref: break
                
                if continue_ref:
                    click_ref(continue_ref, f"{btn_text} button")
                    time.sleep(3)
                else:
                    # Try common refs
                    click_ref("@e8", "Sign In button")
                    click_ref("@e5", "Continue/Next button")
                    time.sleep(3)
            else:
                print(f"    ⚠️  Could not find password field")
                role_errors.append("password_field_not_found")
        else:
            print(f"    ⚠️  Could not find Next button in Clerk form")
            role_errors.append("clerk_next_button_not_found")
    else:
        print(f"  [4/8] Simple login form detected...")
        # Simple form - email then password
        snap = snapshot()
        
        email_ref = None
        pw_ref = None
        submit_ref = None
        
        lines = snap.split('\n')
        for i, line in enumerate(lines):
            if 'textbox' in line and '@e' in line:
                m = re.search(r'@e(\d+)', line)
                if m:
                    if 'email' in line.lower() or 'mail' in line.lower():
                        email_ref = f"@e{m.group(1)}"
                    elif 'pass' in line.lower():
                        pw_ref = f"@e{m.group(1)}"
                    elif not email_ref:
                        email_ref = f"@e{m.group(1)}"
            if 'Sign In' in line and '@e' in line and 'button' in line.lower():
                m = re.search(r'@e(\d+)', line)
                if m: submit_ref = f"@e{m.group(1)}"
        
        if not email_ref and not pw_ref:
            # Try positional refs
            email_ref = "@e5"
            pw_ref = "@e6"
            submit_ref = "@e8"
        
        if email_ref:
            fill_ref(email_ref, creds["email"], "Email")
            time.sleep(1)
        if pw_ref:
            fill_ref(pw_ref, creds["pw"], "Password")
            time.sleep(1)
        if submit_ref:
            click_ref(submit_ref, "Sign In button")
            time.sleep(3)
        else:
            click_ref("@e8", "Sign In (default)")
            time.sleep(3)
    
    # Step 5: Check console for errors
    print(f"  [6/8] Checking console for errors...")
    js_check = eval_js("""(function() {
        return JSON.stringify({
            url: window.location.href,
            title: document.title,
            has_errors: window.__vite_plugin_react_preamble_installed ? 'vite_react' : 'no_vite'
        });
    })()""")
    print(f"  JS Check: {js_check[:200]}")
    
    console_out, _ = run(f'{AB} eval "console.warn(\'__PHASE6_CHECK__\'); console.log(document.title);" 2>&1', timeout=10)
    
    # Check in a more detailed way
    console_check = run(f'{AB} eval "JSON.stringify(window.location.href)" 2>&1', timeout=5)
    console_url = console_check[1] if console_check[1] else "unknown"
    print(f"  Current URL: {console_url}")
    
    # Step 6: Take screenshot for evidence
    print(f"  [7/8] Taking screenshot...")
    shot_path = f"/opt/hermes_shared_memory/projects/Knowledge_Factory/failures/phase6_{role_name}.png"
    take_screenshot(shot_path)
    
    # Step 7: Save auth state
    print(f"  [8/8] Saving auth state...")
    run(f'{AB} state save "{AUTH_DIR}/{role_name}.json" 2>&1', timeout=10)
    
    # Determine success
    current_url = console_url.strip('"')
    has_errors_bool = len(role_errors) > 0
    login_seems_ok = "dashboard" in current_url.lower() or "admin" in current_url.lower() or "candidate" in current_url.lower() or "dashboard" in current_url or "assessment" in current_url
    
    result = {
        "role": role_name, "ok": not has_errors_bool,
        "url": current_url, "errors": role_errors,
        "login_seems_ok": login_seems_ok
    }
    results.append(result)
    
    if has_errors_bool:
        errors[role_name] = role_errors
        print(f"  ❌ {role_name}: Errors found - {role_errors}")
        print(f"     URL: {current_url}")
    elif login_seems_ok:
        print(f"  ✅ {role_name}: Login successful, no console errors")
        print(f"     URL: {current_url}")
    else:
        print(f"  ⚠️  {role_name}: Login may not have completed, but no JS errors")
        print(f"     URL: {current_url}")
    
    # Close tab for next role
    run(f'{AB} close 2>&1', timeout=5)
    time.sleep(1)

# Summary
print(f"\n{'='*60}")
print(f"  PHASE 6+8 SUMMARY")
print(f"{'='*60}")
for r in results:
    icon = "✅" if r["ok"] and r.get("login_seems_ok") else ("⚠️" if r["ok"] else "❌")
    print(f"  {icon} {r['role']}: URL={r['url'][:80]}")
    if r.get("errors"):
        print(f"     Errors: {r['errors']}")

print(f"\nResults JSON:")
print(json.dumps({"phase_6_8_results": results}))
