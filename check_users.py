#!/usr/bin/env python3
"""Check what users exist in the database."""
import sqlite3
import sys

db_path = "/mnt/hermes-shared/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check users table
print("=== USERS TABLE ===")
cur.execute("SELECT id, email, role, full_name, is_active FROM users")
users = cur.fetchall()
for u in users:
    print(f"  ID={u[0]:<40} Email={u[1]:<40} Role={u[2]:<15} Name={u[3]:<20} Active={u[4]}")

# Check candidates table
print("\n=== CANDIDATES TABLE ===")
cur.execute("SELECT id, user_id, status, college FROM candidates LIMIT 10")
for row in cur.fetchall():
    print(f"  Candidate ID={row[0]:<40} UserID={row[1]:<40} Status={row[2]:<20} College={row[3]}")

# Check candidate count by status
print("\n=== CANDIDATES BY STATUS ===")
cur.execute("SELECT status, COUNT(*) FROM candidates GROUP BY status")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
