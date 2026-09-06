import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.ensemble import IsolationForest

X_train_normal = np.load('data/processed/X_train_normal.npy', allow_pickle=True).astype(np.float32)
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)
X_test_if = np.load('data/processed/X_test_if.npy', allow_pickle=True).astype(np.float32)
y_test_if = np.load('data/processed/y_test_if.npy', allow_pickle=True).astype(int)

# 5% anomalies validation set
X_val_normal = X_val[y_val == 0]
y_val_normal = y_val[y_val == 0]
X_val_attack = X_val[y_val == 1]
y_val_attack = y_val[y_val == 1]
attack_target_count = int(len(X_val_normal) * 0.05 / 0.95)

np.random.seed(42)
attack_indices = np.random.choice(len(X_val_attack), attack_target_count, replace=False)
X_val_attack_sampled = X_val_attack[attack_indices]
y_val_attack_sampled = y_val_attack[attack_indices]

X_val_if_sub = np.vstack([X_val_normal, X_val_attack_sampled])
y_val_if_sub = np.concatenate([y_val_normal, y_val_attack_sampled])

if_model = IsolationForest(contamination=0.1, n_estimators=100, random_state=42, n_jobs=-1)
if_model.fit(X_train_normal)

scores = if_model.decision_function(X_val_if_sub)
thresholds = np.linspace(np.min(scores), np.max(scores), 100)

best_f1 = 0
best_thresh = 0
for t in thresholds:
    preds = (scores < t).astype(int)
    f1 = f1_score(y_val_if_sub, preds, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1
        best_thresh = t

print(f"Optimal Threshold (All Features): {best_thresh}")
test_scores = if_model.decision_function(X_test_if)
test_preds = (test_scores < best_thresh).astype(int)

print(f"TEST METRICS (All Features):")
print(f"F1: {f1_score(y_test_if, test_preds):.4f}")
print(f"Precision: {precision_score(y_test_if, test_preds):.4f}")
print(f"Recall: {recall_score(y_test_if, test_preds):.4f}")
