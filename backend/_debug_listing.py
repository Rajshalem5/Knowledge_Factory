"""Debug the candidate listing — raw response."""
import httpx

BASE = "http://localhost:8000"

# Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
token = r.json()["access_token"]

# Try listing without any filters
r = httpx.get(f"{BASE}/api/candidates/", headers={"Authorization": f"Bearer {token}"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Keys: {list(data.keys())}")
    print(f"Data content: {str(data)[:500]}")
else:
    print(f"Error: {r.text[:500]}")

# Try with explicit cycle_id from db
import sqlite3
conn = sqlite3.connect('knowledge_factory.db')
cur = conn.cursor()
cur.execute("SELECT id, name, status FROM hiring_cycles WHERE status = 'ACTIVE'")
cycles = cur.fetchall()
print(f"\nActive cycles: {cycles}")
cur.execute("SELECT id, name, status FROM hiring_cycles")
all_cycles = cur.fetchall()
print(f"All cycles: {all_cycles}")
cur.execute("SELECT COUNT(*) FROM candidates")
print(f"Candidate count: {cur.fetchone()[0]}")
cur.execute("SELECT id, email, status, cycle_id FROM candidates LIMIT 5")
for row in cur.fetchall():
    print(f"  Candidate: id={str(row[0])[:12]}, email={row[1]}, status={row[2]}, cycle_id={str(row[3])[:20] if row[3] else 'NULL'}")
conn.close()

# Try listing with cycle_id if available
if cycles:
    cycle_id = str(cycles[0][0])
    r = httpx.get(f"{BASE}/api/candidates/?cycle_id={cycle_id}", headers={"Authorization": f"Bearer {token}"})
    print(f"\nWith cycle_id filter: Status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get('data', data.get('items', data.get('candidates', [])))
        print(f"Items: {len(items)}")
        print(f"Full: {str(data)[:300]}")
