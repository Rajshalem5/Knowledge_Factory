import psycopg2
from app.config import settings

def fix_schema():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    # Adding multiple missing columns
    columns = ['degree', 'skills', 'custom_fields', 'screening_score', 'mcq_score', 'coding_score', 'risk_penalty', 'composite_score', 'adjusted_final_score', 'recommendation', 'decision_reason', 'decision_by', 'decision_timestamp']
    for col in columns:
        try:
            # Need to specify types correctly based on model
            col_type = 'VARCHAR(50)' if col == 'degree' else 'TEXT' if col == 'skills' else 'JSON' if col == 'custom_fields' else 'NUMERIC(5,2)' if 'score' in col or 'penalty' in col else 'VARCHAR(30)' if col == 'recommendation' else 'TEXT' if col == 'decision_reason' else 'VARCHAR(36)' if col == 'decision_by' else 'TIMESTAMP'
            cur.execute(f"ALTER TABLE candidates ADD COLUMN IF NOT EXISTS {col} {col_type}")
            print(f"Column {col} added")
        except Exception as e:
            print(f"Error adding {col}: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    fix_schema()
