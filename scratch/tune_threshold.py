import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import pickle

# Load data
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

# IF uses PCA features, load IF model and PCA
with open('backend/models/isolation_forest_model.pkl', 'rb') as f:
    if_model = pickle.load(f)
with open('backend/models/pca_model.pkl', 'rb') as f:
    pca_model = pickle.load(f)
import json
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']

# Subsample Validation set to 5% anomalies to match X_test_if
X_val_normal = X_val[y_val == 0]
y_val_normal = y_val[y_val == 0]
X_val_attack = X_val[y_val == 1]
y_val_attack = y_val[y_val == 1]

# Calculate target attack count for 5% prevalence
attack_target_count = int(len(X_val_normal) * 0.05 / 0.95)

# Assuming we have enough attacks in validation
np.random.seed(42)
attack_indices = np.random.choice(len(X_val_attack), attack_target_count, replace=False)
X_val_attack_sampled = X_val_attack[attack_indices]
y_val_attack_sampled = y_val_attack[attack_indices]

X_val_if_sub = np.vstack([X_val_normal, X_val_attack_sampled])
y_val_if_sub = np.concatenate([y_val_normal, y_val_attack_sampled])

# Apply feature selection and PCA
X_val_if_selected = X_val_if_sub[:, top_indices]
X_val_if_pca = pca_model.transform(X_val_if_selected)

# Get decision function scores
scores = if_model.decision_function(X_val_if_pca)
# For sklearn IsolationForest, lower scores (negative) are anomalies, higher (positive) are normal.
# Therefore, anomaly if score < threshold.

thresholds = np.linspace(np.min(scores), np.max(scores), 200)
best_f1 = 0
best_thresh = 0
best_metrics = {}

for t in thresholds:
    # 1 if anomaly (attack), 0 if normal
    preds = (scores < t).astype(int)
    
    # We want to identify attacks (class 1)
    f1 = f1_score(y_val_if_sub, preds, zero_division=0)
    
    if f1 > best_f1:
        best_f1 = f1
        best_thresh = t
        best_metrics = {
            'precision': precision_score(y_val_if_sub, preds, zero_division=0),
            'recall': recall_score(y_val_if_sub, preds, zero_division=0),
            'f1': f1,
            'cm': confusion_matrix(y_val_if_sub, preds).tolist()
        }

print(f"Optimal Threshold: {best_thresh}")
print(f"Best Validation F1: {best_metrics['f1']:.4f}")
print(f"Precision: {best_metrics['precision']:.4f}")
print(f"Recall: {best_metrics['recall']:.4f}")
print(f"Confusion Matrix: {best_metrics['cm']}")

# Evaluate on X_test_if with this threshold
X_test_if = np.load('data/processed/X_test_if.npy', allow_pickle=True).astype(np.float32)
y_test_if = np.load('data/processed/y_test_if.npy', allow_pickle=True).astype(int)
X_test_if_selected = X_test_if[:, top_indices]
X_test_if_pca = pca_model.transform(X_test_if_selected)

test_scores = if_model.decision_function(X_test_if_pca)
test_preds = (test_scores < best_thresh).astype(int)

print(f"\nTEST METRICS (with new threshold):")
print(f"F1: {f1_score(y_test_if, test_preds):.4f}")
print(f"Precision: {precision_score(y_test_if, test_preds):.4f}")
print(f"Recall: {recall_score(y_test_if, test_preds):.4f}")
print(f"Confusion Matrix: {confusion_matrix(y_test_if, test_preds).tolist()}")

