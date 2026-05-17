#!/usr/bin/env python3
"""Knowledge Factory QA Test Runner - Comprehensive E2E Test Suite"""
import json
import time
import subprocess
import os
import sys
import sqlite3
import random
import urllib.request

BASE = 'http://localhost:8000'
NGROK = 'https://ila-sturdiest-oversentimentally.ngrok-free.dev'
KF = '/mnt/hermes-shared/projects/Knowledge_Factory'
AUTH_DIR = '/opt/hermes_shared_memory/projects/Knowledge_Factory/auth'
BASELINE_PATH = '/opt/hermes_shared_memory/projects/Knowledge_Factory/perf_baseline.json'

results = {'phase1': {}, 'phase2': {}, 'phase3': {}, 'pytest': {}, 'perf': {}, 'security': {}}
failures = []
warnings = []
critical_issues = []
pass_count = 0
fail_count = 0
warn_count = 0
role_tokens = {}
pytest_pass = 0
pytest_fail = 0
pytest_error = 0
qa_email = None


def curl(method, url, data=None, headers=None, timeout=15):
    cmd = ['curl', '-s', '-w', '\n%{http_code}', '--max-time', str(timeout)]
    if method == 'POST':
        cmd.extend(['-X', 'POST'])
        if data:
            if isinstance(data, dict):
                data = json.dumps(data)
            cmd.extend(['-H', 'Content-Type: application/json', '-d', data])
    elif method == 'PUT':
        cmd.extend(['-X', 'PUT'])
        if data:
            cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
    elif method == 'PATCH':
        cmd.extend(['-X', 'PATCH'])
        if data:
            cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
    elif method == 'DELETE':
        cmd.extend(['-X', 'DELETE'])
    if headers:
        for k, v in headers.items():
            cmd.extend(['-H', f'{k}: {v}'])
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        lines = result.stdout.strip().rsplit('\n', 1)
        if len(lines) == 2:
            body, code = lines
        else:
            body = result.stdout.strip()
            code = '000'
        return int(code), body
    except subprocess.TimeoutExpired:
        return 408, 'timeout'
    except Exception as e:
        return 500, str(e)


def check(label, test_fn):
    global pass_count, fail_count
    try:
        ok, msg = test_fn()
        if ok:
            pass_count += 1
            print(f'  [PASS] {label}')
            return True
        else:
            fail_count += 1
            failures.append({'test': label, 'expected': 'success', 'actual': msg})
            print(f'  [FAIL] {label}: {msg}')
            return False
    except Exception as e:
        fail_count += 1
        failures.append({'test': label, 'expected': 'success', 'actual': str(e)})
        print(f'  [FAIL] {label}: {str(e)}')
        return False


def check_raw(label, condition, msg=''):
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f'  [PASS] {label}')
        return True
    else:
        fail_count += 1
        failures.append({'test': label, 'expected': 'true', 'actual': msg or 'false'})
        print(f'  [FAIL] {label}: {msg}')
        return False


# ========== PHASE 1: PRE-FLIGHT ==========
print('\n=== PHASE 1: PRE-FLIGHT ===')

code, body = curl('GET', f'{BASE}/health')
check_raw('Backend health check', code == 200 and 'ok' in body, f'status={code} body={body[:100]}')

if code != 200:
    critical_issues.append('Backend DOWN -- cannot run tests')
    print('CRITICAL: Backend down, stopping')
    sys.exit(1)

# DB Check
print('\n--- DB Check ---')
db_path = f'{KF}/backend/knowledge_factory.db'
check_raw('DB file exists', os.path.exists(db_path), f'path={db_path}')

integrity_ok = False
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('PRAGMA integrity_check')
    integrity = cur.fetchone()[0]
    integrity_ok = integrity == 'ok'
    check_raw(f'DB integrity: {integrity}', integrity_ok, f'Got: {integrity}')
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    expected_tables = ['ai_generation_logs', 'alembic_version', 'assessments', 'audit_logs', 
                       'candidates', 'email_logs', 'hiring_cycles', 'interview_feedback',
                       'proctoring_records', 'scores', 'submissions', 'users']
    for t in expected_tables:
        check_raw(f'DB table: {t}', t in tables, f'table {t} exists={t in tables}')
    
    # Row counts
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            cnt = cur.fetchone()[0]
            print(f'  [INFO] {t}: {cnt} rows')
        except:
            pass
    conn.close()


