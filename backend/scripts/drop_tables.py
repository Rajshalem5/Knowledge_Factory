import psycopg2
from app.config import settings

def drop_all_tables():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    # Drop all tables in public schema
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.commit()
    print("Tables dropped")
    conn.close()

if __name__ == '__main__':
    drop_all_tables()
