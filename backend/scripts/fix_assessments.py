import psycopg2
from app.config import settings

conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
cur = conn.cursor()
# Fix assessment constraints
cur.execute("ALTER TABLE assessments ALTER COLUMN round SET DEFAULT 1")
conn.commit()
print("Assessments fixed")
conn.close()
