#!/usr/bin/env python3
"""Test candidate login."""

import requests

def test_candidate_login():
    # Test candidate login
    print('Testing candidate login...')
    login_response = requests.post(
        'http://localhost:8000/api/auth/login',
        json={'email': 'candidate@test.com', 'password': 'Test@123'}
    )

    print(f'Login Status: {login_response.status_code}')
    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f'✅ Candidate Login Success: {login_data["user"]["email"]} - {login_data["user"]["role"]}')
    else:
        print(f'❌ Login Error: {login_response.text}')

if __name__ == "__main__":
    test_candidate_login()