import sqlite3
DB=r'c:\\HIRING_PLATFORM\\knowledge_factory.db'
conn=sqlite3.connect(DB)
c=conn.cursor()
for t in ['users','candidates','hiring_cycles','assessments']:
    try:
        r=c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    except Exception as e:
        r=str(e)
    print(f"{t}: {r}")
conn.close()
