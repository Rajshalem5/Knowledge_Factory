#!/bin/bash
# Bulk FE Login + Console Check for all roles
AB="/opt/hermes_shared_memory/bin/ab"
NGROK="https://ila-sturdiest-oversentimentally.ngrok-free.dev"
AUTH_DIR="/opt/hermes_shared_memory/projects/Knowledge_Factory/auth"
mkdir -p "$AUTH_DIR"

login_role() {
  local email="$1" pw="$2" role="$3"
  
  echo "=== Testing $role ==="
  
  # Open app
  $AB open "$NGROK" 2>/dev/null
  sleep 2
  
  # Bypass ngrok interstitial if present
  snapshot=$($AB snapshot -c -i 2>/dev/null)
  if echo "$snapshot" | grep -q "Visit Site"; then
    $AB click @e6 2>/dev/null
    sleep 2
  fi
  
  # Click Login
  $AB click @e3 2>/dev/null
  sleep 2
  
  # Fill credentials via JS (handles Clerk React)
  $AB eval "
    var ei = document.querySelector('input[type=email]') || Array.from(document.querySelectorAll('input')).find(i=>i.name==='email'||i.placeholder==='Email');
    var pi = document.querySelector('input[type=password]') || Array.from(document.querySelectorAll('input')).find(i=>i.name==='password'||i.placeholder==='Password');
    if(ei){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(ei,'$email');ei.dispatchEvent(new Event('input',{bubbles:true}));ei.dispatchEvent(new Event('change',{bubbles:true}));ei.dispatchEvent(new Event('blur',{bubbles:true}));}
    if(pi){var s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(pi,'$pw');pi.dispatchEvent(new Event('input',{bubbles:true}));pi.dispatchEvent(new Event('change',{bubbles:true}));pi.dispatchEvent(new Event('blur',{bubbles:true}));}
    JSON.stringify({email:ei?.value,pw:pi?'filled':'missing'});
  " 2>/dev/null
  sleep 1
  
  # Click Sign In
  $AB click @e8 2>/dev/null
  sleep 5
  
  # Get page info
  info=$($AB eval "JSON.stringify({url:location.href,title:document.title})" 2>/dev/null)
  url=$(echo "$info" | python3 -c "import json,sys; d=json.loads(sys.stdin.read().strip()); print(d.get('url',''))" 2>/dev/null)
  title=$(echo "$info" | python3 -c "import json,sys; d=json.loads(sys.stdin.read().strip()); print(d.get('title',''))" 2>/dev/null)
  
  # Check for errors
  errcheck=$($AB eval "JSON.stringify({errorEls:document.querySelectorAll('[class*=error],[class*=Error],[id*=error]').length, hasError:document.body.innerText.toLowerCase().includes('error'), hasFailed:document.body.innerText.toLowerCase().includes('failed'), hasUndefined:document.body.innerText.includes('undefined')})" 2>/dev/null)
  
  # Save auth state
  $AB state save "$AUTH_DIR/$role.json" 2>/dev/null
  echo "INFO: url=$url title=$title errcheck=$errcheck"
  
  # Close session
  $AB close --all 2>/dev/null
  sleep 1
  
  # Return results
  if echo "$url" | grep -qi "$role"; then
    echo "STATUS: PASSED"
  else
    echo "STATUS: FAILED (expected route containing '$role', got: $url)"
  fi
  echo "---"
}

# Test each role
login_role "superadmin@knowledgefactory.io" "Super@12345" "superadmin"
login_role "admin@knowledgefactory.io" "admin123" "admin"
login_role "hr@knowledgefactory.io" "Hr@12345" "hr"
login_role "interviewer@test.com" "Interviewer@12345" "interviewer"
login_role "candidate@test.com" "Candidate@12345" "candidate"

echo ""
echo "=== PHASE 6 + 8 COMPLETE ==="
ls -la "$AUTH_DIR"/
