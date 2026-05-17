#!/usr/bin/env python3
"""Save auth state for remaining roles using agent-browser."""
import json, subprocess, time

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"

ROLES = {
    "admin": {"email": "admin@knowledgefactory.io", "pw": "admin123"},
    "hr": {"email": "hr@knowledgefactory.io", "pw": "Hr@12345"},
    "interviewer": {"email": "interviewer@test.com", "pw": "Interviewer@12345"},
    "candidate": {"email": "candidate@test.com", "pw": "Candidate@12345"},
}

def run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

results = {}

for role, creds in ROLES.items():
    print(f"\n{'='*50}")
    print(f"  Role: {role}")
    print(f"{'='*50}")
    
    try:
        run(f"{AB} close --all", timeout=5)
        time.sleep(1)
        
        run(f"{AB} open {NGROK}", timeout=15)
        time.sleep(3)
        
        # Bypass ngrok
        _, snap, _ = run(f"{AB} snapshot -c", timeout=10)
        if "Visit Site" in snap:
            run(f"{AB} click @e6", timeout=10)
            print("  Bypassed ngrok")
            time.sleep(3)
        
        # Click Login button - parse ref from snapshot
        _, snap, _ = run(f"{AB} snapshot -c", timeout=10)
        for line in snap.split('\n'):
            if 'Login' in line and '@e' in line:
                parts = line.split('@e')
                if len(parts) > 1:
                    ref = parts[1].split(']')[0].split(' ')[0].strip('"')
                    run(f"{AB} click @e{ref}", timeout=10)
                    print(f"  Clicked Login @e{ref}")
                    time.sleep(2)
                    break
        
        # Fill and submit using eval with explicit JS
        fill_js = """
        (function() {
          var inputs = document.querySelectorAll('input');
          var emailInput = null, pwInput = null;
          for (var i = 0; i < inputs.length; i++) {
            var inp = inputs[i];
            if (inp.type === 'email' || inp.name === 'email') { emailInput = inp; }
            if (inp.type === 'password') { pwInput = inp; }
          }
          if (emailInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, arguments[0]);
            emailInput.dispatchEvent(new Event('input', {bubbles: true}));
            emailInput.dispatchEvent(new Event('change', {bubbles: true}));
          }
          if (pwInput) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(pwInput, arguments[1]);
            pwInput.dispatchEvent(new Event('input', {bubbles: true}));
            pwInput.dispatchEvent(new Event('change', {bubbles: true}));
          }
          var form = emailInput ? emailInput.closest('form') : null;
          if (form) { form.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true})); return 'submitted'; }
          return emailInput ? 'filled' : 'no inputs';
        })()
        """
        # Replace placeholders with actual credentials
        fill_js = fill_js.replace('arguments[0]', '"' + creds['email'] + '"')
        fill_js = fill_js.replace('arguments[1]', '"' + creds['pw'] + '"')
        
        run(f'{AB} eval \'{fill_js}\'', timeout=15)
        time.sleep(5)
        
        _, url, _ = run(f"{AB} eval 'location.href'", timeout=10)
        url = url.strip('"').strip("'")
        print(f"  URL: {url}")
        
        state_file = f"{AUTH_DIR}/{role}.json"
        run(f"{AB} state save {state_file}", timeout=10)
        print(f"  Saved: {state_file}")
        
        results[role] = {"url": url, "ok": '/login' not in url}
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results[role] = {"url": "", "ok": False}
    
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)

print(f"\n\n{'='*50}")
print("  RESULTS")
print(f"{'='*50}")
for role, r in results.items():
    icon = "✅" if r.get("ok") else "❌"
    print(f"  {icon} {role}: {r.get('url', 'N/A')}")
