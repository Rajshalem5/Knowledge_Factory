#!/usr/bin/env python3
"""Final authentication test."""

import requests

def test_final_auth():
    print("🎯 Final Authentication Test")
    print("=" * 50)
    
    # Test all credentials
    credentials = [
        ("hr@test.com", "Test@123", "HR"),
        ("candidate@test.com", "Test@123", "CANDIDATE"),
    ]
    
    for email, password, expected_role in credentials:
        print(f"\n🔐 Testing {email}...")
        
        # Test login
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'email': email, 'password': password},
            headers={
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:5173'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login Success: {data['user']['role']}")
            
            # Test /auth/me
            token = data['access_token']
            me_response = requests.get(
                'http://localhost:8000/api/auth/me',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if me_response.status_code == 200:
                print(f"   ✅ /auth/me Success")
            else:
                print(f"   ❌ /auth/me Failed: {me_response.status_code}")
        else:
            print(f"   ❌ Login Failed: {response.status_code} - {response.text}")
    
    print(f"\n🌐 Frontend should now work at: http://localhost:5173")
    print(f"🔧 Backend API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    test_final_auth()