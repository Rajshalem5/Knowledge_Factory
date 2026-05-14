#!/usr/bin/env python3
"""Check users with correct column names."""
import sqlite3

db_path = "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check all users
print("=== Users ===")
cursor.execute("SELECT id, email, name, role FROM users")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]} | name={r[2]} | role={r[3]}")

# Check all candidates  
print("\n=== Candidates ===")
cursor.execute("SELECT id, email, name, status FROM candidates")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]} | name={r[2]} | status={r[3]}")

# Check assessment table
print("\n=== Assessments ===")
try:
    cursor.execute("PRAGMA table_info(assessments)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"  Columns: {cols}")
    cursor.execute("SELECT * FROM assessments LIMIT 10")
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