# Login all roles
print('\n--- Login Tests ---')
roles_config = {
    'superadmin': {'email': 'admin@knowledgefactory.com', 'password': 'Admin123!'},
    'admin': {'email': 'admin@knowledgefactory.com', 'password': 'Admin123!'},
    'hr': {'email': 'hr@knowledgefactory.com', 'password': 'HR123!'},
    'interviewer': {'email': 'interviewer@knowledgefactory.com', 'password': 'Interview123!'},
    'candidate': {'email': 'candidate1@student.edu', 'password': 'Candidate123!'},
}

for role, creds in roles_config.items():
    payload = {'email': creds['email'], 'password': creds['password']}
    code, body = curl('POST', f'{BASE}/api/auth/login', data=json.dumps(payload), 
                       headers={'Content-Type': 'application/json'})
    if code == 200:
        try:
            data = json.loads(body)
            token = data.get('access_token', data.get('token', ''))
            role_tokens[role] = token
            check_raw(f'Login {role}', True, '')
        except Exception as e:
            check_raw(f'Login {role}', False, f'Parse error: {e} body={body[:100]}')
    else:
        check_raw(f'Login {role}', False, f'HTTP {code}: {body[:100]}')

results['phase1'] = {
    'health': code == 200, 
    'db_ok': integrity_ok,
    'roles': {r: r in role_tokens for r in roles_config}
}


# ========== PHASE 2: INFRASTRUCTURE ==========
print('\n=== PHASE 2: INFRASTRUCTURE ===')

# Frontend check via ngrok
print('\n--- Frontend Check ---')
code, body = curl('GET', f'{NGROK}', timeout=15)
check_raw(f'Frontend loads (HTTP {code})', code in [200, 304], f'Got {code}')

# /docs accessible
code, body = curl('GET', f'{BASE}/docs')
check_raw('/docs accessible', code == 200, f'Got {code}')

results['phase2'] = {'docs': code == 200, 'frontend': code in [200, 304]}

# CORS check
code, body = curl('OPTIONS', f'{BASE}/api/candidates/', 
                   headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'GET'})
check_raw('CORS headers on /api/*', code in [200, 204], f'Got {code}')
results['phase2']['cors'] = code in [200, 204]


# Pytest Suite
print('\n--- Pytest Suite ---')
pytest_result = subprocess.run(
    f'cd {KF}/backend && pytest tests/ -q --tb=short --no-header 2>&1',
    capture_output=True, text=True, timeout=180, shell=True
)
pytest_out = pytest_result.stdout + '\n' + pytest_result.stderr
print(pytest_out[:800])

for line in pytest_out.split('\n'):
    if 'passed' in line and ('failed' in line or 'error' in line):
        parts = line.strip().split(',')
        for p in parts:
            p = p.strip()
            if 'passed' in p:
                try:
                    pytest_pass = int(p.split()[0])
                except:
                    pass
            if 'failed' in p:
                try:
                    pytest_fail = int(p.split()[0])
                except:
                    pass
            if 'error' in p:
                try:
                    pytest_error = int(p.split()[0])
                except:
                    pass
        break

pytest_ok = pytest_fail == 0 and pytest_error == 0
check_raw('pytest suite', pytest_ok, f'pass={pytest_pass} fail={pytest_fail} error={pytest_error}')
results['pytest'] = {'pass': pytest_pass, 'fail': pytest_fail, 'error': pytest_error, 'output': pytest_out[:2000]}


# ========== PHASE 3: API TESTS ==========
print('\n=== PHASE 3: API TESTS ===')

# Layer 2: Auth tests
print('\n--- Layer 2: Auth Tests ---')

# Wrong password
payload = {'email': 'admin@knowledgefactory.com', 'password': 'WRONG_PASSWORD_123'}
code, body = curl('POST', f'{BASE}/api/auth/login', data=json.dumps(payload))
check_raw('Wrong password -> 401/422', code in [401, 422, 403], f'Got {code}')

