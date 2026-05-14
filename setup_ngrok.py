#!/usr/bin/env python3
"""Setup ngrok tunnel for KF QA testing."""
import os, subprocess, json, time, sys

# Kill existing ngrok processes
subprocess.run(["pkill", "-9", "-f", "ngrok"], capture_output=True)
time.sleep(1)

# Kill whatever is on port 5000 (the other app)
subprocess.run(["pkill", "-9", "-f", "uvicorn"], capture_output=True)
# Wait
time.sleep(2)

# Start fresh backend on port 8000
os.chdir("/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")
proc = subprocess.Popen(
    [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=open("/tmp/kf_backend.log", "w"),
    stderr=subprocess.STDOUT
)
print(f"Backend PID: {proc.pid}")

# Wait for backend
for i in range(20):
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:8000/health"], capture_output=True, text=True, timeout=2)
        if r.stdout.strip():
            print(f"Backend ready: {r.stdout.strip()}")
            break
    except:
        pass
    time.sleep(1)
else:
    print("Backend NOT ready after 20s")
    sys.exit(1)

# Verify SPA serving works
r = subprocess.run(["curl", "-s", "http://localhost:8000/"], capture_output=True, text=True, timeout=2)
if "root" in r.stdout:
    print("SPA serving: OK")
else:
    print("SPA serving: FAIL - checking main.py")
    sys.exit(1)

# Start ngrok on port 8000
ngrok_proc = subprocess.Popen(
    ["ngrok", "http", "8000", "--log=stdout"],
    stdout=open("/tmp/ngrok_kf.log", "w"),
    stderr=subprocess.STDOUT
)
print(f"ngrok PID: {ngrok_proc.pid}")
time.sleep(3)

# Get ngrok URL
for i in range(10):
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:4040/api/tunnels"], capture_output=True, text=True, timeout=2)
        data = json.loads(r.stdout)
        tunnels = data.get("tunnels", [])
        if tunnels:
            url = tunnels[0]["public_url"]
            print(f"NGROK_URL={url}")
            # Save to file
            with open("/tmp/kf_ngrok_url.txt", "w") as f:
                f.write(url)
            break
    except:
        pass
    time.sleep(1)
else:
    print("ngrok tunnel not ready")
    sys.exit(1)

print("Setup complete!")
print(f"Backend PID: {proc.pid}")
print(f"ngrok PID: {ngrok_proc.pid}")
