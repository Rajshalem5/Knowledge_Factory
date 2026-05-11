#!/usr/bin/env python3
"""Test authenticated endpoints."""

import requests

def test_authenticated_endpoints():
    # First login to get token
    print('🔐 Logging in as HR...')
    login_response = requests.post(
        'http://localhost:8000/api/auth/login',
        json={'email': 'hr@test.com', 'password': 'Test@123'}
    )
    
    if login_response.status_code != 200:
        print(f'❌ Login failed: {login_response.text}')
        return
    
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print('✅ Login successful')
    
    # Test candidates endpoint
    print('\n📋 Testing candidates endpoint...')
    candidates_response = requests.get(
        'http://localhost:8000/api/candidates/',
        headers=headers
    )
    
    print(f'Status: {candidates_response.status_code}')
    if candidates_response.status_code == 200:
        data = candidates_response.json()
        print(f'Full response: {data}')
        items = data.get('data', [])
        print(f'✅ Found {len(items)} candidates')
        if items:
            candidate = items[0]
            print(f'Sample: {candidate.get("name", "N/A")} - CGPA: {candidate.get("cgpa", "N/A")}')
    else:
        print(f'❌ Error: {candidates_response.text}')
    
    # Test screening stats
    print('\n📊 Testing screening stats...')
    stats_response = requests.get(
        'http://localhost:8000/api/screening/pipeline-stats',
        headers=headers
    )
    
    print(f'Status: {stats_response.status_code}')
    if stats_response.status_code == 200:
        data = stats_response.json()
        print(f'✅ Stats: {data}')
    else:
        print(f'❌ Error: {stats_response.text}')

if __name__ == "__main__":
    test_authenticated_endpoints()