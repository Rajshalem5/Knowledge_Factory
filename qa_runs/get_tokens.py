#!/usr/bin/env python3
import urllib.request, json, os

roles = {
    'superadmin': ('superadmin@knowledgefactory.io', 'Super@12345'),
    'admin': ('admin@knowledgefactory.io', 'admin123'),
    'hr': ('hr@knowledgefactory.io', 'Hr@12345'),
    'interviewer': ('interviewer@test.com', 'Interviewer@12345'),
    'candidate': ('candidate@test.com', 'Candidate@12345'),
}

tokens_dir = '/opt/hermes_shared_memory/projects/Knowledge_Factory/auth/tokens'
os.makedirs(tokens_dir, exist_ok=True)

for role, (email, pw) in roles.items():
    try:
        data = json.dumps({'email': email, 'password': pw}).encode()
        req = urllib.request.Request('http://localhost:8000/api/auth/login', data=data,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            tok = body.get('access_token', '')
            with open(f'{tokens_dir}/{role}.json', 'w') as f:
                json.dump({'token': tok, 'email': email, 'role': role.upper()}, f)
            print(f'  OK {role}: token saved ({len(tok)} chars)')
    except urllib.error.HTTPError as e:
        print(f'  FAIL {role}: HTTP {e.code}')
    except Exception as e:
        print(f'  FAIL {role}: {e}')
