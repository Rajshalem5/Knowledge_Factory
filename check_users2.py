#!/usr/bin/env python3
"""Check what users exist in the database."""
import sqlite3
import sys

db_path = "/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check schema first
print("=== USERS TABLE SCHEMA ===")
cur.execute("PRAGMA table_info(users)")
for col in cur.fetchall():
    print(f"  {col}")

# Check users table
print("\n=== USERS TABLE ===")
cur.execute("SELECT id, email, role, is_active FROM users")
users = cur.fetchall()
for u in users:
    print(f"  ID={u[0][:20]:<22} Email={u[1]:<40} Role={u[2]:<15} Active={u[3]}")

# Check candidates table
print("\n=== CANDIDATES TABLE SCHEMA ===")
cur.execute("PRAGMA table_info(candidates)")
for col in cur.fetchall():
    print(f"  {col}")

print("\n=== CANDIDATES (first 20) ===")
cur.execute("SELECT id, user_id, status, college, name FROM candidates LIMIT 20")
for row in cur.fetchall():
    print(f"  Candidate ID={row[0][:20]:<22} UserID={str(row[1])[:20]:<22} Status={str(row[2]):<25} College={str(row[3]):<15} Name={row[4]}")

# Check candidate count by status
print("\n=== CANDIDATES BY STATUS ===")
cur.execute("SELECT status, COUNT(*) FROM candidates GROUP BY status ORDER BY status")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
