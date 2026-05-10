"""Test the funnel applied count with and without name filter."""
import httpx

BASE = 'http://127.0.0.1:8002'

# Login as HR
r = httpx.post(f'{BASE}/api/auth/login', json={'email': 'hr@knowledgefactory.com', 'password': 'Hr@12345'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test funnel WITHOUT filters
r = httpx.get(f'{BASE}/api/analytics/funnel', headers=headers)
print(f'Funnel (no filters): {r.json()}')

# Test funnel WITH name filter
r = httpx.get(f'{BASE}/api/analytics/funnel?name=Test', headers=headers)
print(f'Funnel (name=Test): {r.json()}')

# Test funnel with email filter (exact match - should show 0-1)
r = httpx.get(f'{BASE}/api/analytics/funnel?email=applied@test.com', headers=headers)
print(f'Funnel (email=applied@test.com): {r.json()}')

# Pipeline stats for comparison
r = httpx.get(f'{BASE}/api/screening/pipeline-stats', headers=headers)
print(f'Pipeline stats (no filters): {r.json()["stats"]}')
