import psycopg2
from app.config import settings
import uuid
from datetime import datetime, timezone

def create_assessment():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    # Get alice@test.com
    cur.execute("SELECT id FROM candidates WHERE email = 'alice@test.com'")
    candidate_id = cur.fetchone()[0]
    
    assessment_id = str(uuid.uuid4())
    cur.execute("INSERT INTO assessments (id, candidate_id, status, started_at) VALUES (%s, %s, %s, %s)", 
                (assessment_id, candidate_id, 'IN_PROGRESS', datetime.now(timezone.utc)))
    conn.commit()
    print(f"Assessment created: {assessment_id}")
    
    # Create session
    session_id = str(uuid.uuid4())
    cur.execute("INSERT INTO proctoring_sessions (id, assessment_attempt_id, user_id, status, started_at) VALUES (%s, %s, %s, %s, %s)", 
                (session_id, assessment_id, 'test-user', 'ACTIVE', datetime.now(timezone.utc)))
    conn.commit()
    print(f"Session created: {session_id}")
    conn.close()

if __name__ == '__main__':
    create_assessment()
