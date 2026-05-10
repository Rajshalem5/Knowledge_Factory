"""Test the name filter on all endpoints."""
import httpx

BASE = 'http://127.0.0.1:8002'

# Login as HR
r = httpx.post(f'{BASE}/api/auth/login', json={'email': 'hr@knowledgefactory.com', 'password': 'Hr@12345'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test name filter on candidates list
r = httpx.get(f'{BASE}/api/candidates/?name=Test', headers=headers)
print(f'Name filter candidates: {r.status_code}')
data = r.json()
print(f'  Total: {data["pagination"]["total"]}')
for c in data['data']:
    print(f'  - {c["name"]} ({c["status"]})')

# Test name filter on pipeline stats
r = httpx.get(f'{BASE}/api/screening/pipeline-stats?name=Test', headers=headers)
print(f'Name filter pipeline-stats: {r.status_code}')
print(f'  Stats: {r.json()["stats"]}')

# Test name filter on funnel
r = httpx.get(f'{BASE}/api/analytics/funnel?name=Test', headers=headers)
print(f'Name filter funnel: {r.status_code}')
print(f'  Funnel: {r.json()}')

# Test screening with name filter
r = httpx.post(f'{BASE}/api/screening/run?name=Test', headers=headers)
print(f'Name filter screening run: {r.status_code}')
print(f'  Result: {r.json()}')

print()
print('All name filter endpoints work!')
