"""Test the new assessment_status filter via the live server."""
import httpx

BASE = 'http://localhost:8002'

# Login as admin
r = httpx.post(f'{BASE}/api/auth/login', json={'email':'admin@knowledgefactory.io','password':'Admin@12345'})
assert r.status_code == 200
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 1. Run screening to move some candidates to ROUND1_PASSED
r = httpx.post(f'{BASE}/api/screening/run', headers=headers)
data = r.json()
print(f'1. Screening: {data["screened"]} screened, {data["passed"]} passed')

# 2. Check candidates with COMPLETED assessments (should be 0 initially)
r = httpx.get(f'{BASE}/api/candidates/?assessment_status=COMPLETED', headers=headers)
data = r.json()
total_completed = data['pagination']['total']
print(f'2. Candidates with COMPLETED assessments: {total_completed}')

# 3. Check candidates with IN_PROGRESS assessments (should be 0 initially)
r = httpx.get(f'{BASE}/api/candidates/?assessment_status=IN_PROGRESS', headers=headers)
data = r.json()
total_in_progress = data['pagination']['total']
print(f'3. Candidates with IN_PROGRESS assessments: {total_in_progress}')

# 4. Verify the filter works on pipeline-stats too
r = httpx.get(f'{BASE}/api/screening/pipeline-stats?assessment_status=COMPLETED', headers=headers)
data = r.json()
print(f'4. Pipeline stats (COMPLETED assessments): total_filtered={data["aggregates"]["total_filtered"]}')

# 5. Verify funnel filter
r = httpx.get(f'{BASE}/api/analytics/funnel?assessment_status=COMPLETED', headers=headers)
data = r.json()
print(f'5. Funnel (COMPLETED assessments): {data}')

print()
print('Assessment status filter test passed!')
