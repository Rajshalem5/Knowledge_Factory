#!/usr/bin/env python3
"""Create test candidate."""

import asyncio
import asyncpg
from app.config import settings
from app.core.security import hash_password

async def add_candidate():
    db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get active hiring cycle
        cycle = await conn.fetchrow('SELECT id FROM hiring_cycles WHERE status = $1 LIMIT 1', 'ACTIVE')
        if not cycle:
            print('No active hiring cycle found')
            return
            
        # Hash password
        password_hash = hash_password('Test@123')
        
        # Insert candidate directly
        await conn.execute('''
            INSERT INTO candidates (cycle_id, email, password_hash, name, college, branch, cgpa, passed_out_year, language_choice)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ''', cycle['id'], 'candidate@test.com', password_hash, 'Test Candidate', 'Test University', 'Computer Science', 8.5, 2024, 'Python')
        
        print('✅ Test candidate created:')
        print('   Email: candidate@test.com')
        print('   Password: Test@123')
        print('   College: Test University')
        print('   Branch: Computer Science')
        
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_candidate())