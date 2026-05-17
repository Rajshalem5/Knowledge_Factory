#!/usr/bin/env python3
"""Frontend Console + Login Check script.
Uses agent-browser to log in as each role, capture the page, and check for errors.
"""
import json, subprocess, sys, time, re
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

AUTH_DIR.mkdir(parents=True, exist_ok=True)

results = {}

for role, creds in ROLES.items():
    print(f"\n{'='*50}")
    print(f"  Testing role: {role}")
    print(f"{'='*50}")
    
    step = "start"
    result = {"status": "unknown", "page_title": "", "url": "", "errors": [], "error_count": 0}
    
    try:
        # 1. Open the app
        rc = subprocess.run(f"{AB} open {NGROK}", shell=True, capture_output=True, text=True, timeout=15)
        print(f"  open: {rc.returncode}")
        
        time.sleep(2)
        
        # 2. Check if ngrok interstitial, click Visit Site
        rc2, out2, _ = run(f"{AB} snapshot -c -i")
        if "Visit Site" in out2:
            rc3 = subprocess.run(f"{AB} click @e6", shell=True, capture_output=True, text=True, timeout=10)
            print(f"  bypass ngrok: {rc3.returncode}")
            time.sleep(2)
        
        time.sleep(1)
        
        # 3. Click Login
        rc4 = subprocess.run(f"{AB} click @e3", shell=True, capture_output=True, text=True, timeout=10)
        print(f"  click login: {rc4.returncode}")
        time.sleep(2)
        
        # 4. Fill credentials via JS for Clerk compatibility
        js_fill = f"""
        const emailInput = document.querySelector('input[type="email"]') || Array.from(document.querySelectorAll('input')).find(i => i.name === 'email' || i.placeholder === 'Email');
        const pwInput = document.querySelector('input[type="password"]') || Array.from(document.querySelectorAll('input')).find(i => i.name === 'password' || i.placeholder === 'Password');
        if (emailInput) {{
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, '{creds["email"]}');
            emailInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            emailInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            emailInput.dispatchEvent(new Event('blur', {{bubbles: true}}));
        }}
        if (pwInput) {{
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(pwInput, '{creds["pw"]}');
            pwInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            pwInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            pwInput.dispatchEvent(new Event('blur', {{bubbles: true}}));
        }}
        JSON.stringify({{email: emailInput?.value, pw: pwInput ? 'filled' : 'missing'}});
        """
        rc5, out5, _ = run(f'{AB} eval \'{js_fill}\'')
        print(f"  fill: {out5[:80]}")
        
        time.sleep(1)
        
        # 5. Click Sign In
        rc6 = subprocess.run(f"{AB} click @e8", shell=True, capture_output=True, text=True, timeout=10)
        print(f"  click signin: {rc6.returncode}")
        
        time.sleep(5)
        
        # 6. Check the page after login
        rc7, out7, _ = run(f"{AB} eval 'JSON.stringify({{url: location.href, title: document.title}})'")
        print(f"  post-login: {out7[:120]}")
        
        try:
            page_info = json.loads(out7)
            result["url"] = page_info.get("url", "")
            result["page_title"] = page_info.get("title", "")
        except:
            result["url"] = str(out7)[:100]
        
        # 7. Check for errors
        rc8, out8, _ = run(f"{AB} eval 'JSON.stringify({{errorEls: Array.from(document.querySelectorAll(\"[class*=error],[class*=Error],[id*=error]\")).length, hasErrorText: document.body.innerText.toLowerCase().includes(\"error\"), hasFailedText: document.body.innerText.toLowerCase().includes(\"failed\"), hasUndefined: document.body.innerText.includes(\"undefined\"), bodyPreview: document.body.innerText.substring(0, 500)}})'")
        print(f"  error check: {out8[:150]}")
        
        try:
            error_info = json.loads(out8)
            result["error_elements"] = error_info.get("errorEls", 0)
            result["error_count"] = (1 if error_info.get("hasErrorText") else 0) + (1 if error_info.get("hasFailedText") else 0)
            result["has_undefined"] = error_info.get("hasUndefined", False)
            result["body_preview"] = error_info.get("bodyPreview", "")[:200]
        except:
            pass
        
        # 8. Determine status
        if result["url"] and role.lower() in result["url"].lower():
            result["status"] = "passed"
        elif not result["url"]:
            result["status"] = "failed"
        else:
            result["status"] = "mismatch"
        
        # 9. Save auth state
        rc9 = subprocess.run(f"{AB} state save {AUTH_DIR / f'{role}.json'}", shell=True, capture_output=True, text=True, timeout=10)
        print(f"  save state: {rc9.returncode}")
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
    
    results[role] = result
    
    # Close session for next role
    subprocess.run(f"{AB} close --all", shell=True, capture_output=True, text=True, timeout=10)
    time.sleep(1)

print("\n\n=== PHASE 6 & 8 RESULTS ===")
print(json.dumps(results, indent=2))

# Summary
all_passed = all(r["status"] == "passed" for r in results.values())
any_errors = any(r["error_count"] > 0 for r in results.values())
print(f"\nAll roles logged in successfully: {all_passed}")
print(f"Any console errors: {any_errors}")
for role, r in results.items():
    emoji = "✅" if r["status"] == "passed" else "❌"
    err = " ⚠️ errors" if r.get("error_count", 0) > 0 else " ✅ clean"
    print(f"  {emoji} {role}: {r.get('url','?')}{err}")
