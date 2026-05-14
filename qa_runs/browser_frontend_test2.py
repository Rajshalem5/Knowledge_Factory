#!/usr/bin/env python3
"""
Browser-based frontend testing - handles ngrok interstitial first.
Tests each role's login flow and basic page verification.
"""
import subprocess, json, sys, os, time, re

NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AB = "/opt/hermes_shared_memory/bin/ab"
FAILURES_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/failures"
RUN_ID = os.environ.get('RUN_ID', time.strftime('%Y%m%d_%H%M%S'))

results = {"browser_checks": [], "errors": [], "successes": []}
baselines_dir = "/opt/hermes_shared_memory/projects/Knowledge_Factory/baselines"

def run_ab(*args, timeout=30):
    cmd = [AB] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)

def check(name, ok, detail="", critical=False):
    entry = {"name": name, "ok": ok, "detail": str(detail)[:300]}
    results["browser_checks"].append(entry)
    if ok:
        results["successes"].append(name)
    else:
        results["errors"].append(f"{'🔴' if critical else '🟠'} {name}: {detail[:200]}")
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
        shot_path = f"{FAILURES_DIR}/{RUN_ID}/{safe_name}.png"
        run_ab("screenshot", shot_path, timeout=10)
    return ok

def eval_js(js_code, timeout=15):
    """Run JS and return (success, output)."""
    rc, out, err = run_ab("eval", js_code, timeout=timeout)
    if rc == 0:
        return True, out.strip()
    # Check if it's the "--args ignored" issue
    if "args ignored" in err:
        run_ab("close", "--all", timeout=5)
        time.sleep(2)
        rc, out, err = run_ab("eval", js_code, timeout=timeout)
        if rc == 0:
            return True, out.strip()
    return False, (err or out)[:300]

# Clean start
run_ab("close", "--all", timeout=5)
time.sleep(1)

# Step 1: Open the ngrok URL
print("=== Step 1: Open ngrok ===")
rc, out, err = run_ab("open", NGROK, timeout=30)
check("open_ngrok", rc == 0, out[:200] if rc == 0 else err[:200])
if rc != 0:
    print("FATAL: Could not open ngrok")
    exit(1)
time.sleep(3)

# Step 2: Click "Visit Site" button to bypass ngrok interstitial
print("=== Step 2: Bypass ngrok interstitial ===")
rc, out, err = run_ab("snapshot", "-i", "-c", timeout=15)
print(f"Snapshot: {out[:400]}")

rc, out, err = run_ab("click", "@e6", timeout=15)  # "Visit Site" button
check("click_visit_site", rc == 0, out[:200] if rc == 0 else err[:200])
time.sleep(4)

# Step 3: Check what loaded
print("=== Step 3: Check page content ===")
success, text = eval_js("document.body.innerText")
if success:
    check("page_loaded", True, text[:300])
    print(f"Page loaded. Text: {text[:300]}")
    
    # Take screenshot
    shot = f"{FAILURES_DIR}/{RUN_ID}/page_loaded.png"
    run_ab("screenshot", shot, timeout=15)
else:
    check("page_loaded", False, text)

# Step 4: Identify login form elements
print("=== Step 4: Find login form elements ===")
success, inputs = eval_js("""
JSON.stringify(Array.from(document.querySelectorAll('input, button, a, select')).map(el => ({
    tag: el.tagName,
    type: el.type || '',
    name: el.name || '',
    id: el.id || '',
    placeholder: el.placeholder || '',
    text: (el.textContent || '').trim().substring(0, 50),
    class: (el.className || '').substring(0, 40),
    href: el.href || ''
})).slice(0, 30))
""")
if success:
    check("login_form_elements", True, inputs[:500])
    print(f"Form elements: {inputs[:600]}")
else:
    check("login_form_elements", False, inputs)

# Step 5: Try filling login form (Admin)
print("\n=== Step 5: Admin Login ===")
# Find the email/username input
success, _ = eval_js("""
document.querySelector('input[type="email"]') ? 'email_found' : 
document.querySelector('input[name="email"]') ? 'name_email_found' :
document.querySelector('input[placeholder*="email" i]') ? 'placeholder_found' :
document.querySelector('input:first-of-type') ? 'first_input' : 'no_inputs'
""")
print(f"Input search: {success} - {_ if success else 'failed'}")

