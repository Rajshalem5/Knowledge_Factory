#!/usr/bin/env python3
"""Check password hashes in DB."""
import sqlite3

db_path = "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check password hashes in users
print("=== Users password hashes ===")
cursor.execute("SELECT id, email, name, role, password_hash FROM users")
rows = cursor.fetchall()
for r in rows:
    ph = r[4]
    ph_preview = (ph[:40] + "...") if ph and len(ph) > 40 else (ph or "NULL")
    print(f"  {r[1]} | name={r[2]} | role={r[3]} | hash={ph_preview}")

# Check password hashes in candidates
print("\n=== Candidates password hashes ===")
cursor.execute("SELECT id, email, name, status, password_hash FROM candidates LIMIT 10")
rows = cursor.fetchall()
for r in rows:
    ph = r[4]
    ph_preview = (ph[:40] + "...") if ph and len(ph) > 40 else (ph or "NULL")
    print(f"  {r[1]} | name={r[2]} | status={r[3]} | hash={ph_preview}")

conn.close()
