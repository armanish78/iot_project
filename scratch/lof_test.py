import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.neighbors import LocalOutlierFactor
import json

# Load Data
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

# Load Top 15 features
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']

# Validation subset to 5% anomalies
X_val_normal = X_val[y_val == 0]
y_val_normal = y_val[y_val == 0]
X_val_attack = X_val[y_val == 1]
y_val_attack = y_val[y_val == 1]
attack_target_count = int(len(X_val_normal) * 0.05 / 0.95)

np.random.seed(42)
attack_indices = np.random.choice(len(X_val_attack), attack_target_count, replace=False)
X_val_attack_sampled = X_val_attack[attack_indices]
y_val_attack_sampled = y_val_attack[attack_indices]

X_val_sub = np.vstack([X_val_normal, X_val_attack_sampled])
y_val_sub = np.concatenate([y_val_normal, y_val_attack_sampled])

X_val_15 = X_val_sub[:, top_indices]

# LOF Model (LOF has novelty=True to predict on new data)
lof = LocalOutlierFactor(n_neighbors=20, novelty=True, contamination=0.05, n_jobs=-1)
# Fit on normal validation data for a quick check
lof.fit(X_val_normal[:, top_indices])

preds = lof.predict(X_val_15) # 1 for normal, -1 for anomaly
preds_binary = (preds == -1).astype(int)

print("--- LOF Baseline ---")
print(f"F1: {f1_score(y_val_sub, preds_binary, zero_division=0):.4f}")
print(f"Precision: {precision_score(y_val_sub, preds_binary, zero_division=0):.4f}")
print(f"Recall: {recall_score(y_val_sub, preds_binary, zero_division=0):.4f}")
