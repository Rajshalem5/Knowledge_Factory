"""Check database contents."""
import sqlite3
import sys

conn = sqlite3.connect("knowledge_factory.db")
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check each table
for table_row in tables:
    table = table_row[0]
    if table == "alembic_version":
        continue
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"\n{table}: {count} rows")
        if count > 0:
            cursor.execute(f'SELECT * FROM "{table}" LIMIT 3')
            cols = [desc[0] for desc in cursor.description]
            print(f"  Columns: {cols}")
            for row in cursor.fetchall():
                print(f"  Row: {row}")
    except Exception as e:
        print(f"{table}: error - {e}")

conn.close()
