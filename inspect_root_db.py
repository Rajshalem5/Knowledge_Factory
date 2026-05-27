import sqlite3
from pprint import pprint

def main():
    db=r'c:\\HIRING_PLATFORM\\knowledge_factory.db'
    print('DB path:', db)
    try:
        conn=sqlite3.connect(db)
        c=conn.cursor()
        tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print('tables:', tables)
        info=list(c.execute("PRAGMA table_info('candidates')").fetchall())
        print('candidates schema rows:', len(info))
        pprint(info)
        try:
            av=list(c.execute("SELECT * FROM alembic_version").fetchall())
            print('alembic_version:', av)
        except Exception as e:
            print('alembic_version error', e)
    except Exception as e:
        print('DB open error', e)

if __name__=='__main__':
    main()
