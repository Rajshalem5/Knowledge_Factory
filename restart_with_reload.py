#!/usr/bin/env python3
"""Kill old uvicorn, restart with --reload for model changes"""
import os, signal, time, subprocess

# Kill existing uvicorn
result = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True, timeout=5)
for pid in result.stdout.strip().split():
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
            print(f"Killed uvicorn PID {pid}")
        except Exception as e:
            print(f"Error killing {pid}: {e}")

time.sleep(2)

# Start with --reload
os.chdir("/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")
proc = subprocess.Popen(
    [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print(f"Started uvicorn PID {proc.pid} with --reload")

# Wait for ready
for i in range(20):
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:8000/health"], capture_output=True, text=True, timeout=3)
        if "ok" in r.stdout:
            print(f"Backend ready (attempt {i+1})")
            break
    except:
        pass
    time.sleep(1)
else:
    print("Backend failed to start")
    sys.exit(1)

# Test hiring cycles
print("\nTesting hiring cycles...")
r = subprocess.run(["curl", "-s", "http://localhost:8000/api/auth/login", "-H", "Content-Type: application/json", "-d", '{"email":"admin@knowledgefactory.io","password":"admin123"}'], capture_output=True, text=True, timeout=5)
import json
try:
    data = json.loads(r.stdout)
    token = data.get("access_token", "")
    print(f"Login: OK, token length: {len(token)}")
    
    r = subprocess.run(["curl", "-s", "http://localhost:8000/api/hiring-cycles/", "-H", f"Authorization: Bearer {token}"], capture_output=True, text=True, timeout=5)
    print(f"Hiring cycles: HTTP {r.returncode} - {r.stdout[:200]}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Login response: {r.stdout[:200]}")
