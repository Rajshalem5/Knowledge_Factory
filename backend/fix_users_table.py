"""
Fix users table schema - make password_hash nullable
"""

import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_users_table():
    """Make password_hash column nullable in users table"""
    
    print("🔧 Fixing users table schema...")
    
    async with engine.begin() as conn:
        try:
            # Check current schema
            result = await conn.execute(text("""
                SELECT column_name, is_nullable, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_hash'
            """))
            
            row = result.fetchone()
            if row:
                print(f"📋 Current password_hash column: nullable={row.is_nullable}")
                
                if row.is_nullable == 'NO':
                    print("🔄 Making password_hash column nullable...")
                    
                    # Make password_hash nullable
                    await conn.execute(text("""
                        ALTER TABLE users 
                        ALTER COLUMN password_hash DROP NOT NULL
                    """))
                    
                    print("✅ password_hash column is now nullable")
                else:
                    print("✅ password_hash column is already nullable")
            else:
                print("❌ password_hash column not found")
                
                # Check if users table exists
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name = 'users'
                """))
                
                if result.fetchone():
                    print("📋 Users table exists but no password_hash column")
                    print("🔄 Adding nullable password_hash column...")
                    
                    await conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
                    """))
                    
                    print("✅ Added nullable password_hash column")
                else:
                    print("❌ Users table doesn't exist")
                    return
            
            # Verify the fix
            result = await conn.execute(text("""
                SELECT column_name, is_nullable, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_hash'
            """))
            
            row = result.fetchone()
            if row:
                print(f"✅ Verification: password_hash nullable={row.is_nullable}")
            
        except Exception as e:
            print(f"❌ Error fixing users table: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_users_table())