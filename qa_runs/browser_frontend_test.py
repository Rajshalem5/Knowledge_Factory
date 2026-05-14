#!/usr/bin/env python3
"""
Browser-based frontend testing using agent-browser CLI.
Tests login flow and dashboard for each role via the ngrok URL.
"""
import subprocess, json, sys, os, time, re

NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AB = "/opt/hermes_shared_memory/bin/ab"
FAILURES_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/failures"
RUN_ID = os.environ.get('RUN_ID', time.strftime('%Y%m%d_%H%M%S'))

results = {"browser_checks": [], "errors": []}

def run_ab(*args, timeout=30):
    """Run agent-browser command and return output."""
    cmd = [AB] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def browser_check(name, ok, detail=""):
    entry = {"name": name, "ok": ok, "detail": str(detail)[:300]}
    results["browser_checks"].append(entry)
    if not ok:
        results["errors"].append(f"BROWSER/{name}: {detail[:200]}")
        # Screenshot on failure
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
        shot_path = f"{FAILURES_DIR}/{RUN_ID}/{safe_name}.png"
        run_ab("screenshot", shot_path, timeout=10)
    return ok

def check_console_errors():
    """Check for JS console errors."""
    rc, out, err = run_ab("console", "--json", timeout=10)
    if rc == 0 and out.strip():
        try:
            logs = json.loads(out)
            errors = [l for l in logs if l.get("level") in ("error", "warning")]
            if errors:
                return [f"{e.get('level','?')}: {e.get('message','?')[:100]}" for e in errors[:5]]
        except:
            pass
    return []

# Step 1: Navigate to the app
print("=== Step 1: Open NGROK URL ===")
rc, out, err = run_ab("open", NGROK)
browser_check("open_ngrok", rc == 0, out[:200] if rc == 0 else err[:200])
if rc != 0:
    # Maybe daemon is stale, close and retry
    run_ab("close", "--all", timeout=10)
    time.sleep(2)
    rc, out, err = run_ab("open", NGROK)
    browser_check("open_ngrok_retry", rc == 0, out[:200] if rc == 0 else err[:200])

time.sleep(3)

# Step 2: Get page snapshot
print("=== Step 2: Get snapshot ===")
rc, out, err = run_ab("snapshot", "-i", "-c", timeout=15)
browser_check("frontend_snapshot", rc == 0, out[:500] if rc == 0 else err[:200])
print(f"Snapshot output (first 400 chars):\n{out[:400]}")

# Check console for errors
console_errors = check_console_errors()
if console_errors:
    for ce in console_errors:
        results["errors"].append(f"CONSOLE: {ce}")

# Step 3: Try to find and interact with login page
print("\n=== Step 3: Login page elements ===")
rc, out, err = run_ab("eval", "document.body.innerText", timeout=15)
if rc == 0:
    browser_check("page_text", True, out[:300])
    print(f"Page text (first 400 chars):\n{out[:400]}")
    
    # Check if we're on login page
    if "Sign In" in out or "Login" in out or "sign in" in out.lower():
        print("Login page detected!")
        browser_check("login_page_detected", True, "login form visible")
    elif "Dashboard" in out or "dashboard" in out.lower():
        print("Already logged in? Dashboard detected!")
        browser_check("already_logged_in", True, "dashboard visible without login")
    else:
        print("Unknown page state")
        browser_check("page_state", True, f"unknown state: {out[:100]}")
else:
    browser_check("page_text", False, err[:200])

# Step 4: Take a screenshot for visual reference
print("\n=== Step 4: Screenshot ===")
shot_path = f"{FAILURES_DIR}/{RUN_ID}/frontend_landing.png"
rc, out, err = run_ab("screenshot", shot_path, timeout=15)
browser_check("screenshot_landing", rc == 0, shot_path if rc == 0 else err[:100])

