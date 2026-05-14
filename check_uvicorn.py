#!/usr/bin/env python3
"""Check uvicorn process and restart if needed."""
import os, signal, time
import subprocess

# Check current uvicorn processes
result = subprocess.run(["pgrep", "-a", "uvicorn"], capture_output=True, text=True, timeout=5)
print("Current uvicorn processes:")
print(result.stdout or "  (none)")

# Check if backend is responding
result = subprocess.run(["curl", "-s", "http://localhost:8000/health"], capture_output=True, text=True, timeout=5)
print(f"\nHealth check: {result.stdout}")

# Check what the backend log shows
result = subprocess.run(["tail", "-5", "/tmp/kf_backend.log"], capture_output=True, text=True, timeout=5)
print(f"\nBackend log (last 5 lines):\n{result.stdout}")
