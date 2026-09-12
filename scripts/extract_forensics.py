import sqlite3
import json

conn = sqlite3.connect('instance/iot_security.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

run_id = 'LIVE-1789144810'

# PART 1: 10 Alerts
cursor.execute("SELECT * FROM predictions WHERE run_id = ? AND threat = 1", (run_id,))
alerts = cursor.fetchall()

cursor.execute("SELECT * FROM alerts")
alert_dict = {a['prediction_id']: a for a in cursor.fetchall()}

# PART 5: Distribution
cursor.execute("SELECT confidence FROM predictions WHERE run_id = ?", (run_id,))
all_confs = [r['confidence'] for r in cursor.fetchall()]

cursor.execute("SELECT confidence FROM predictions WHERE run_id = ? AND threat = 0", (run_id,))
benign_confs = [r['confidence'] for r in cursor.fetchall()]

alert_confs = [r['confidence'] for r in alerts]

def summarize_confs(confs):
    if not confs: return {}
    confs = sorted(confs)
    n = len(confs)
    return {
        "min": confs[0],
        "max": confs[-1],
        "mean": sum(confs)/n,
        "median": confs[n//2] if n%2!=0 else (confs[n//2-1]+confs[n//2])/2,
        "P75": confs[int(n*0.75)],
        "P90": confs[int(n*0.90)],
        "P95": confs[int(n*0.95)],
        "P99": confs[int(n*0.99)],
    }

print("--- PART 5 ---")
print("ALL:", summarize_confs(all_confs))
print("ALERTS:", summarize_confs(alert_confs))
print("BENIGN:", summarize_confs(benign_confs))
print("Alert exact confs:", sorted(alert_confs))

print("\n--- FORENSICS FOR THE 10 ALERTS ---")
shap_freq = {}
for p in alerts:
    a = alert_dict.get(p['id'])
    expl = json.loads(p['explanation'])
    print(f"\nID: {p['id']} | Time: {p['timestamp']}")
    print(f"Src: {p['source_ip']} -> Dst: {p['dest_ip']}")
    
    rf_pred = p['rf_prediction'] if 'rf_prediction' in p.keys() else 1
    if_pred = p['if_prediction'] if 'if_prediction' in p.keys() else 1
    
    print(f"RF Pred: {rf_pred} | RF Conf: {p['confidence']} | IF Pred: {if_pred} | IF Anomaly: {expl.get('if_anomaly', False)}")
    
    # SHAP
    top_features = expl.get('top_features', [])
    print("Top SHAP:")
    for f in top_features:
        name = f['feature']
        shap_freq[name] = shap_freq.get(name, 0) + 1
        print(f"  - {name}: raw={f['raw_value']}, impact={f['impact']:.4f} ({f['direction']})")
        
    print(f"Protocol: {expl.get('protocol_raw', {})}")

print("\n--- SHAP AGGREGATES ---")
for k, v in sorted(shap_freq.items(), key=lambda x: -x[1]):
    print(f"{k}: {v}/10")

conn.close()
