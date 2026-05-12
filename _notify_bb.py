"""Notify Big Brother that a Knowledge Factory cron job is starting/completing."""
import socket
import sys

message = sys.argv[1] if len(sys.argv) > 1 else "Knowledge Factory cron job running"
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(('127.0.0.1', 9876))
    # Prefix with SAY: source ID so Big Brother's protocol interpreter can route it
    payload = message if message.startswith("SAY:") else f"SAY:hermes:{message}"
    s.sendall(payload.encode())
    s.close()
    print(f"Big Brother notified: {message}")
except Exception as e:
    print(f"Big Brother not reachable: {e}")
