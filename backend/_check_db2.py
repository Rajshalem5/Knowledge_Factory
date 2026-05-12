"""Check what users exist in the dev database."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app.config import settings
from sqlalchemy import create_engine, text

db_url = settings.DATABASE_URL
print(f"DB URL: {db_url}")

sync_url = db_url.replace("+aiosqlite", "").replace("+asyncpg", "")
engine = create_engine(sync_url)

with engine.connect() as conn:
    # Check users
    rows = conn.execute(text("SELECT id, email, role, status, password_hash FROM users")).fetchall()
    print(f"\n=== USERS ({len(rows)}) ===")
    for row in rows:
        pw_hash = row[4][:40] if row[4] else "NULL"
        print(f"  {str(row[0])[:8]:8} | {row[1]:35} | role={row[2]:15} | status={row[3]:8} | hash={pw_hash}...")
    
    # Check candidates
    try:
        rows = conn.execute(text("SELECT id, email, status, password_hash, name FROM candidates")).fetchall()
        print(f"\n=== CANDIDATES ({len(rows)}) ===")
        for row in rows:
            pw_hash = row[3][:40] if row[3] else "NULL"
            print(f"  {str(row[0])[:8]:8} | {row[1]:30} | status={row[2]:20} | hash={pw_hash}... | name={row[4]}")
    except Exception as e:
        print(f"\nError reading candidates: {e}")
