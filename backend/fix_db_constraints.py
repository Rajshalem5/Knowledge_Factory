import psycopg2

DSN = "postgresql://postgres.nwlfflecgukgfgdcyihk:fRld9eJsOZ6WME0x@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

FIX_SQL = """
-- Update users table role constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check 
    CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'HR', 'INTERVIEWER', 'CANDIDATE'));

-- Update users table status constraint (just in case)
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_status_check;
ALTER TABLE users ADD CONSTRAINT users_status_check 
    CHECK (status IN ('ACTIVE', 'INACTIVE', 'PENDING'));
"""

def run():
    print("Connecting to Supabase to fix constraints...")
    try:
        conn = psycopg2.connect(DSN)
        conn.autocommit = True
        cur = conn.cursor()

        print("Applying constraint fixes...")
        cur.execute(FIX_SQL)
        print("[OK] Constraints updated successfully!")

        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to update constraints: {e}")

if __name__ == "__main__":
    run()
