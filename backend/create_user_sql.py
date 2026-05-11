"""
Create test users directly in database (for development only)
"""

import asyncio
import uuid
from sqlalchemy import text
from app.database import engine

async def create_test_users_sql():
    """Create users directly in the users table"""
    
    print("🔄 Creating test users directly in database...")
    
    users = [
        {
            "id": str(uuid.uuid4()),
            "email": "quicktest.hr@example.com",
            "full_name": "Quick Test HR",
            "role": "HR",
            "status": "ACTIVE"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "quicktest.candidate@example.com", 
            "full_name": "Quick Test Candidate",
            "role": "CANDIDATE",
            "status": "ACTIVE"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "quicktest.admin@example.com",
            "full_name": "Quick Test Admin", 
            "role": "ADMIN",
            "status": "ACTIVE"
        }
    ]
    
    async with engine.begin() as conn:
        for user in users:
            try:
                await conn.execute(
                    text("""
                        INSERT INTO users (id, email, full_name, role, status, created_at, updated_at)
                        VALUES (:id, :email, :full_name, :role, :status, NOW(), NOW())
                        ON CONFLICT (email) DO NOTHING
                    """),
                    user
                )
                print(f"✅ Created user: {user['email']} ({user['role']})")
            except Exception as e:
                print(f"❌ Failed to create {user['email']}: {e}")
    
    print("\n🔑 Test these credentials:")
    print("Email: quicktest.hr@example.com | Role: HR")
    print("Email: quicktest.candidate@example.com | Role: CANDIDATE") 
    print("Email: quicktest.admin@example.com | Role: ADMIN")
    print("\n⚠️  Note: These users won't have Supabase auth passwords.")
    print("You'll need to create auth entries separately or use existing accounts.")

if __name__ == "__main__":
    asyncio.run(create_test_users_sql())