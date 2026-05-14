#!/usr/bin/env python3
"""Kill backend and restart with --reload to pick up model changes"""
import subprocess, time, os, signal

# Find and kill existing uvicorn processes
result = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True)
pids = result.stdout.strip().split()
print(f"Existing uvicorn PIDs: {pids}")

for pid in pids:
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
            print(f"Killed {pid}")
        except:
            pass

time.sleep(2)

# Kill again to be sure
result = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True)
if result.stdout.strip():
    pids = result.stdout.strip().split()
    for pid in pids:
        if pid:
            try:
                os.kill(int(pid), signal.SIGKILL)
                print(f"Force killed {pid}")
            except:
                pass

time.sleep(1)

# Start fresh backend
os.chdir("/opt/hermes_shared_memory/projects/Knowledge_Factory/backend")
proc = subprocess.Popen(
    [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    stdout=open("/tmp/kf_backend.log", "w"),
    stderr=subprocess.STDOUT
)
print(f"Backend started PID: {proc.pid}")

# Wait for it
for i in range(15):
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:8000/health"], capture_output=True, text=True, timeout=2)
        if r.stdout.strip():
            print(f"Backend ready: {r.stdout.strip()}")
            break
    except:
        pass
    time.sleep(1)
else:
    print("Backend failed to start!")
    subprocess.run(["cat", "/tmp/kf_backend.log"], capture_output=True)
    sys.exit(1)

print("Done! Backend is running with --reload")
