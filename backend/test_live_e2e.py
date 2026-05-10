"""Live E2E pipeline test against running server."""
import httpx, time

BASE = 'http://127.0.0.1:8002'

def main():
    # 1. Register a new candidate
    unique = str(int(time.time()))
    email = f'e2e-{unique}@test.com'
    r = httpx.post(f'{BASE}/api/auth/register', json={
        'name': 'E2E Test', 'email': email, 'password': 'Candidate@123',
        'college': 'Test Uni', 'branch': 'CSE', 'cgpa': 8.5,
        'passed_out_year': 2026, 'language_choice': 'python',
    })
    print(f'1. Register: {r.status_code}')
    assert r.status_code == 201, f'FAIL: {r.text[:200]}'
    candidate_token = r.json()['access_token']

    # 2. Get my profile
    r = httpx.get(f'{BASE}/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
    print(f'2. Profile: {r.status_code} - status={r.json()["status"]}')
    assert r.status_code == 200
    assert r.json()['status'] == 'APPLIED'

    # 3. Login as HR
    r = httpx.post(f'{BASE}/api/auth/login', json={'email': 'hr@knowledgefactory.com', 'password': 'Hr@12345'})
    print(f'3. HR Login: {r.status_code}')
    assert r.status_code == 200
    hr_token = r.json()['access_token']
    hr_headers = {'Authorization': f'Bearer {hr_token}'}

    # 4. Run screening
    r = httpx.post(f'{BASE}/api/screening/run', headers=hr_headers)
    print(f'4. Screening: {r.status_code} - {r.json()}')
    assert r.status_code == 200

    # 5. Check candidate status after screening
    r = httpx.get(f'{BASE}/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
    print(f'5. After screening: status={r.json()["status"]}')
    assert r.json()['status'] == 'ROUND1_PASSED'

    # 6. Start assessment (ROUND_2)
    r = httpx.post(f'{BASE}/api/assessment/start', headers={'Authorization': f'Bearer {candidate_token}'},
                   json={'round': 'ROUND_2'})
    print(f'6. Start assessment: {r.status_code}')
    if r.status_code != 200:
        print(f'  FAIL: {r.text[:200]}')
        return False
    assessment = r.json()
    assessment_id = assessment['id']
    print(f'   Assessment: id={assessment_id}, round={assessment["round"]}, status={assessment["status"]}')

    # 7. Check candidate status
    r = httpx.get(f'{BASE}/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
    print(f'7. After start: status={r.json()["status"]}')
    assert r.json()['status'] == 'ROUND2_IN_PROGRESS'

    # 8. Submit section
    r = httpx.post(f'{BASE}/api/assessment/submit-section',
                   headers={'Authorization': f'Bearer {candidate_token}'},
                   json={'assessment_id': assessment_id, 'section': 'CODING',
                         'content': {'code': 'print("hello")', 'problemId': 'r2_p1'},
                         'time_spent_seconds': 120})
    print(f'8. Submit: {r.status_code} - {r.json()}')
    assert r.status_code == 200

    # 9. Complete assessment
    r = httpx.post(f'{BASE}/api/assessment/{assessment_id}/complete',
                   headers={'Authorization': f'Bearer {candidate_token}'})
    print(f'9. Complete: {r.status_code} - status={r.json()["status"]}')
    assert r.status_code == 200
    assert r.json()['status'] == 'COMPLETED'

    # 10. Check candidate status
    r = httpx.get(f'{BASE}/api/candidates/me', headers={'Authorization': f'Bearer {candidate_token}'})
    print(f'10. After complete: status={r.json()["status"]}')
    assert r.json()['status'] == 'ROUND2_PASSED'

    print()
    print('\u2713 FULL PIPELINE PASSED!')
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)