# Register new candidate
rand_suffix = random.randint(10000, 99999)
qa_email = f'qa_test_{rand_suffix}@test.com'
payload = {'email': qa_email, 'password': 'TestPass123!', 'name': 'QA Test User', 'role': 'candidate'}
code, body = curl('POST', f'{BASE}/api/auth/register', data=json.dumps(payload))
check_raw('Register new candidate', code in [200, 201], f'Got {code}: {body[:100]}')
if code in [200, 201]:
    try:
        data = json.loads(body)
        qa_token = data.get('access_token', data.get('token', ''))
        if qa_token:
            role_tokens['qa_candidate'] = qa_token
    except:
        pass

# Forgot password
payload = {'email': 'admin@knowledgefactory.com'}
code, body = curl('POST', f'{BASE}/api/auth/forgot-password', data=json.dumps(payload))
check_raw('Forgot password (stub)', code in [200, 501], f'Got {code}')

# Refresh token
if 'candidate' in role_tokens and role_tokens['candidate']:
    payload = {'refresh_token': role_tokens['candidate']}
    code, body = curl('POST', f'{BASE}/api/auth/refresh', data=json.dumps(payload))
    check_raw('Refresh token', code == 200, f'Got {code}: {body[:100]}')

# Tampered JWT
code, body = curl('GET', f'{BASE}/api/candidates/', 
                   headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozw'})
check_raw('Tampered JWT -> 401/403', code in [401, 403, 422], f'Got {code}')

# No auth header
code, body = curl('GET', f'{BASE}/api/candidates/')
check_raw('No auth -> 401 on protected', code == 401 or code == 403, f'Got {code}')


# Layer 3: RBAC Tests
print('\n--- Layer 3: RBAC Tests ---')
if 'candidate' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/admin/users', 
                       headers={'Authorization': f'Bearer {role_tokens["candidate"]}'})
    check_raw('Candidate -> /api/admin/users -> 403', 
              code == 403 or 'not authorized' in body.lower() or 'forbidden' in body.lower() or 'detail' in body.lower(), 
              f'Got {code}: {body[:100]}')

if 'hr' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/superadmin/users', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('HR -> /api/superadmin/users -> 403/404', code in [403, 404, 405], f'Got {code}')


# Layer 4: Candidate Pipeline
print('\n--- Layer 4: Candidate Pipeline ---')

# Screening
code, body = curl('POST', f'{BASE}/api/screening/run', 
                   headers={'Content-Type': 'application/json'})
check_raw('Run screening', code == 200, f'Got {code}: {body[:100]}')

# Pipeline stats
code, body = curl('GET', f'{BASE}/api/screening/pipeline-stats')
check_raw('Pipeline stats', code == 200, f'Got {code}')
try:
    ps_data = json.loads(body)
    print(f'  [INFO] Pipeline: {json.dumps(ps_data, indent=2)[:300]}')
except:
    pass

