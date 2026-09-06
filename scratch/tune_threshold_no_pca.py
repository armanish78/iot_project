import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.ensemble import IsolationForest

X_train_normal = np.load('data/processed/X_train_normal.npy', allow_pickle=True).astype(np.float32)
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

import json
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']

# Validation 5% sub
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

X_train_normal_if = X_train_normal[:, top_indices]
X_val_if_selected = X_val_if_sub[:, top_indices]

if_model = IsolationForest(contamination=0.1, n_estimators=200, random_state=42, n_jobs=-1)
if_model.fit(X_train_normal_if)

scores = if_model.decision_function(X_val_if_selected)
thresholds = np.linspace(np.min(scores), np.max(scores), 200)

best_f1 = 0
best_thresh = 0
for t in thresholds:
    preds = (scores < t).astype(int)
    f1 = f1_score(y_val_if_sub, preds, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1
        best_thresh = t

print(f"Optimal Threshold (No PCA): {best_thresh}")
preds = (scores < best_thresh).astype(int)
print(f"Validation F1: {f1_score(y_val_if_sub, preds):.4f}")
print(f"Precision: {precision_score(y_val_if_sub, preds):.4f}")
print(f"Recall: {recall_score(y_val_if_sub, preds):.4f}")

# Test
X_test_if = np.load('data/processed/X_test_if.npy', allow_pickle=True).astype(np.float32)
y_test_if = np.load('data/processed/y_test_if.npy', allow_pickle=True).astype(int)
X_test_if_selected = X_test_if[:, top_indices]

test_scores = if_model.decision_function(X_test_if_selected)
test_preds = (test_scores < best_thresh).astype(int)

print(f"\nTEST METRICS:")
print(f"F1: {f1_score(y_test_if, test_preds):.4f}")
print(f"Precision: {precision_score(y_test_if, test_preds):.4f}")
print(f"Recall: {recall_score(y_test_if, test_preds):.4f}")
print(f"Confusion Matrix: {confusion_matrix(y_test_if, test_preds).tolist()}")

