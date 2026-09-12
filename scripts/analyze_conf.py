import sqlite3
import json

conn = sqlite3.connect('instance/iot_security.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM predictions WHERE run_id = 'LIVE-1789144810'")
rows = cursor.fetchall()

high_conf = 0
med_conf = 0
hybrid_alerts = 0

for r in rows:
    conf = r['confidence']
    threat = r['threat']
    
    # In live_inference_service, confidence = rf_conf if rf_conf >= 0.80
    if threat == 1:
        hybrid_alerts += 1
        
    try:
        expl = json.loads(r['explanation'])
        if 'if_anomaly' in expl:
            is_if = expl['if_anomaly']
    except:
        pass
        
    if conf >= 0.80:
        high_conf += 1
    elif conf >= 0.50:
        med_conf += 1

print(f"Total rows: {len(rows)}")
print(f"Conf >= 0.80: {high_conf}")
print(f"Conf >= 0.50 and < 0.80: {med_conf}")
print(f"Hybrid Threats (threat=1): {hybrid_alerts}")

conn.close()
