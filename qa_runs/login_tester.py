#!/usr/bin/env python3
"""Rapid browser login test using agent-browser eval for all roles."""
import subprocess, json, time, sys

AB = "/opt/hermes_shared_memory/bin/ab"
NGROK = "https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR = "/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"

ROLES = {
    "superadmin": ("superadmin@knowledgefactory.io", "Super@12345"),
    "admin": ("admin@knowledgefactory.io", "admin123"),
    "hr": ("hr@knowledgefactory.io", "Hr@12345"),
    "interviewer": ("interviewer@test.com", "Interviewer@12345"),
    "candidate": ("candidate@test.com", "Candidate@12345"),
}

def eval_js(js_code):
    r = subprocess.run(f'{AB} eval {json.dumps(js_code)} 2>&1', shell=True, capture_output=True, text=True, timeout=15)
    out = r.stdout.strip()
    # Strip the warning prefix
    lines = out.split('\n')
    for l in lines:
        if l.startswith('"') or l.startswith('{') or l.startswith('[') or l.startswith('null'):
            return l
    return lines[-1] if lines else out

def close_tab():
    subprocess.run(f'{AB} close 2>&1', shell=True, capture_output=True, timeout=5)

close_tab()
time.sleep(1)

results = []

for role_name, (email, pw) in ROLES.items():
    print(f"\n{'='*60}")
    print(f"  ROLE: {role_name.upper()} ({email})")
    print(f"{'='*60}")
    
    # Open app
    print(f"  Opening app...")
    subprocess.run(f'{AB} open "{NGROK}" 2>&1', shell=True, timeout=15)
    time.sleep(3)
    
    # Bypass ngrok interstitial if visible - eval approach doesn't need this as we already bypassed
    
    # Click Login button (index 1)
    print(f"  Clicking Login...")
    eval_js("document.querySelectorAll('button')[1].click()")
    time.sleep(3)
    
    # Fill credentials
    print(f"  Filling credentials...")
    eval_js(f"""(function() {{
      const inputs = document.querySelectorAll('input');
      if (inputs.length < 2) return JSON.stringify({{error: 'not enough inputs', count: inputs.length}});
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(inputs[0], '{email}');
      inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
      inputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
      setter.call(inputs[1], '{pw}');
      inputs[1].dispatchEvent(new Event('input', {{bubbles: true}}));
      inputs[1].dispatchEvent(new Event('change', {{bubbles: true}}));
      return JSON.stringify({{email_set: inputs[0].value, pw_set: inputs[1].value ? 'yes' : 'no'}});
    }})()""")
    time.sleep(1)
    
    # Click Sign In button
    print(f"  Clicking Sign In...")
    result = eval_js("""(function() {
      const btns = document.querySelectorAll('button');
      for (let i = 0; i < btns.length; i++) {
        if (btns[i].textContent.trim() === 'Sign In') {
          btns[i].click();
          return JSON.stringify({clicked: true});
        }
      }
      return JSON.stringify({clicked: false, buttons: Array.from(btns).map(b => b.textContent.trim())});
    })()""")
    print(f"  Sign In result: {result}")
    time.sleep(5)
    
    # Check URL and page content
    url_info = eval_js("JSON.stringify({url: window.location.href, title: document.title})")
    print(f"  URL: {url_info}")
    
    # Check page content
    page_text = eval_js("document.body.innerText.substring(0, 300)")
    print(f"  Page: {page_text[:200]}")
    
    # Determine login success
    current_url = json.loads(url_info).get('url', '') if url_info.startswith('{') else url_info
    
    # Save auth state
    subprocess.run(f'{AB} state save "{AUTH_DIR}/{role_name}.json" 2>&1', shell=True, capture_output=True, timeout=10)
    print(f"  State saved to {AUTH_DIR}/{role_name}.json")
    
    # Check if login succeeded (URL should have changed from /login or /)
    if '/superadmin' in current_url or '/admin' in current_url or '/dashboard' in current_url or '/hr' in current_url or '/interviewer' in current_url or '/candidate' in current_url:
        print(f"  ✅ {role_name}: LOGIN SUCCESSFUL -> {current_url}")
        results.append({"role": role_name, "ok": True, "url": current_url[:100], "error": None})
    elif '/login' in current_url or 'accounts' in current_url:
        print(f"  ❌ {role_name}: LOGIN FAILED - still on login page")
        results.append({"role": role_name, "ok": False, "url": current_url[:100], "error": "stuck_on_login"})
    else:
        print(f"  ⚠️  {role_name}: UNCLEAR - staying on {current_url}")
        results.append({"role": role_name, "ok": False, "url": current_url[:100], "error": "unexpected_url"})
    
    # Close tab for next role
    close_tab()
    time.sleep(2)

# Summary
print(f"\n{'='*60}")
print(f"  LOGIN TEST RESULTS")
print(f"{'='*60}")
for r in results:
    icon = "✅" if r["ok"] else "❌"
    print(f"  {icon} {r['role']}: {r['url'][:80]} {r.get('error','') or ''}")

print(f"\n{json.dumps({'login_results': results})}")
