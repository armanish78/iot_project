import numpy as np
import pickle
from sklearn.metrics import f1_score

X_val = np.load('data/processed/X_val.npy', allow_pickle=True).astype(np.float32)
y_val = np.load('data/processed/y_val.npy', allow_pickle=True).astype(int)

with open('backend/models/random_forest_model.pkl', 'rb') as f:
    rf_model = pickle.load(f)
    
rf_preds = rf_model.predict(X_val)
print(f"RF Alone Val F1: {f1_score(y_val, rf_preds):.4f}")
