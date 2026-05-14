#!/usr/bin/env python3
"""Quick check ngrok interstitial page."""
import subprocess, time

AB = "/opt/hermes_shared_memory/bin/ab"

# Close any old sessions
subprocess.run([AB, "close", "--all"], capture_output=True, text=True, timeout=10)

# Open the page
r = subprocess.run([AB, "open", "https://ila-sturdiest-oversentimentally.ngrok-free.dev"], 
                   capture_output=True, text=True, timeout=30)
print(f"Open: rc={r.returncode}")
time.sleep(3)

# Snapshot to see what's on the page
r = subprocess.run([AB, "snapshot", "-i"], capture_output=True, text=True, timeout=15)
print(f"Snapshot ({len(r.stdout)} chars):")
print(r.stdout[:1500])

# Get all buttons
r = subprocess.run([AB, "eval", "document.querySelectorAll('button').length"], 
                   capture_output=True, text=True, timeout=15)
print(f"\nNumber of buttons: {r.stdout}")

# Get button texts
r = subprocess.run([AB, "eval", 
  "Array.from(document.querySelectorAll('button')).map(b => b.innerText)"], 
  capture_output=True, text=True, timeout=15)
print(f"Button texts: {r.stdout}")

# Try clicking the Visit Site button
r = subprocess.run([AB, "eval", 
  "(function(){ const btns = document.querySelectorAll('button'); for(const b of btns){ if(b.innerText.includes('Visit') || b.innerText.includes('Continue')){ b.click(); return 'clicked: '+b.innerText; } } return 'no match'; })()"], 
  capture_output=True, text=True, timeout=15)
print(f"Visit click: {r.stdout}")

time.sleep(3)

# Check title again
r = subprocess.run([AB, "eval", "document.title"], capture_output=True, text=True, timeout=15)
print(f"Title: {r.stdout}")

r = subprocess.run([AB, "eval", "document.body.innerText.substring(0, 500)"], 
                   capture_output=True, text=True, timeout=15)
print(f"Content: {r.stdout[:500]}")

# Screenshot
r = subprocess.run([AB, "screenshot", "/tmp/ngrok_page.png"], capture_output=True, text=True, timeout=15)
print(f"Screenshot: rc={r.returncode}")

# Close
subprocess.run([AB, "close", "--all"], capture_output=True, text=True, timeout=10)
