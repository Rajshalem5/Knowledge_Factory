#!/usr/bin/env python3
"""Diagnose hiring cycles - using raw sqlite3"""
import sqlite3, json

db_path = "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check table info
cur.execute("PRAGMA table_info(hiring_cycles)")
cols = cur.fetchall()
print("Hiring cycles columns:")
for c in cols:
    print(f"  {c}")

# Check all rows
cur.execute("SELECT * FROM hiring_cycles")
rows = cur.fetchall()
print(f"\nHiring cycles rows ({len(rows)}):")
for row in rows:
    print(f"  {row}")

conn.close()
