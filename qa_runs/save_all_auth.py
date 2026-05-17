#!/usr/bin/env python3
"""Save auth state for all roles using agent-browser."""
import json, subprocess, time, sys

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
        # Close any existing session
        run(f"{AB} close --all", timeout=5)
        time.sleep(1)
        
        # Navigate
        run(f"{AB} open {NGROK}", timeout=15)
        time.sleep(3)
        
        # Bypass ngrok interstitial if needed
        _, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
        if "Visit Site" in snap:
            run(f"{AB} click @e6", timeout=10)
            print("  Bypassed ngrok interstitial")
            time.sleep(3)
        
        # Click Login
        _, snap, _ = run(f"{AB} snapshot -c -i", timeout=10)
        if "Login" in snap:
            # Find Login button ref
            for line in snap.split('\n'):
                if 'Login' in line and '@e' in line:
                    ref = line.split('@e')[1].split(']')[0]
                    run(f"{AB} click @e{ref}", timeout=10)
                    print(f"  Clicked Login (@e{ref})")
                    time.sleep(2)
                    break
        
        # Fill email and password using eval
        fill_js = f"""
        (function() {{
          var inputs = document.querySelectorAll('input');
          var emailInput = null, pwInput = null;
          for (var i = 0; i < inputs.length; i++) {{
            var inp = inputs[i];
            if (inp.type === 'email' || inp.name === 'email' || (inp.placeholder && inp.placeholder.toLowerCase().includes('email'))) {{
              emailInput = inp;
            }}
            if (inp.type === 'password' || inp.name === 'password' || (inp.placeholder && inp.placeholder.toLowerCase().includes('password'))) {{
              pwInput = inp;
            }}
          }}
          if (emailInput) {{
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInput, '{creds["email"]}');
            emailInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            emailInput.dispatchEvent(new Event('change', {{bubbles: true}}));
          }}
          if (pwInput) {{
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(pwInput, '{creds["pw"]}');
            pwInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            pwInput.dispatchEvent(new Event('change', {{bubbles: true}}));
          }}
          var form = emailInput ? emailInput.closest('form') : null;
          if (form) {{
            form.dispatchEvent(new Event('submit', {{bubbles: true, cancelable: true}}));
            return 'Form submitted';
          }}
          return emailInput ? 'email filled, no form' : 'inputs not found';
        }})()
        """
        rc, out, _ = run(f'{AB} eval \'{fill_js}\'', timeout=15)
        print(f"  Form: {out[:100]}")
        time.sleep(5)
        
        # Check URL
        _, url, _ = run(f"{AB} eval 'location.href'", timeout=10)
        url_clean = url.strip('"').strip("'")
        print(f"  URL: {url_clean}")
        
        # Save auth state
        state_file = f"{AUTH_DIR}/{role}.json"
        run(f"{AB} state save {state_file}", timeout=10)
        print(f"  State saved to {state_file}")
        
        # Check page for errors
        _, err_check, _ = run(f"{AB} eval 'JSON.stringify({{url: location.href, hasError: document.body.innerText.toLowerCase().includes(\"error\"), hasFailed: document.body.innerText.toLowerCase().includes(\"failed\"), text: document.body.innerText.substring(0,200)}})'", timeout=10)
        print(f"  Page check: {err_check[:200]}")
        
        results[role] = {"url": url_clean, "status": "ok" if url_clean and ('/login' not in url_clean) else "stuck"}
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results[role] = {"url": "", "status": "error", "error": str(e)}
    
    # Close session
    run(f"{AB} close --all", timeout=5)
    time.sleep(1)

print(f"\n\n{'='*50}")
print("  RESULTS")
print(f"{'='*50}")
for role, r in results.items():
    status = "✅" if r.get("status") == "ok" else "❌"
    print(f"  {status} {role}: {r.get('url', 'N/A')}")
print(f"\n  Auth states saved to: {AUTH_DIR}")
