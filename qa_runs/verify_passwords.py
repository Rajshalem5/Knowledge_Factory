#!/usr/bin/env python3
"""Verify passwords against stored hashes."""
import bcrypt
import sqlite3

db_path = "/opt/hermes_shared_memory/projects/Knowledge_Factory/backend/knowledge_factory.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Test specific passwords
test_passwords = {
    "admin@test.com": "admin123",
    "hr@test.com": "Hr@12345",
    "interviewer@test.com": "Interviewer@12345",
    "hr@knowledgefactory.io": "Hr@12345",
    "interviewer@knowledgefactory.io": "Interviewer@12345",
    "superadmin@knowledgefactory.io": "Super@12345",
    "admin@knowledgefactory.io": "admin123",
    "candidate@test.com": "Candidate@12345",
    "alice@test.com": "Candidate@12345",
}

# First, get hashes
cursor.execute("SELECT email, password_hash FROM users")
user_hashes = dict(cursor.fetchall())
cursor.execute("SELECT email, password_hash FROM candidates")
candidate_hashes = dict(cursor.fetchall())

print("=== Password verification ===\n")
for email, pwd in test_passwords.items():
    h = user_hashes.get(email) or candidate_hashes.get(email, "")
    if not h:
        print(f"  {email}: NOT FOUND in DB")
        continue
    h_bytes = h.encode('utf-8') if isinstance(h, str) else h
    pwd_bytes = pwd.encode('utf-8')
    try:
        result = bcrypt.checkpw(pwd_bytes, h_bytes)
        print(f"  {'✅' if result else '❌'} {email}: pwd='{pwd}' -> {'MATCH' if result else 'MISMATCH'}")
    except Exception as e:
        print(f"  💥 {email}: ERROR: {e}")
