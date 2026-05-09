"""Quick debug: test candidate retrieval"""
import httpx

BASE = "http://127.0.0.1:8001"

# Login as admin
r = httpx.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "admin123"})
print(f"Login: {r.status_code}")
if r.status_code != 200:
    r = httpx.post(f"{BASE}/api/auth/login", json={"email": "admin@knowledgefactory.io", "password": "Admin@12345"})
    print(f"Login try2: {r.status_code}")

d = r.json()
token = d["access_token"]
user = d["user"]
print(f"User: {user}")
headers = {"Authorization": f"Bearer {token}"}

# List candidates
r2 = httpx.get(f"{BASE}/api/candidates/?limit=10", headers=headers)
print(f"List candidates: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print(f"  Total: {data.get('pagination',{}).get('total')}")
    for c in data.get("data", []):
        print(f"  - {c['id']}: {c['name']} ({c['status']})")

# Try getting the registered candidate
if r2.status_code == 200:
    candidates = r2.json().get("data", [])
    for c in candidates:
        if "pipeline-test" in c.get("email", ""):
            cid = c["id"]
            print(f"\nFound candidate: {cid}")
            r3 = httpx.get(f"{BASE}/api/candidates/{cid}", headers=headers)
            print(f"Get candidate {cid}: {r3.status_code} - {r3.text[:200]}")
            break

# Check a specific ID
test_id = "37a7cabc-aa01-4b38-be3e-e57ad7ea0b2f"
r4 = httpx.get(f"{BASE}/api/candidates/{test_id}", headers=headers)
print(f"\nGet candidate {test_id}: {r4.status_code} - {r4.text[:200]}")
