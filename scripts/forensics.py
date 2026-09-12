import sqlite3
import json
import numpy as np

conn = sqlite3.connect('instance/iot_security.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

run_id = 'LIVE-1789144810'

# Get all predictions for this run
cursor.execute("SELECT * FROM predictions WHERE run_id = ?", (run_id,))
all_preds = cursor.fetchall()

# Separate alerts and benign
alert_preds = []
benign_preds = []

# Fetch alert data
cursor.execute("SELECT * FROM alerts")
all_alerts = cursor.fetchall()
alert_dict = {a['prediction_id']: a for a in all_alerts}

for p in all_preds:
    if p['threat'] == 1:
        alert_preds.append(p)
    else:
        benign_preds.append(p)

print(f"Total: {len(all_preds)}, Alerts: {len(alert_preds)}, Benign: {len(benign_preds)}")

print("\n--- PART 1 & 2: EXACT 10 THREATS AND VECTORS ---")
feature_names = ['spkts', 'dpkts', 'sbytes', 'dbytes', 'dur', 'smean', 'dmean', 'rate', 'sload', 'dload', 'proto_tcp', 'proto_udp', 'proto_icmp', 'proto_other']

shap_aggregates = {}

for p in alert_preds:
    a = alert_dict.get(p['id'])
    
    rf_pred = p['rf_prediction'] if 'rf_prediction' in p.keys() else None
    if_pred = p['if_prediction'] if 'if_prediction' in p.keys() else None
    
    expl = json.loads(p['explanation'])
    if_score = expl.get('if_score', None)
    
    # We may need to get features from the JSON or DB
    print(f"Pred ID: {p['id']}, Time: {p['timestamp']}, Src: {p['source_ip']}, Dst: {p['dest_ip']}")
    print(f"RF Conf: {p['confidence']}, IF Pred: {if_pred}, Alert ID: {a['id'] if a else None}, Sev: {a['severity'] if a else None}")
    
    if 'features' in expl:
        feat_vals = expl['features']
        print(f"Features: {feat_vals}")
    else:
        print("Features missing from DB")
        
    if 'shap_values' in expl:
        shap_vals = expl['shap_values']
        # Top 5
        sorted_shap = sorted(shap_vals.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        print(f"Top 5 SHAP: {sorted_shap}")
        for feat, val in sorted_shap:
            shap_aggregates[feat] = shap_aggregates.get(feat, 0) + 1

print("\n--- PART 3: SHAP AGGREGATES ---")
for feat, count in sorted(shap_aggregates.items(), key=lambda x: x[1], reverse=True):
    print(f"{feat}: {count}/10")

print("\n--- PART 4: DISTRIBUTIONS (Alerts vs Benign) ---")
def print_dist(name, alert_vals, benign_vals):
    print(f"{name} -> Alerts (Mean: {np.mean(alert_vals):.4f}, Max: {np.max(alert_vals):.4f}) | Benign (Mean: {np.mean(benign_vals):.4f}, Max: {np.max(benign_vals):.4f})")

alert_confs = [p['confidence'] for p in alert_preds]
benign_confs = [p['confidence'] for p in benign_preds]
print_dist('RF Confidence', alert_confs, benign_confs)

# If features are in explanation
try:
    alert_feats = np.array([json.loads(p['explanation']).get('features', [0]*14) for p in alert_preds])
    benign_feats = np.array([json.loads(p['explanation']).get('features', [0]*14) for p in benign_preds])
    
    if len(alert_feats) > 0 and len(alert_feats[0]) == 14:
        for i, fname in enumerate(feature_names):
            print_dist(fname, alert_feats[:, i], benign_feats[:, i])
except Exception as e:
    print("Could not parse features for distribution:", e)

print("\n--- PART 5: RF CONFIDENCE DISTRIBUTION ---")
all_confs = alert_confs + benign_confs
print(f"ALL: Min={np.min(all_confs):.4f}, Max={np.max(all_confs):.4f}, Mean={np.mean(all_confs):.4f}, Median={np.median(all_confs):.4f}, P75={np.percentile(all_confs, 75):.4f}, P95={np.percentile(all_confs, 95):.4f}")
print(f"ALERTS: Min={np.min(alert_confs):.4f}, Max={np.max(alert_confs):.4f}, Mean={np.mean(alert_confs):.4f}, Median={np.median(alert_confs):.4f}")
print(f"BENIGN: Min={np.min(benign_confs):.4f}, Max={np.max(benign_confs):.4f}, Mean={np.mean(benign_confs):.4f}, Median={np.median(benign_confs):.4f}")

print("\nAlert exact confs:", sorted(alert_confs))

print("\n--- PART 6: IF ANALYSIS ---")
rf_attack_if_anom = 0
rf_attack_if_norm = 0
for p in alert_preds:
    expl = json.loads(p['explanation'])
    if_anom = expl.get('if_anomaly', False)
    if if_anom:
        rf_attack_if_anom += 1
    else:
        rf_attack_if_norm += 1
print(f"RF Attack + IF Anomaly: {rf_attack_if_anom}/{len(alert_preds)}")
print(f"RF Attack + IF Normal: {rf_attack_if_norm}/{len(alert_preds)}")

conn.close()
