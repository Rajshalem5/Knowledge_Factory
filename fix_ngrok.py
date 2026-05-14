#!/usr/bin/env python3
"""Kill existing ngrok and start new tunnel to port 8000."""
import subprocess, json, time, os

# Kill ANY lingering ngrok
subprocess.run(["pkill", "-9", "-f", "ngrok"], capture_output=True)
print("Killed old ngrok processes")
time.sleep(2)

# Also kill whatever on port 5000 to free the other app
# Actually just leave it, we just need ngrok for port 8000

# Ensure port 4040 (ngrok API) is free
subprocess.run(["pkill", "-9", "-f", "ngrok"], capture_output=True)
time.sleep(1)

# Start fresh ngrok pointing to port 8000
ngrok_proc = subprocess.Popen(
    ["ngrok", "http", "8000", "--log=stdout"],
    stdout=open("/tmp/ngrok_kf2.log", "w"),
    stderr=subprocess.STDOUT
)
print(f"ngrok PID: {ngrok_proc.pid}")
time.sleep(3)

# Get ngrok URL
for i in range(12):
    try:
        r = subprocess.run(["curl", "-s", "http://localhost:4040/api/tunnels"], capture_output=True, text=True, timeout=2)
        data = json.loads(r.stdout)
        tunnels = data.get("tunnels", [])
        if tunnels:
            url = tunnels[0]["public_url"]
            print(f"NGROK_URL={url}")
            with open("/tmp/kf_ngrok_url.txt", "w") as f:
                f.write(url)
            break
    except Exception as e:
        print(f"Attempt {i}: {e}")
    time.sleep(1)
else:
    print("ngrok tunnel not ready after 12s")
    # Show log
    r = subprocess.run(["cat", "/tmp/ngrok_kf2.log"], capture_output=True, text=True)
    print(r.stdout[-500:])
    sys.exit(1)

print("ngrok setup complete!")
