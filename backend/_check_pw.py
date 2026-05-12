"""Check passwords in the dev database."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.config import settings
from app.core.security import verify_password, hash_password
from sqlalchemy import create_engine, text

sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
engine = create_engine(sync_url)

print(f"DB URL: {settings.DATABASE_URL}")
print()

# Test users
test_users = [
    ("admin@test.com", "admin123"),
    ("admin@test.com", "Admin@12345"),
    ("hr@test.com", "Hr@12345"),
    ("interviewer@test.com", "Interview@123"),
    ("admin@knowledgefactory.io", "admin123"),
    ("admin@knowledgefactory.io", "Admin@12345"),
]

with engine.connect() as conn:
    for email, pwd in test_users:
        row = conn.execute(
            text("SELECT password_hash FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
        if row:
            result = verify_password(pwd, row[0])
            print(f"  user: {email:35} | pw: {pwd:20} | match: {result}")
            if not result:
                # Show what the hash looks like
                print(f"    hash: {row[0][:60]}...")
        else:
            print(f"  user: {email:35} | NOT FOUND")

print()
print("=== Hash test ===")
h = hash_password("admin123")
print(f"admin123 -> {h[:60]}")
print(f"Verify: {verify_password('admin123', h)}")
h2 = hash_password("Hr@12345")
print(f"Hr@12345 -> {h2[:60]}")
print(f"Verify: {verify_password('Hr@12345', h2)}")
