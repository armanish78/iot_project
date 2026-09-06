import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from sklearn.ensemble import IsolationForest
import pickle
import json

X_train_normal = np.load('data/processed/X_train_normal.npy', allow_pickle=True).astype(np.float32)
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']

with open('backend/models/pca_model.pkl', 'rb') as f:
    pca_model = pickle.load(f)

# Subsample Validation set to 5% anomalies
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

X_train_pca = pca_model.transform(X_train_normal[:, top_indices])
X_val_pca = pca_model.transform(X_val_if_sub[:, top_indices])

n_estimators_list = [100, 200, 300]
max_samples_list = [256, 1024, 'auto']

best_val_f1 = 0
best_params = {}
best_model = None

for n in n_estimators_list:
    for ms in max_samples_list:
        model = IsolationForest(contamination=0.1, n_estimators=n, max_samples=ms, random_state=42, n_jobs=-1)
        model.fit(X_train_pca)
        
        scores = model.decision_function(X_val_pca)
        auc = roc_auc_score(y_val_if_sub, -scores)
        
        # Tune threshold
        thresholds = np.linspace(np.min(scores), np.max(scores), 100)
        local_best_f1 = 0
        local_best_thresh = 0
        for t in thresholds:
            preds = (scores < t).astype(int)
            f1 = f1_score(y_val_if_sub, preds, zero_division=0)
            if f1 > local_best_f1:
                local_best_f1 = f1
                local_best_thresh = t
                
        print(f"n_estimators: {n}, max_samples: {ms} -> AUC: {auc:.4f}, Best F1: {local_best_f1:.4f} at Thresh: {local_best_thresh}")
        
        if local_best_f1 > best_val_f1:
            best_val_f1 = local_best_f1
            best_params = {'n_estimators': n, 'max_samples': ms, 'threshold': local_best_thresh}
            best_model = model

print("\nBEST PARAMS:", best_params)
