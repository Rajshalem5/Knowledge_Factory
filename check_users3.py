#!/usr/bin/env python3
"""Check users in the database."""
import sqlite3

db_path = "/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check columns
print("=== COLUMNS ===")
cur.execute("PRAGMA table_info(users)")
for col in cur.fetchall():
    print(f"  {col}")

print("\n=== USERS ===")
try:
    cur.execute("SELECT id, email, role, status FROM users")
    for u in cur.fetchall():
        print(f"  ID={u[0][:20]:<22} Email={u[1]:<40} Role={u[2]:<15} Status={u[3]}")
except Exception as e:
    print(f"Error: {e}")
    # Try without status
    try:
        cur.execute("SELECT id, email, role FROM users")
        for u in cur.fetchall():
            print(f"  ID={u[0][:20]:<22} Email={u[1]:<40} Role={u[2]}")
    except Exception as e2:
        print(f"Error2: {e2}")
        cur.execute("SELECT * FROM users LIMIT 5")
        for row in cur.fetchall():
            print(f"  {row}")

print("\n=== CANDIDATES COUNT ===")
cur.execute("SELECT COUNT(*) FROM candidates")
print(f"  Total: {cur.fetchone()[0]}")

conn.close()
