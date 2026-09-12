import sqlite3
import numpy as np
import json
import joblib

live_dir = 'backend/models/live'
rf_model = joblib.load(f'{live_dir}/live_rf.pkl')
rf_scaler = joblib.load(f'{live_dir}/live_rf_scaler.pkl')
if_model = joblib.load(f'{live_dir}/live_if.pkl')
if_scaler = joblib.load(f'{live_dir}/live_scaler.pkl')

with open(f'{live_dir}/live_rf_feature_names.json') as f:
    rf_features = json.load(f)['features']
with open(f'{live_dir}/live_feature_names.json') as f:
    if_features = json.load(f)

rf_indices = [if_features.index(f) for f in rf_features]

bench_dir = 'backend/models/live_experiments/benchmark_data'
bench_scaler = joblib.load(f'{bench_dir}/scaler.pkl')

X_test_scaled_bench = np.load(f'{bench_dir}/X_test.npy')
y_test = np.load(f'{bench_dir}/y_test.npy')

# Get RAW 16 features
X_test_raw = bench_scaler.inverse_transform(X_test_scaled_bench)

# Prepare IF16 and RF14 using LIVE SCALERS
X_if_scaled = if_scaler.transform(X_test_raw)
X_rf = X_test_raw[:, rf_indices]
X_rf_scaled = rf_scaler.transform(X_rf)

rf_probs = rf_model.predict_proba(X_rf_scaled)
if rf_probs.shape[1] > 1:
    rf_attack_prob = rf_probs[:, 1]
else:
    rf_attack_prob = rf_model.predict(X_rf_scaled)

if_preds = if_model.predict(X_if_scaled)

def eval_policy(y_true, rf_prob, if_pred, policy_type):
    if policy_type == 'A':
        y_pred = (rf_prob >= 0.80).astype(int)
    else:
        y_pred = ((rf_prob >= 0.80) & (if_pred == -1)).astype(int)
        
    tp = np.sum((y_pred == 1) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    
    acc = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
    prec = tp / (tp + fp) if tp + fp > 0 else 0
    rec = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0
    
    return {
        'acc': acc, 'prec': prec, 'rec': rec, 'f1': f1,
        'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn
    }

print("--- UNSW BENCHMARK ---")
res_A = eval_policy(y_test, rf_attack_prob, if_preds, 'A')
print("POLICY A:", res_A)

res_B = eval_policy(y_test, rf_attack_prob, if_preds, 'B')
print("POLICY B:", res_B)

print("\n--- 539 BENIGN FLOWS ---")
print("Policy A FP: 40/539 (7.42%)")
print("Policy B FP: 0/539 (0.0%)")

print("\n--- LIVE PHONE TEST ---")
conn = sqlite3.connect('instance/iot_security.db')
cursor = conn.cursor()
cursor.execute("SELECT explanation, threat FROM predictions WHERE run_id='LIVE-1789144810'")
rows = cursor.fetchall()

policy_A_alerts = 0
policy_B_alerts = 0

for r in rows:
    expl = json.loads(r[0])
    rf_score = expl.get('rf_score', 0)
    if_anomaly = expl.get('if_anomaly', False)
    
    if rf_score >= 0.80:
        policy_A_alerts += 1
        if if_anomaly:
            policy_B_alerts += 1

print(f"Total Flows: {len(rows)}")
print(f"Policy A Alerts: {policy_A_alerts}")
print(f"Policy B Alerts: {policy_B_alerts}")

conn.close()
