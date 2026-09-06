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
    feature_names = info['features']

selected_features = [feature_names[i] for i in top_indices]

# Remove dataset_source features
filtered_indices = [i for i, name in zip(top_indices, selected_features) if 'dataset_source' not in name]
print("New feature count:", len(filtered_indices))

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

X_train_normal_filt = X_train_normal[:, filtered_indices]
X_val_filt = X_val_sub[:, filtered_indices]

model = IsolationForest(
    n_estimators=200, 
    max_samples=1.0, 
    max_features=0.5,
    contamination=0.1, 
    random_state=42, 
    n_jobs=-1
)
model.fit(X_train_normal_filt)

scores = model.decision_function(X_val_filt)
thresholds = np.linspace(np.min(scores), np.max(scores), 100)

best_f1 = -1
for t in thresholds:
    preds = (scores < t).astype(int)
    f1 = f1_score(y_val_sub, preds, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1

print(f"Validation F1 (No Dataset ID): {best_f1:.4f}")
