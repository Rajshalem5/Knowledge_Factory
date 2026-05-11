"""
Create users directly via Supabase Admin API (bypasses frontend restrictions)
"""

import asyncio
import httpx
from app.config import settings

async def create_user_admin(email: str, password: str, full_name: str, role: str):
    """Create user via Supabase Admin API"""
    
    # You need the service_role key for this (not anon key)
    # This should be in your Supabase dashboard under Settings > API
    SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY_HERE"  # Replace with actual key
    
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,  # Skip email verification
        "user_metadata": {
            "full_name": full_name,
            "role": role
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            print(f"✅ Created user: {email}")
            return response.json()
        else:
            print(f"❌ Failed to create {email}: {response.status_code} - {response.text}")
            return None

async def create_test_users():
    """Create all test users"""
    
    users = [
        ("testhr@example.com", "Password123!", "Test HR Manager", "HR"),
        ("testcandidate@example.com", "Password123!", "Test Candidate", "CANDIDATE"),
        ("testadmin@example.com", "Password123!", "Test Admin", "ADMIN"),
    ]
    
    for email, password, name, role in users:
        await create_user_admin(email, password, name, role)

if __name__ == "__main__":
    print("🔑 Creating users via Supabase Admin API...")
    print("⚠️  You need to add your SERVICE_ROLE_KEY to this script first!")
    print("📍 Find it in: Supabase Dashboard > Settings > API > service_role key")
    # asyncio.run(create_test_users())