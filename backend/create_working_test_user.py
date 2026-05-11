#!/usr/bin/env python3
"""
Create a working test user for immediate login testing.
"""

import asyncio
import asyncpg
import uuid

async def create_test_user():
    """Create a test user directly in our database."""
    
    # Connect to database
    conn = await asyncpg.connect(
        'postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres',
        statement_cache_size=0  # Disable prepared statements for pgbouncer
    )
    
    try:
        # Create a test user with a known UUID
        test_user_id = "12345678-1234-1234-1234-123456789012"
        test_email = "demo@test.com"
        
        # Insert into users table
        await conn.execute("""
            INSERT INTO users (id, email, full_name, role, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, now(), now())
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                updated_at = now()
        """, test_user_id, test_email, "Demo User", "HR", "ACTIVE")
        
        print(f"✅ Created test user in database:")
        print(f"   ID: {test_user_id}")
        print(f"   Email: {test_email}")
        print(f"   Role: HR")
        print(f"   Password: demo123")
        print()
        print("Now create this user in Supabase Auth with the same ID and email.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())