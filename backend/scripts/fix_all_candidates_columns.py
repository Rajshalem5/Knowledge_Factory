import psycopg2
from app.config import settings

def fix_all_columns():
    conn = psycopg2.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    cur = conn.cursor()
    
    # Expected columns based on Candidate model
    expected_columns = {
        'id': 'VARCHAR(36)',
        'cycle_id': 'VARCHAR(36)',
        'email': 'VARCHAR(255)',
        'phone': 'VARCHAR(20)',
        'password_hash': 'VARCHAR(255)',
        'name': 'VARCHAR(255)',
        'college': 'VARCHAR(255)',
        'branch': 'VARCHAR(50)',
        'degree': 'VARCHAR(50)',
        'skills': 'TEXT',
        'cgpa': 'NUMERIC(4,2)',
        'passed_out_year': 'INTEGER',
        'resume_url': 'VARCHAR(500)',
        'govt_id_url': 'VARCHAR(500)',
        'language_choice': 'VARCHAR(30)',
        'status': 'VARCHAR(30)',
        'email_verified': 'BOOLEAN',
        'custom_fields': 'JSON',
        'created_at': 'TIMESTAMP',
        'updated_at': 'TIMESTAMP',
        'screening_score': 'NUMERIC(5,2)',
        'mcq_score': 'NUMERIC(5,2)',
        'coding_score': 'NUMERIC(5,2)',
        'risk_penalty': 'NUMERIC(5,2)',
        'composite_score': 'NUMERIC(5,2)',
        'adjusted_final_score': 'NUMERIC(5,2)',
        'recommendation': 'VARCHAR(30)',
        'decision_reason': 'TEXT',
        'decision_by': 'VARCHAR(36)',
        'decision_timestamp': 'TIMESTAMP'
    }
    
    # Check existing columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'candidates'")
    existing_columns = {row[0] for row in cur.fetchall()}
    
    for col, col_type in expected_columns.items():
        if col not in existing_columns:
            try:
                cur.execute(f"ALTER TABLE candidates ADD COLUMN {col} {col_type}")
                print(f"Column {col} added")
            except Exception as e:
                print(f"Error adding {col}: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    fix_all_columns()
