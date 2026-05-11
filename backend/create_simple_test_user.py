#!/usr/bin/env python3
"""Create a simple test user that works with the existing database schema."""

import asyncio
import asyncpg
from app.core.security import hash_password

async def create_test_user():
    """Create a test user in the existing users table."""
    
    conn = await asyncpg.connect(
        'postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres',
        statement_cache_size=0
    )
    
    try:
        # Create a test user using the existing schema
        test_user_id = "12345678-1234-1234-1234-123456789012"
        test_email = "hr@test.com"
        test_password = "Test@123"
        
        # Insert into users table using the existing columns
        await conn.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, now(), now())
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                status = EXCLUDED.status,
                updated_at = now()
        """, test_user_id, test_email, hash_password(test_password), "HR Test User", "HR", "ACTIVE")
        
        print(f"✅ Created/updated test user:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   Role: HR")
        print()
        print("You can now login with these credentials!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())