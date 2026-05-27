import psycopg2
from app.config import settings

def fix_schema():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    cur.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS degree VARCHAR(50)")
    conn.commit()
    print("Column degree added")
    conn.close()

if __name__ == '__main__':
    fix_schema()