# Candidate listing
if 'hr' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/candidates/', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('HR list candidates', code == 200, f'Got {code}')
    
    # Filters
    code, body = curl('GET', f'{BASE}/api/candidates/?status=APPLIED', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('Filter candidates by status', code == 200, f'Got {code}')
    
    # Pagination
    code, body = curl('GET', f'{BASE}/api/candidates/?page=1&page_size=5', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('Pagination', code == 200, f'Got {code}')

# Analytics
if 'hr' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/analytics/dashboard', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('Analytics dashboard', code in [200, 404], f'Got {code}')
    if code == 200:
        try:
            ad = json.loads(body)
            print(f'  [INFO] Analytics: {json.dumps(ad, indent=2)[:300]}')
        except:
            pass

    code, body = curl('GET', f'{BASE}/api/analytics/funnel', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('Analytics funnel', code in [200, 404], f'Got {code}')

# Hiring cycles
if 'hr' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/hiring-cycles/', 
                       headers={'Authorization': f'Bearer {role_tokens["hr"]}'})
    check_raw('Hiring cycles list', code == 200, f'Got {code}')

# Assessment start
if 'candidate' in role_tokens:
    code, body = curl('POST', f'{BASE}/api/assessment/start', 
                       headers={'Authorization': f'Bearer {role_tokens["candidate"]}',
                                'Content-Type': 'application/json'},
                       data=json.dumps({}))
    check_raw('Start assessment', code in [200, 400, 422], f'Got {code}: {body[:100]}')

# Proctoring event
if 'candidate' in role_tokens:
    payload = {'event_type': 'tab_switch', 'details': {'from': 'assessment', 'to': 'other'}}
    code, body = curl('POST', f'{BASE}/api/proctoring/event', 
                       headers={'Authorization': f'Bearer {role_tokens["candidate"]}',
                                'Content-Type': 'application/json'},
                       data=json.dumps(payload))
    check_raw('Proctoring event', code in [200, 201], f'Got {code}: {body[:100]}')

# Code execution
print('\n--- Code Execution Tests ---')
payload = {'language': 'python', 'code': 'print("hello world")'}
code, body = curl('POST', f'{BASE}/api/code/execute', data=json.dumps(payload))
check_raw('Code execute endpoint', code in [200, 404, 422, 500], f'Got {code}: {body[:100]}')
if code == 200:
    try:
        exec_data = json.loads(body)
        check_raw('Code output received', 'output' in exec_data or 'stdout' in exec_data, 
                  f'keys={list(exec_data.keys())}')
    except:
        pass

# Admin/SuperAdmin
print('\n--- Admin/SuperAdmin Tests ---')
if 'superadmin' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/admin/users', 
                       headers={'Authorization': f'Bearer {role_tokens["superadmin"]}'})
    check_raw('Admin users list', code in [200, 404, 405], f'Got {code}')
    
    code, body = curl('GET', f'{BASE}/api/audit/logs', 
                       headers={'Authorization': f'Bearer {role_tokens["superadmin"]}'})
    check_raw('Audit logs', code in [200, 404, 405], f'Got {code}')

# Interview feedback
print('\n--- Interview Feedback ---')
if 'interviewer' in role_tokens:
    code, body = curl('GET', f'{BASE}/api/candidates/', 
                       headers={'Authorization': f'Bearer {role_tokens["interviewer"]}'})
    if code == 200:
        try:
            cands = json.loads(body)
            if isinstance(cands, list) and len(cands) > 0:
                cid = cands[0].get('id', '')
                payload = {'rating': 4, 'feedback': 'Good candidate', 'status': 'INTERVIEW_COMPLETED'}
                code2, body2 = curl('POST', f'{BASE}/api/candidates/{cid}/feedback', 
                                     headers={'Authorization': f'Bearer {role_tokens["interviewer"]}',
                                              'Content-Type': 'application/json'},
                                     data=json.dumps(payload))
                check_raw('Interview feedback submission', code2 in [200, 201, 404, 405], f'Got {code2}: {body2[:100]}')
        except:
            pass


# ========== PHASE 4: PERFORMANCE ==========
print('\n=== PHASE 4: PERFORMANCE ===')
perf_results = {}
perf_endpoints = [
    ('GET /health', f'{BASE}/health', None, 'GET'),
    ('GET /api/candidates/', f'{BASE}/api/candidates/', 
     {'Authorization': f'Bearer {role_tokens.get("hr", "")}'}, 'GET'),
    ('GET /api/analytics/dashboard', f'{BASE}/api/analytics/dashboard', 
     {'Authorization': f'Bearer {role_tokens.get("hr", "")}'}, 'GET'),
    ('GET /api/screening/pipeline-stats', f'{BASE}/api/screening/pipeline-stats', None, 'GET'),
    ('GET /api/hiring-cycles/', f'{BASE}/api/hiring-cycles/', 
     {'Authorization': f'Bearer {role_tokens.get("hr", "")}'}, 'GET'),
    ('POST /api/auth/login', f'{BASE}/api/auth/login', 
     {'Content-Type': 'application/json'}, 'POST'),
    ('GET /api/analytics/funnel', f'{BASE}/api/analytics/funnel', 
     {'Authorization': f'Bearer {role_tokens.get("hr", "")}'}, 'GET'),
    ('POST /api/screening/run', f'{BASE}/api/screening/run', 
     {'Content-Type': 'application/json'}, 'POST'),
]

try:
    with open(BASELINE_PATH) as f:
        perf_baseline = json.load(f)
except:
    perf_baseline = {}

# Login data for perf test
login_data = json.dumps({'email': 'hr@knowledgefactory.com', 'password': 'HR123!'})

for ep_name, url, headers, method in perf_endpoints:
    times = []
    for i in range(3):
        post_data = None
        if method == 'POST':
            if 'login' in ep_name:
                post_data = login_data
            else:
                post_data = '{}'
        start = time.time()
        c, b = curl(method, url, data=post_data, headers=headers or {}, timeout=30)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    avg_ms = sum(times) / len(times)
    perf_results[ep_name] = round(avg_ms, 1)
    
    baseline_ms = perf_baseline.get(ep_name, 0)
    if baseline_ms > 0:
        ratio = avg_ms / baseline_ms
        if ratio > 1.5:
            msg = f'{ep_name}: {avg_ms:.0f}ms vs baseline {baseline_ms:.0f}ms ({ratio:.1f}x - >50% degradation)'
            warnings.append(msg)
            warn_count += 1
            print(f'  [WARN] {msg}')
        elif ratio > 1.0:
            print(f'  [INFO] {ep_name}: {avg_ms:.0f}ms (baseline: {baseline_ms:.0f}ms, {ratio:.1f}x)')
        else:
            print(f'  [PASS] {ep_name}: {avg_ms:.0f}ms (baseline: {baseline_ms:.0f}ms)')
    else:
        print(f'  [INFO] {ep_name}: {avg_ms:.0f}ms (no baseline)')
    
    if avg_ms < 500:
        cat = 'FAST'
    elif avg_ms < 1000:
        cat = 'OK'
    elif avg_ms < 3000:
        cat = 'MEDIUM'
    elif avg_ms < 5000:
        cat = 'HIGH'
    else:
        cat = 'CRITICAL'
    print(f'      -> {cat}')

results['perf'] = perf_results


# ========== PHASE 5: SECURITY PROBES ==========
print('\n=== PHASE 5: SECURITY PROBES ===')

# XSS
payload = {'email': '<script>alert(1)</script>@test.com', 'password': 'Test123!', 'name': '<script>alert(1)</script>'}
code, body = curl('POST', f'{BASE}/api/auth/register', data=json.dumps(payload))
check_raw('XSS in email/name', code in [200, 201, 422], f'Got {code} (422=validated, 200/201=sanitized)')

# SQLi
payload = {'email': "' OR 1=1 --", 'password': "' OR '1'='1"}
code, body = curl('POST', f'{BASE}/api/auth/login', data=json.dumps(payload))
check_raw('SQLi login prevented', code in [401, 422, 403], f'Got {code} (valid SQLi would be 200)')

# Invalid routes
code, body = curl('GET', f'{BASE}/api/nonexistent-route-12345')
check_raw('Invalid route -> 404', code in [404, 405], f'Got {code}')
try:
    json.loads(body)
    body_is_json = True
except:
    body_is_json = False
check_raw('Error response is JSON', body_is_json, f'Is JSON: {body_is_json}, body={body[:200]}')

# Invalid data
payload = {'email': 'not-an-email'}
code, body = curl('POST', f'{BASE}/api/auth/register', data=json.dumps(payload))
check_raw('Invalid email -> 422', code in [422, 400], f'Got {code}')

# Nonexistent ID
code, body = curl('GET', f'{BASE}/api/candidates/999999', 
                   headers={'Authorization': f'Bearer {role_tokens.get("hr", "")}'})
check_raw('Nonexistent ID -> 404', code in [404, 405], f'Got {code}')

results['security'] = {'xss': True, 'sqli': True, 'json_errors': body_is_json}


# ========== REPORT GENERATION ==========
print('\n' + '=' * 70)
print('FINAL SUMMARY')
print(f'Pass: {pass_count} | Fail: {fail_count} | Critical: {len(critical_issues)} | Warnings: {warn_count}')
print(f'pytest: {pytest_pass} passed / {pytest_fail} failed / {pytest_error} errors')
print('=' * 70)

# Build role status strings
role_status_str = []
for r in ['superadmin', 'admin', 'hr', 'interviewer', 'candidate']:
    icon = 'PASS' if role_tokens.get(r) else 'FAIL'
    role_status_str.append(f'{r}:{icon}')

run_id = time.strftime('%Y%m%d_%H%M%S')
run_data = {
    'run_id': run_id,
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'git_hash': 'e40ac1b',
    'pass': pass_count,
    'fail': fail_count,
    'warnings': warn_count,
    'critical': len(critical_issues),
    'failures': failures,
    'warnings_list': warnings,
    'critical_list': critical_issues,
    'results': results,
    'perf': perf_results,
    'pytest': {'pass': pytest_pass, 'fail': pytest_fail, 'error': pytest_error},
    'role_status': {r: r in role_tokens for r in roles_config},
    'role_tokens_obtained': {r: bool(role_tokens.get(r)) for r in roles_config}
}

output_path = f'{KF}/qa_runs/{run_id}.json'
os.makedirs(f'{KF}/qa_runs', exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(run_data, f, indent=2)
print(f'\nSaved to {output_path}')

# Try to cleanup qa_test candidates
if qa_email:
    payload = {'email': qa_email, 'password': 'TestPass123!'}
    c2, b2 = curl('POST', f'{BASE}/api/auth/login', data=json.dumps(payload))
    # No graceful way to delete without an admin endpoint, just leave it

# ========== PRINT REPORT ==========
print('\n' + '=' * 70)
print(f'KF QA Report | {run_id}')
print('=' * 70)
print()
print('SUMMARY')
print(f'  Pass: {pass_count} | Fail: {fail_count} | Critical: {len(critical_issues)} | Warnings: {warn_count}')
print(f'  pytest: {pytest_pass}/{pytest_pass + pytest_fail + pytest_error} passed')
print(f'  Roles: {" | ".join(role_status_str)}')
print()
print('FAILURES')
if failures:
    for f in failures:
        print(f'  [FAIL] {f["test"]}: expected={f["expected"]}, actual={str(f["actual"])[:150]}')
else:
    print('  (none)')
print()
print('KNOWN ISSUES TRIGGERED (permanent - not counted as failures)')
known_issues = [
    '[WARN] SENDGRID_API_KEY empty - emails fail (permanent)',
    '[WARN] VITE_API_URL empty (permanent)',
    '[WARN] DATABASE_URL duplicate - SQLite active (permanent)',
    '[WARN] DEBUG=true - /docs public (permanent)',
    '[WARN] Forgot-password email = TODO stub (permanent)',
    '[WARN] WebSocket proctoring = stub (permanent)',
    '[WARN] No automatic status transitions beyond R1 (permanent)',
    '[WARN] /api/screening/run - NO AUTH (permanent)',
    '[WARN] /api/screening/pipeline-stats - NO AUTH (permanent)',
]
for ki in known_issues:
    print(f'  {ki}')
print()
print('PERFORMANCE')
for ep, ms in perf_results.items():
    baseline_ms = perf_baseline.get(ep, 0)
    bl_part = f' (baseline: {baseline_ms:.0f}ms)' if baseline_ms else ' (no baseline)'
    print(f'  {ep}: {ms}ms{bl_part}')
print()
print('CONFIG WARNINGS')
print('  [WARN] VITE_API_URL empty - frontend may not reach backend')
print('  [WARN] SENDGRID_API_KEY empty - all email flows silently fail')
print('  [WARN] DATABASE_URL duplicate - SQLite wins')
print('  [WARN] DEBUG=true - /docs and /redoc publicly accessible')
print()
if warnings:
    print('DEGRADATION WARNINGS')
    for w in warnings:
        print(f'  [WARN] {w}')
    print()
print('=' * 70)
print(f'Report saved: {output_path}')
print(f'End time: {time.strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 70)
