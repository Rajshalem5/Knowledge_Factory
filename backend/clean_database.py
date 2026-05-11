#!/usr/bin/env python3
"""
Clean Database Setup - Remove Supabase and create simple users table
"""

import asyncio
import asyncpg
from app.config import settings
from app.core.security import hash_password

async def clean_and_setup_database():
    """Drop all tables and create a clean simple schema."""
    
    # Parse DATABASE_URL to get connection params
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🧹 Cleaning database...")
        
        # Drop all tables (be careful!)
        await conn.execute("DROP SCHEMA public CASCADE;")
        await conn.execute("CREATE SCHEMA public;")
        await conn.execute("GRANT ALL ON SCHEMA public TO postgres;")
        await conn.execute("GRANT ALL ON SCHEMA public TO public;")
        
        print("✅ All tables dropped")
        
        # Create clean users table
        await conn.execute("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(30) NOT NULL DEFAULT 'CANDIDATE',
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        
        print("✅ Users table created")
        
        # Create hiring_cycles table (needed for candidate registration)
        await conn.execute("""
            CREATE TABLE hiring_cycles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        
        print("✅ Hiring cycles table created")
        
        # Create candidates table (for candidate registration)
        await conn.execute("""
            CREATE TABLE candidates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cycle_id UUID NOT NULL REFERENCES hiring_cycles(id),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name VARCHAR(255) NOT NULL,
                college VARCHAR(255),
                branch VARCHAR(255),
                cgpa DECIMAL(4,2),
                passed_out_year INTEGER,
                language_choice VARCHAR(50),
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        
        print("✅ Candidates table created")
        
        # Insert test data
        test_password_hash = hash_password("Test@123")
        
        # Insert test hiring cycle
        await conn.execute("""
            INSERT INTO hiring_cycles (name, status) 
            VALUES ('Test Cycle 2024', 'ACTIVE')
        """)
        
        # Insert test users
        await conn.execute("""
            INSERT INTO users (email, password_hash, full_name, role) VALUES
            ('hr@test.com', $1, 'HR Test User', 'HR'),
            ('admin@test.com', $1, 'Admin Test User', 'ADMIN'),
            ('interviewer@test.com', $1, 'Interviewer Test User', 'INTERVIEWER')
        """, test_password_hash)
        
        print("✅ Test users created:")
        print("  - hr@test.com / Test@123 (HR)")
        print("  - admin@test.com / Test@123 (ADMIN)")
        print("  - interviewer@test.com / Test@123 (INTERVIEWER)")
        
        print("\n🎉 Database cleaned and setup complete!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(clean_and_setup_database())