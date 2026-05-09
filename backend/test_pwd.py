"""Test password hashing."""
import sys
sys.path.insert(0, '.')
from app.core.security import hash_password, verify_password

h = hash_password("Admin@12345")
print(f"Hash: {h[:50]}...")
print(f"Type: {'argon2' if h.startswith('$argon2') else 'bcrypt' if h.startswith('$2b') else 'unknown'}")

result = verify_password("Admin@12345", h)
print(f"Verify correct: {result}")

result2 = verify_password("wrong", h)
print(f"Verify wrong: {result2}")
