import numpy as np
import json
from sklearn.metrics import precision_score, recall_score, f1_score
import pickle

# Load Data
X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

# Load Top 15 features
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']
    if_threshold = info['if_threshold']

with open('backend/models/random_forest_model.pkl', 'rb') as f:
    rf_model = pickle.load(f)
    
with open('backend/models/isolation_forest_model.pkl', 'rb') as f:
    if_model = pickle.load(f)

X_val_15 = X_val[:, top_indices]

# Predictions
rf_preds = rf_model.predict(X_val)
rf_probs = rf_model.predict_proba(X_val)[:, 1]
if_scores = if_model.decision_function(X_val_15)

# 1. Baseline RF
print(f"RF Baseline F1: {f1_score(y_val, rf_preds):.4f}")

# 2. Current OR logic (with tuned IF threshold)
if_preds = (if_scores < if_threshold).astype(int)
hybrid_or = (rf_preds == 1) | (if_preds == 1)
print(f"Current OR Logic F1: {f1_score(y_val, hybrid_or):.4f} (P: {precision_score(y_val, hybrid_or):.4f}, R: {recall_score(y_val, hybrid_or):.4f})")

# 3. Soft Voting
# Normalize IF scores based on training min/max
# We will use validation min/max here as a proxy to see theoretical limit
if_min, if_max = np.min(if_scores), np.max(if_scores)
if_scores_norm = (if_scores - if_min) / (if_max - if_min)
if_probs = 1 - if_scores_norm 

best_f1 = -1
best_w = 0
for w_rf in np.linspace(0.5, 0.95, 20):
    hybrid_soft = (w_rf * rf_probs + (1 - w_rf) * if_probs) > 0.5
    f1 = f1_score(y_val, hybrid_soft)
    if f1 > best_f1:
        best_f1 = f1
        best_w = w_rf

print(f"Soft Voting (RF Weight={best_w:.2f}) F1: {best_f1:.4f}")

# 4. RF Probability Thresholding
# If RF Prob > threshold_1, Attack.
# If RF Prob < threshold_2, Normal.
# If between threshold_2 and threshold_1, trust IF.
best_f1 = -1
best_t1, best_t2 = 0, 0
for t1 in np.linspace(0.5, 0.9, 5):
    for t2 in np.linspace(0.1, 0.5, 5):
        hybrid_override = np.zeros_like(rf_preds)
        for i in range(len(y_val)):
            if rf_probs[i] >= t1:
                hybrid_override[i] = 1
            elif rf_probs[i] <= t2:
                hybrid_override[i] = 0
            else:
                hybrid_override[i] = if_preds[i]
                
        f1 = f1_score(y_val, hybrid_override)
        if f1 > best_f1:
            best_f1 = f1
            best_t1 = t1
            best_t2 = t2
            
print(f"RF Uncertainty Override (T1={best_t1:.2f}, T2={best_t2:.2f}) F1: {best_f1:.4f}")

