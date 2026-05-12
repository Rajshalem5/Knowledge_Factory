import sqlite3
import sys

conn = sqlite3.connect('knowledge_factory.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print('Tables:', tables)
for t in tables:
    cnt = conn.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
    print(f'  {t[0]}: {cnt} rows')
conn.close()
