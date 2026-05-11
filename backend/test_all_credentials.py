#!/usr/bin/env python3
"""Test all user credentials."""

import requests

def test_all_credentials():
    credentials = [
        ("hr@test.com", "Test@123", "HR"),
        ("admin@test.com", "Test@123", "ADMIN"),
        ("interviewer@test.com", "Test@123", "INTERVIEWER"),
        ("candidate@test.com", "Test@123", "CANDIDATE"),
    ]
    
    print("🧪 Testing All Credentials")
    print("=" * 50)
    
    for email, password, expected_role in credentials:
        print(f"\n🔐 Testing {email}...")
        
        # Test login
        login_response = requests.post(
            'http://localhost:8000/api/auth/login',
            json={'email': email, 'password': password}
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            actual_role = login_data['user']['role']
            
            if actual_role == expected_role:
                print(f"   ✅ Login Success: {email} - {actual_role}")
                
                # Test /auth/me
                token = login_data['access_token']
                me_response = requests.get(
                    'http://localhost:8000/api/auth/me',
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if me_response.status_code == 200:
                    print(f"   ✅ /auth/me Success")
                else:
                    print(f"   ❌ /auth/me Failed: {me_response.status_code}")
            else:
                print(f"   ⚠️  Role mismatch: expected {expected_role}, got {actual_role}")
        else:
            print(f"   ❌ Login Failed: {login_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 All Credentials Summary:")
    print("   HR: hr@test.com / Test@123")
    print("   Admin: admin@test.com / Test@123") 
    print("   Interviewer: interviewer@test.com / Test@123")
    print("   Candidate: candidate@test.com / Test@123")

if __name__ == "__main__":
    test_all_credentials()