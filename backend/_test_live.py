"""Live test of the screening-to-assessment pipeline."""
import httpx, json, uuid, sys

BASE = 'http://localhost:8002'

# 1. Register a candidate
email = f'test-{uuid.uuid4().hex[:8]}@test.com'
r = httpx.post(f'{BASE}/api/auth/register', json={
    'name': 'Test Candidate', 'email': email, 'password': 'Candidate@123',
    'college': 'Test Uni', 'branch': 'CSE', 'cgpa': 8.5,
    'passed_out_year': 2025, 'language_choice': 'python',
})
result = r.json() if r.status_code != 201 else 'registered'
print(f'1. Register: {r.status_code}')
assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.text}'

# 2. Login as HR
r = httpx.post(f'{BASE}/api/auth/login', json={'email':'hr@knowledgefactory.com','password':'Hr@12345'})
assert r.status_code == 200
token = r.json()['access_token']
hr_headers = {'Authorization': f'Bearer {token}'}
print(f'2. HR Login: {r.status_code}')

# 3. Run screening
r = httpx.post(f'{BASE}/api/screening/run', headers=hr_headers)
print(f'3. Run screening: {r.status_code}, result: {r.json()}')
assert r.status_code == 200

# 4. Login as candidate
r = httpx.post(f'{BASE}/api/auth/login', json={'email': email, 'password': 'Candidate@123'})
assert r.status_code == 200
token = r.json()['access_token']
cand_headers = {'Authorization': f'Bearer {token}'}
candidate_id = r.json()['user']['id']
print(f'4. Candidate Login: {r.status_code}, id={candidate_id}')

# 5. Check profile
r = httpx.get(f'{BASE}/api/candidates/me', headers=cand_headers)
assert r.status_code == 200
assert r.json()['status'] == 'ROUND1_PASSED', f'Expected ROUND1_PASSED, got {r.json()["status"]}'
print(f'5. Profile after screening: {r.status_code}, status={r.json()["status"]}')

# 6. Start assessment
r = httpx.post(f'{BASE}/api/assessment/start', headers=cand_headers, json={'round':'ROUND_2'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
assessment_id = r.json()['id']
print(f'6. Start assessment: {r.status_code}, id={assessment_id}, status={r.json()["status"]}')

# 7. Check status after start
r = httpx.get(f'{BASE}/api/candidates/me', headers=cand_headers)
assert r.status_code == 200
assert r.json()['status'] == 'ROUND2_IN_PROGRESS', f'Expected ROUND2_IN_PROGRESS, got {r.json()["status"]}'
print(f'7. Status after start: {r.json()["status"]}')

# 8. Submit section
r = httpx.post(f'{BASE}/api/assessment/submit-section', headers=cand_headers, json={
    'assessment_id': assessment_id,
    'section': 'CODING',
    'content': {'code': 'print("hello")', 'problemId': 'q1'},
    'time_spent_seconds': 0,
})
print(f'8. Submit section: {r.status_code}, result: {r.json()}')
assert r.status_code == 200

# 9. Complete assessment
r = httpx.post(f'{BASE}/api/assessment/{assessment_id}/complete', headers=cand_headers)
print(f'9. Complete assessment: {r.status_code}')
assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
assert r.json()['status'] == 'COMPLETED', f'Expected COMPLETED, got {r.json()}'

# 10. Final status
r = httpx.get(f'{BASE}/api/candidates/me', headers=cand_headers)
assert r.status_code == 200
assert r.json()['status'] == 'ROUND2_PASSED', f'Expected ROUND2_PASSED, got {r.json()["status"]}'
print(f'10. Final status: {r.json()["status"]}')

print()
print('✓ Pipeline E2E passed! (screening → assessment → submit → complete)')
