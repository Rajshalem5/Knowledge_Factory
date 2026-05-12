"""Check candidate and assessment states."""
import sqlite3
conn = sqlite3.connect('knowledge_factory.db')

print("=== Candidates ===")
cursor = conn.execute("SELECT id, name, email, status FROM candidates ORDER BY created_at DESC")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | {row[1]:20s} | {row[2]:25s} | {row[3]}")
    
print("\n=== Assessments ===")
cursor = conn.execute("SELECT a.id, a.candidate_id, a.round, a.status, c.name FROM assessments a JOIN candidates c ON a.candidate_id = c.id ORDER BY a.started_at DESC")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | candidate={row[1][:8]}... | round={row[2]:10s} | status={row[3]} | {row[4]}")

print("\n=== Submissions ===")
cursor = conn.execute("SELECT id, assessment_id, section FROM submissions")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | assessment={row[1][:8]}... | section={row[2]}")

print("\n=== Hiring Cycles ===")
cursor = conn.execute("SELECT id, name, status, eligibility_config FROM hiring_cycles")
for row in cursor.fetchall():
    print(f"  {row[0][:8]}... | {row[1]:20s} | {row[2]} | {row[3]}")

conn.close()
