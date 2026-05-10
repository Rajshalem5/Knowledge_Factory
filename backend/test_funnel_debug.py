"""Debug the funnel filter issue."""
import httpx

BASE = 'http://127.0.0.1:8002'

r = httpx.post(f'{BASE}/api/auth/login', json={'email': 'hr@knowledgefactory.com', 'password': 'Hr@12345'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test each filter individually on the funnel
tests = [
    ("no filters", {}),
    ("branch=CSE", {"branch": "CSE"}),
    ("college=Test Uni", {"college": "Test Uni"}),
    ("search=Test", {"search": "Test"}),
    ("email=applied@test.com", {"email": "applied@test.com"}),
    ("cgpa_min=9.0", {"cgpa_min": 9.0}),
]

for name, params in tests:
    r = httpx.get(f'{BASE}/api/analytics/funnel', headers=headers, params=params)
    print(f'{name}: {r.json()}')
