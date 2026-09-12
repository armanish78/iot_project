import sqlite3, os

for db_path in ['instance/iot_security.db', 'backend/instance/iot_security.db']:
    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f'DB: {db_path}  Tables: {tables}')
        for t in tables:
            cur.execute(f'SELECT COUNT(*) FROM [{t}]')
            print(f'  {t}: {cur.fetchone()[0]} rows')
        cur.execute("SELECT * FROM sqlite_master WHERE type='table'")
        for row in cur.fetchall():
            print(row[4])
        con.close()
    else:
        print(f'NOT FOUND: {db_path}')
