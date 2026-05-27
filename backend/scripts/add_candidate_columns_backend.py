import sqlite3

DB=r'c:\\HIRING_PLATFORM\\backend\\knowledge_factory.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()

existing=[r[1] for r in cur.execute("PRAGMA table_info('candidates')").fetchall()]
print('existing columns:', existing)

columns=[
    ("screening_score","NUMERIC(5,2)","0.0"),
    ("mcq_score","NUMERIC(5,2)","0.0"),
    ("coding_score","NUMERIC(5,2)","0.0"),
    ("risk_penalty","NUMERIC(5,2)","0.0"),
    ("composite_score","NUMERIC(5,2)","0.0"),
    ("adjusted_final_score","NUMERIC(5,2)","0.0"),
    ("recommendation","VARCHAR(30)",None),
    ("decision_reason","TEXT",None),
    ("decision_by","VARCHAR(36)",None),
    ("decision_timestamp","DATETIME",None),
]

for name,ctype,default in columns:
    if name in existing:
        print('skip', name)
        continue
    ddl=f"ALTER TABLE candidates ADD COLUMN {name} {ctype}"
    if default is not None:
        ddl += f" DEFAULT {default}"
    print('exec:', ddl)
    cur.execute(ddl)
    conn.commit()

# ensure alembic_version points to head
try:
    cur.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
    cur.execute("DELETE FROM alembic_version")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES (?)", ("7a9b8c6d5e4f",))
    conn.commit()
    print('alembic_version set to 7a9b8c6d5e4f')
except Exception as e:
    print('alembic_version error', e)

print('done')
conn.close()