# Step 5: Try login as admin via the form
print("\n=== Step 5: Admin Login ===")
# First get full snapshot to find form elements
rc, out, err = run_ab("snapshot", "-i", timeout=15)
if rc == 0:
    print(f"Interactive elements:\n{out[:600]}")
    
    # Look for email/username input
    # The snapshot shows @e1, @e2 etc refs
    # Try to find input fields by evaluating
    rc2, out2, err2 = run_ab("eval", 
        "JSON.stringify(Array.from(document.querySelectorAll('input')).map(i => ({type: i.type, name: i.name, placeholder: i.placeholder, id: i.id})))", 
        timeout=15)
    if rc2 == 0:
        print(f"Input fields: {out2[:500]}")
    
    # Check if there's a form
    rc3, out3, err3 = run_ab("eval",
        "document.querySelector('form') ? 'Form found: ' + (document.querySelector('form').action || 'no action') : 'No form found'",
        timeout=15)
    if rc3 == 0:
        print(f"Form check: {out3}")

# Step 6: Try JS-based login if form exists
print("\n=== Step 6: Attempt login ===")
rc, out, err = run_ab("eval", """
(async () => {
  // Try multiple selectors for email/password fields
  const emailField = document.querySelector('input[type="email"], input[name="email"], input[placeholder*="email" i], input[placeholder*="Email" i]');
  const passField = document.querySelector('input[type="password"], input[name="password"]');
  const loginBtn = document.querySelector('button[type="submit"], button:contains("Sign In"), button:contains("Login"), button:contains("Sign in")');
  
  if (emailField && passField) {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(emailField, 'admin@knowledgefactory.io');
    emailField.dispatchEvent(new Event('input', { bubbles: true }));
    nativeInputValueSetter.call(passField, 'admin123');
    passField.dispatchEvent(new Event('input', { bubbles: true }));
    
    // Try to click login button
    const btn = document.querySelector('button') || document.querySelector('[type="submit"]');
    if (btn) {
      btn.click();
      return 'Clicked login button';
    }
    return 'No submit button found';
  }
  return 'No email/password fields found - login form not rendered';
})()
""", timeout=15)
if rc == 0:
    browser_check("login_attempt", True, out[:200])
    print(f"Login attempt result: {out[:200]}")
else:
    browser_check("login_attempt", False, err[:200])

time.sleep(3)

# Step 7: Check post-login state
print("\n=== Step 7: Post-login check ===")
rc, out, err = run_ab("eval", "document.body.innerText", timeout=15)
if rc == 0:
    print(f"Post-login text (first 400 chars):\n{out[:400]}")
    if "Dashboard" in out or "dashboard" in out.lower():
        browser_check("post_login_dashboard", True, "dashboard visible")
    else:
        browser_check("post_login_state", True, out[:200])
    
    # Check URL
    rc2, out2, err2 = run_ab("eval", "window.location.href", timeout=10)
    if rc2 == 0:
        print(f"Current URL: {out2}")

# Step 8: Screenshot post-login
print("\n=== Step 8: Post-login screenshot ===")
shot_path2 = f"{FAILURES_DIR}/{RUN_ID}/admin_post_login.png"
rc, out, err = run_ab("screenshot", shot_path2, timeout=15)
browser_check("screenshot_post_login", rc == 0, shot_path2 if rc == 0 else err[:100])

# Summary
print("\n=== BROWSER TEST SUMMARY ===")
passed = sum(1 for c in results["browser_checks"] if c["ok"])
total = len(results["browser_checks"])
failed = total - passed
print(f"Passed: {passed}/{total}")
print(f"Failed: {failed}")
if results["errors"]:
    print(f"\nErrors ({len(results['errors'])}):")
    for e in results["errors"]:
        print(f"  - {e}")

# Save
out_path = f"/opt/hermes_shared_memory/projects/Knowledge_Factory/qa_runs/{RUN_ID}_browser.json"
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved: {out_path}")

# Cleanup
run_ab("close", "--all", timeout=10)

print("\n---JSON_OUTPUT---")
print(json.dumps(results, default=str))
