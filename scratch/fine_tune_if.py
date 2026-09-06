import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.ensemble import IsolationForest
import json

# Load Data
X_train_normal = np.load('data/processed/X_train_normal.npy', allow_pickle=True).astype(np.float32)
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

X_train_normal_15 = X_train_normal[:, top_indices]
X_val_15 = X_val_sub[:, top_indices]

# Grid
n_estimators_list = [150, 200, 250]
max_samples_list = [0.8, 0.9, 1.0]
max_features_list = [0.4, 0.5, 0.6]
contamination_list = [0.05, 0.1, 0.15]

best_f1 = -1
best_thresh = 0
best_params = {}

for c in contamination_list:
    for n in n_estimators_list:
        for ms in max_samples_list:
            for mf in max_features_list:
                model = IsolationForest(
                    n_estimators=n, 
                    max_samples=ms, 
                    max_features=mf,
                    contamination=c, 
                    random_state=42, 
                    n_jobs=-1
                )
                model.fit(X_train_normal_15)
                
                scores = model.decision_function(X_val_15)
                thresholds = np.linspace(np.min(scores), np.max(scores), 100)
                
                for t in thresholds:
                    preds = (scores < t).astype(int)
                    f1 = f1_score(y_val_sub, preds, zero_division=0)
                    if f1 > best_f1:
                        best_f1 = f1
                        best_thresh = t
                        best_params = {"c": c, "n": n, "ms": ms, "mf": mf, "t": t}
                        
print(f"Best Params: {best_params}")
model = IsolationForest(n_estimators=best_params['n'], max_samples=best_params['ms'], max_features=best_params['mf'], contamination=best_params['c'], random_state=42, n_jobs=-1)
model.fit(X_train_normal_15)
preds = (model.decision_function(X_val_15) < best_params['t']).astype(int)
print(f"Validation F1: {best_f1:.4f}")
print(f"Precision: {precision_score(y_val_sub, preds, zero_division=0):.4f}")
print(f"Recall: {recall_score(y_val_sub, preds, zero_division=0):.4f}")

