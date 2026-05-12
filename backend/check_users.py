"""Check users in dev database."""
import sqlite3
conn = sqlite3.connect('knowledge_factory.db')
cursor = conn.execute("SELECT id, email, name, role, status, password_hash FROM users")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | {row[1]:30s} | {row[2]:20s} | {row[3]:12s} | {row[4]:8s} | {row[5][:30]}...")

cursor = conn.execute("SELECT id, email, name, status, password_hash FROM candidates LIMIT 5")
print("\nCandidates (sample):")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | {row[1]:30s} | {row[2]:25s} | {row[3]}")
conn.close()
