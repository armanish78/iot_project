import numpy as np
import json
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import pickle

# Load Data
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

# Load Top 15 features
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']
    threshold = info['if_threshold']

with open('backend/models/random_forest_model.pkl', 'rb') as f:
    rf_model = pickle.load(f)
    
with open('backend/models/isolation_forest_model.pkl', 'rb') as f:
    if_model = pickle.load(f)

X_val_15 = X_val[:, top_indices]

# RF Predictions
rf_preds = rf_model.predict(X_val)
rf_probs = rf_model.predict_proba(X_val)[:, 1]

# IF Predictions
if_scores = if_model.decision_function(X_val_15)
if_preds = (if_scores < threshold).astype(int) # 1 if anomaly, 0 if normal

# Strategy 1: OR (Current)
hybrid_or = (rf_preds == 1) | (if_preds == 1)
print("--- STRATEGY 1: OR (Current Baseline) ---")
print(f"F1: {f1_score(y_val, hybrid_or):.4f}")
print(f"Precision: {precision_score(y_val, hybrid_or):.4f}")
print(f"Recall: {recall_score(y_val, hybrid_or):.4f}")

# Strategy 2: AND (Conservative)
hybrid_and = (rf_preds == 1) & (if_preds == 1)
print("\n--- STRATEGY 2: AND ---")
print(f"F1: {f1_score(y_val, hybrid_and):.4f}")
print(f"Precision: {precision_score(y_val, hybrid_and):.4f}")
print(f"Recall: {recall_score(y_val, hybrid_and):.4f}")

# Strategy 3: RF Confidence Threshold Override
# If RF is highly confident (>0.90), trust RF. Else, trust IF.
hybrid_conf = rf_preds.copy()
for i in range(len(y_val)):
    if rf_probs[i] < 0.90 and rf_probs[i] > 0.10: # RF is unsure
        hybrid_conf[i] = if_preds[i]

print("\n--- STRATEGY 3: RF Confidence Override ---")
print(f"F1: {f1_score(y_val, hybrid_conf):.4f}")
print(f"Precision: {precision_score(y_val, hybrid_conf):.4f}")
print(f"Recall: {recall_score(y_val, hybrid_conf):.4f}")

# Strategy 4: Soft Voting (Weighted sum of scores)
# Normalize IF scores to [0, 1] pseudo-probabilities
if_scores_norm = (if_scores - np.min(if_scores)) / (np.max(if_scores) - np.min(if_scores))
# IF outputs lower score for anomaly, so invert it
if_probs = 1 - if_scores_norm 

for w_rf in [0.7, 0.8, 0.9]:
    hybrid_soft = (w_rf * rf_probs + (1 - w_rf) * if_probs) > 0.5
    print(f"\n--- STRATEGY 4: Soft Voting (RF Weight={w_rf}) ---")
    print(f"F1: {f1_score(y_val, hybrid_soft):.4f}")
    print(f"Precision: {precision_score(y_val, hybrid_soft):.4f}")
    print(f"Recall: {recall_score(y_val, hybrid_soft):.4f}")

