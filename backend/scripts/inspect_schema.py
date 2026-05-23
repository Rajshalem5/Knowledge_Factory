import psycopg2
from app.config import settings

def inspect():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    print("Tables:", cur.fetchall())
    for table in ['candidates', 'proctoring_sessions', 'proctoring_events']:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        print(f"{table} columns:", cur.fetchall())
    conn.close()

if __name__ == '__main__':
    inspect()
