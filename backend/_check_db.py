"""Check database contents."""
import sqlite3
conn = sqlite3.connect('knowledge_factory.db')
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('Tables:', tables)

# Check users
if 'users' in tables:
    cur.execute('SELECT id, email, role FROM users LIMIT 5')
    for row in cur.fetchall():
        print(f'User: {row}')

# Check hiring cycles
if 'hiring_cycles' in tables:
    cur.execute('SELECT id, name, status, eligibility_config FROM hiring_cycles LIMIT 5')
    for row in cur.fetchall():
        print(f'Cycle: {row}')

# Check candidates
if 'candidates' in tables:
    cur.execute('SELECT id, email, name, status, cgpa, branch FROM candidates LIMIT 10')
    for row in cur.fetchall():
        print(f'Candidate: {row}')

conn.close()