# Try filling via direct value setting
success, result = eval_js("""
(function() {
    // Find email field
    const emailInput = document.querySelector('input[type="email"]') || 
                        document.querySelector('input[name="email"]') ||
                        document.querySelector('input:first-of-type');
    const passInput = document.querySelector('input[type="password"]');
    
    if (!emailInput) return 'NO_EMAIL_FIELD';
    if (!passInput) return 'NO_PASS_FIELD';
    
    // Set values
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(emailInput, 'admin@knowledgefactory.io');
    emailInput.dispatchEvent(new Event('input', {bubbles: true}));
    emailInput.dispatchEvent(new Event('change', {bubbles: true}));
    
    setter.call(passInput, 'admin123');
    passInput.dispatchEvent(new Event('input', {bubbles: true}));
    passInput.dispatchEvent(new Event('change', {bubbles: true}));
    
    return 'FILLED: email=' + emailInput.value + ' pass=' + '*'.repeat(passInput.value.length);
})()
""")
if success:
    check("fill_login_form", True, result[:200])
    print(f"Fill result: {result[:200]}")
else:
    check("fill_login_form", False, result)

time.sleep(1)

# Step 6: Click login/submit button
print("=== Step 6: Click submit ===")
success, result = eval_js("""
(function() {
    const btn = document.querySelector('button[type="submit"]') ||
                document.querySelector('button:not([type])') ||
                document.querySelector('button');
    if (!btn) return 'NO_BUTTON';
    btn.click();
    return 'CLICKED: ' + (btn.textContent || '').trim();
})()
""")
if success:
    check("click_login", True, result[:200])
    print(f"Click result: {result[:200]}")
else:
    check("click_login", False, result)

time.sleep(4)

# Step 7: Check post-login
print("=== Step 7: Post-login check ===")
success, text = eval_js("document.body.innerText")
if success:
    check("post_login_text", True, text[:400])
    print(f"Post-login text: {text[:400]}")
    
    success2, url = eval_js("window.location.href")
    if success2:
        print(f"URL: {url}")
        check("post_login_url", True, url[:200])
else:
    check("post_login_text", False, text)

# Step 8: Screenshot post-login
shot = f"{FAILURES_DIR}/{RUN_ID}/admin_dashboard.png"
rc, out, err = run_ab("screenshot", shot, timeout=15)
check("screenshot_dashboard", rc == 0, shot)

# Check for dashboard content
success, _ = eval_js("document.querySelectorAll('nav, .sidebar, header, [role=\"navigation\"]').length")
if success:
    print(f"Nav elements found: {_}")
    check("has_navigation", int(_) > 0, f"{_} nav elements" if int(_) > 0 else "none found")

success, _ = eval_js("""
JSON.stringify(Array.from(document.querySelectorAll('a[href], nav a')).slice(0,20).map(a => ({
    text: (a.textContent || '').trim().substring(0, 30),
    href: (a.getAttribute('href') || '').substring(0, 50)
})))
""")
if success:
    print(f"Nav links: {_[:500]}")
    check("nav_links", True, _[:300])

# Check console for errors
success, console_out = eval_js("""
(function() {
    if (window.__consoleErrors) return JSON.stringify(window.__consoleErrors);
    // Try to get Vite React errors
    const errors = document.querySelector('[data-rrweb-error]') ? 'rrweb_error' : 'none';
    return errors;
})()
""")

# Summary
print("\n=== BROWSER TEST RESULTS ===")
passed = sum(1 for c in results["browser_checks"] if c["ok"])
total = len(results["browser_checks"])
failed = total - passed
print(f"Passed: {passed}/{total}")
print(f"Failed: {failed}")
if results["errors"]:
    print(f"\nIssues ({len(results['errors'])}):")
    for e in results["errors"]:
        print(f"  {e}")

# Save
out_path = f"/opt/hermes_shared_memory/projects/Knowledge_Factory/qa_runs/{RUN_ID}_browser.json"
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved: {out_path}")

# Cleanup
run_ab("close", "--all", timeout=10)

print("\n---JSON_OUTPUT---")
print(json.dumps(results, default=str))
