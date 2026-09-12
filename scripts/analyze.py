import sqlite3
import json

conn = sqlite3.connect('instance/iot_security.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT run_id, MAX(timestamp) FROM predictions WHERE run_id LIKE 'LIVE-%'")
latest = cursor.fetchone()
if latest and latest['run_id']:
    phone_test_run_id = latest['run_id']
    print(f'Using phone test run_id: {phone_test_run_id}')
    
    cursor.execute("SELECT * FROM predictions WHERE run_id = ? ORDER BY timestamp ASC", (phone_test_run_id,))
    run_records = cursor.fetchall()
    print(f'Total predictions in this run: {len(run_records)}')
    
    rf_attack_count = 0
    if_anomaly_count = 0
    hybrid_threat_count = 0
    
    for r in run_records:
        threat = r['threat']
        
        rf_pred = r['rf_prediction'] if 'rf_prediction' in r.keys() else None
        if_pred = r['if_prediction'] if 'if_prediction' in r.keys() else None
        
        # Determine from JSON if columns are missing
        try:
            expl = json.loads(r['explanation'])
            if 'if_anomaly' in expl and expl['if_anomaly']:
                if_anomaly_count += 1
            if rf_pred is None:
                is_rf = 'threat' in expl.get('text', '').lower()
                if is_rf: rf_attack_count += 1
        except:
            pass
            
        if rf_pred == 1: rf_attack_count += 1
        if if_pred == -1: if_anomaly_count += 1
            
        if threat == 1:
            hybrid_threat_count += 1
            
    print('---')
    print('RF Attack Count:', rf_attack_count)
    print('IF Anomaly Count:', if_anomaly_count)
    print('Hybrid Threat Count:', hybrid_threat_count)
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE prediction_id IN (SELECT id FROM predictions WHERE run_id = ?)", (phone_test_run_id,))
    run_alerts = cursor.fetchone()[0]
    print('Alerts for this run:', run_alerts)

else:
    print('No records found.')
conn.close()
