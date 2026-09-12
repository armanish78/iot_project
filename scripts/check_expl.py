import sqlite3
import json

conn = sqlite3.connect('instance/iot_security.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT explanation FROM predictions WHERE run_id='LIVE-1789144810' AND threat=1 LIMIT 1")
row = cursor.fetchone()
print(row['explanation'])
conn.close()
