import psycopg2
from app.config import settings
import uuid
from datetime import datetime, timezone

def create_session():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    # Need a valid assessment_attempt_id (FK to assessments table)
    # Get any assessment_attempt_id first
    cur.execute("SELECT id FROM assessments LIMIT 1")
    assessment_id = cur.fetchone()[0]
    
    session_id = str(uuid.uuid4())
    cur.execute("INSERT INTO proctoring_sessions (id, assessment_attempt_id, user_id, status, started_at) VALUES (%s, %s, %s, %s, %s)", 
                (session_id, assessment_id, 'test-user', 'ACTIVE', datetime.now(timezone.utc)))
    conn.commit()
    print(f"Session created: {session_id}")
    conn.close()

if __name__ == '__main__':
    create_session()
