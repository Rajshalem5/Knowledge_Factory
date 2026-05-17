#!/usr/bin/env python3
"""Generate QA report and update perf baseline."""
import json
import os

run_id = "20260516_221101"
run_data = json.load(open(f'/mnt/hermes-shared/projects/Knowledge_Factory/qa_runs/{run_id}.json'))

perf_baseline = {}
try:
    with open('/opt/hermes_shared_memory/projects/Knowledge_Factory/perf_baseline.json') as f:
        perf_baseline = json.load(f)
except:
    pass

new_perf = run_data['perf']

# Update perf baseline with rolling average
updated_baseline = {}
for ep in perf_baseline:
    if ep in new_perf:
        updated_baseline[ep] = round(perf_baseline[ep] * 0.7 + new_perf[ep] * 0.3, 1)
    else:
        updated_baseline[ep] = perf_baseline[ep]
for ep in new_perf:
    if ep not in updated_baseline:
        updated_baseline[ep] = new_perf[ep]

updated_baseline = dict(sorted(updated_baseline.items()))

with open('/opt/hermes_shared_memory/projects/Knowledge_Factory/perf_baseline.json', 'w') as f:
    json.dump(updated_baseline, f, indent=2)

print("Perf baseline updated")

# Build degradation report
degradations = []
for ep, current_ms in new_perf.items():
    base_ms = perf_baseline.get(ep, 0)
    if base_ms > 0:
        ratio = current_ms / base_ms
        if ratio > 1.5:
            degradations.append({
                'endpoint': ep,
                'current_ms': round(current_ms, 1),
                'baseline_ms': base_ms,
                'ratio': round(ratio, 2),
            })

all_fast = all(v < 500 for v in new_perf.values())

report = {
    'run_id': run_id,
    'timestamp': '2026-05-16 22:11:01',
    'git_hash': 'e40ac1b',
    'summary': {
        'pass': 44,
        'fail': 7,
        'critical': 0,
        'warnings': 4,
        'pytest_passed': 200,
        'pytest_failed': 48,
        'pytest_regression': True,
        'pytest_previous_failed': 1,
    },
    'systems': {
        'backend_api': 'OK',
        'frontend_ngrok': 'OK',
        'docs': 'OK (DEBUG=True - known config warning)',
        'cors': 'FAIL - OPTIONS without auth returns 401',
        'piston': 'DOWN (404) - code execution stubs',
        'db_integrity': 'OK',
    },
    'roles': {r: True for r in ['superadmin', 'admin', 'hr', 'interviewer', 'candidate']},
    'api_tests': {
        'passed': ['login_all_roles', 'wrong_password_rejected', 'register_candidate',
                    'forgot_password_stub', 'tampered_jwt_rejected', 'no_auth_rejected',
                    'rbac_candidate_blocked_admin', 'rbac_hr_blocked_superadmin',
                    'candidates_list', 'candidates_filter', 'pagination', 'analytics_dashboard',
                    'analytics_funnel', 'hiring_cycles', 'admin_users', 'audit_logs',
                    'xss_filtered', 'sqli_prevented', 'invalid_route_404', 'invalid_data_422'],
        'failed': [
            {'test': 'CORS OPTIONS', 'issue': 'Returns 401 without auth, expected 204'},
            {'test': 'Refresh token', 'issue': 'Test sent param in body, API uses cookies'},
            {'test': 'Proctoring event', 'issue': 'Missing required assessment_id field'},
        ],
        'improved': [
            'Screening/pipeline now requires auth (was unprotected - security fix)',
            'Code execution now requires candidate role (was open to all)',
            'Status transitions reject invalid pipeline moves',
        ]
    },
    'pytest_failures_analysis': {
        'total_failed': 48,
        'by_category': [
            {'category': 'Auth/role enforcement changes', 'count': 21,
             'root_cause': 'Recent auth overhaul in commit ca3b4c6 + e40ac1b changed role checks; tests not updated'},
            {'category': 'Endpoint path mismatch', 'count': 6,
             'root_cause': 'Audit tests use /api/admin/logs (wrong), should be /api/audit/logs'},
            {'category': 'Piston unavailable', 'count': 6,
             'root_cause': 'Piston sandbox returns 404'},
            {'category': 'Test data isolation', 'count': 7,
             'root_cause': 'Session-scoped fixture accumulates data across screening tests'},
            {'category': 'Mock/unit type errors', 'count': 4,
             'root_cause': 'Analytics unit tests have type errors with mock return values'},
            {'category': 'Filter combination counts', 'count': 3,
             'root_cause': 'Assessment status filter combined with has_assessment returns unexpected counts'},
            {'category': 'Cookie-based refresh', 'count': 1,
             'root_cause': 'Refresh token test uses old body-based API'},
        ]
    },
    'perf': {
        'endpoints': new_perf,
        'baseline': perf_baseline,
        'updated_baseline': updated_baseline,
        'all_fast': all_fast,
        'all_under_30ms': all(v < 30 for v in new_perf.values()),
        'degradations': degradations,
    },
    'security': {
        'xss': 'PASS',
        'sqli': 'PASS',
        'invalid_route_json': 'PASS',
        'invalid_email_422': 'PASS',
        'nonexistent_id_404': 'PASS',
    },
    'known_issues': [
        'SENDGRID_API_KEY empty - all email flows silently fail',
        'VITE_API_URL empty - frontend may not reach backend',
        'DATABASE_URL duplicate - SQLite wins (config warning)',
        'DEBUG=true - /docs and /redoc publicly accessible',
        'Forgot-password email = TODO stub',
        'WebSocket proctoring = Phase 2 stub',
        'WebSocket dashboard = Phase 2 stub',
        'No automatic status transitions beyond R1',
        'passRatePerRound mock [75,60,45]',
        'collegeBreakdown/branchPerformance/proctoringViolations return []',
        'No assessment results view for HR',
    ],
    'config_warnings': [
        'VITE_API_URL empty - frontend cannot reach backend from browser',
        'SENDGRID_API_KEY empty - all email notifications silently fail',
        'DATABASE_URL duplicate configuration - SQLite is active',
        'DEBUG=true exposes /docs and /redoc publicly',
    ],
    'recommendations': [
        'Fix audit test paths: change /api/admin/logs to /api/audit/logs (6 tests fixed)',
        'Fix interview/selection tests: use assessment/start instead of PATCH status for pipeline transitions',
        'Fix code execution tests: use candidate token instead of admin/hr',
        'Fix refresh token test: use cookie-based approach',
        'Fix CORS: add OPTIONS handler that returns 204 without auth',
        'Fix proctoring test: include assessment_id in request body',
        'Add test data cleanup in session-scoped fixtures to prevent count drift',
        'Fix analytics unit tests: update mock expectations to match current schema',
    ]
}

report_path = f'/mnt/hermes-shared/projects/Knowledge_Factory/qa_runs/{run_id}_report.json'
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

# Update latest_summary
with open('/mnt/hermes-shared/projects/Knowledge_Factory/qa_runs/latest_summary.json', 'w') as f:
    json.dump({
        'run_id': run_id,
        'timestamp': '2026-05-16 22:11:01',
        'pass': 44,
        'fail': 7,
        'critical': 0,
        'pytest_pass': 200,
        'pytest_fail': 48,
        'all_roles_ok': True,
        'perf_all_fast': all_fast,
    }, f, indent=2)

print(f"Report saved: {report_path}")
