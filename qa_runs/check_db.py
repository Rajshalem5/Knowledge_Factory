#!/usr/bin/env python3
"""Check the actual users in the Knowledge Factory database."""
import sqlite3
import os

db_path = "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check users table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f"Tables ({len(tables)}):")
for t in tables:
    print(f"  - {t[0]}")

# Check auth users
print("\n=== Users (auth/accounts) ===")
try:
    cursor.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"  Columns: {cols}")
    cursor.execute("SELECT id, email, role, full_name FROM users LIMIT 20")
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} | role={r[2]} | name={r[3]}")
except Exception as e:
    print(f"  Error: {e}")

# Check candidates table
print("\n=== Candidates ===")
try:
    cursor.execute("PRAGMA table_info(candidates)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"  Columns: {cols}")
    cursor.execute("SELECT id, email, full_name, status FROM candidates LIMIT 20")
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} | {r[2]} | status={r[3]}")
except Exception as e:
    print(f"  Error: {e}")

# Check hiring cycles
print("\n=== Hiring Cycles ===")
try:
    cursor.execute("SELECT id, name, status, eligibility_config FROM hiring_cycles LIMIT 5")
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} | status={r[2]} | config={str(r[3])[:100]}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
