#!/usr/bin/env python3
"""Debug ngrok interstitial click through."""
import subprocess, time

AB = "/opt/hermes_shared_memory/bin/ab"

def run(args):
    r = subprocess.run([AB]+args, capture_output=True, text=True, timeout=30)
    print(f"  {' '.join(args[:4]):40s} rc={r.returncode} | {r.stdout[:120]}")
    return r

# Close everything
subprocess.run([AB, "close", "--all"], capture_output=True, text=True)
time.sleep(1)

print("=== Test 1: open with --session ===")
run(["--session", "test1", "open", "https://ila-sturdiest-oversentimentally.ngrok-free.dev"])
time.sleep(3)
run(["--session", "test1", "eval", "document.title"])

# Try clicking via different methods
print("\n=== Test click methods ===")
# Method 1: ref-based click
run(["--session", "test1", "snapshot", "-i"])
time.sleep(1)
run(["--session", "test1", "click", "@e6"])
time.sleep(3)
run(["--session", "test1", "eval", "document.title"])

# If still interstitial, try JS
run(["--session", "test1", "eval", "document.querySelector('button')?.click()"])
time.sleep(3)
run(["--session", "test1", "eval", "document.title"])

# Try explicit eval click
run(["--session", "test1", "eval", 
     "(function(){ var btn = document.querySelector('button'); if(btn){ btn.click(); return 'clicked'; } return 'no button'; })()"])
time.sleep(3)
run(["--session", "test1", "eval", "document.title"])

# Screenshot to see state
run(["--session", "test1", "screenshot", "/tmp/ngrok_test1.png"])

subprocess.run([AB, "close", "--all"], capture_output=True, text=True)
