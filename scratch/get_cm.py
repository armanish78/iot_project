import numpy as np
from sklearn.metrics import confusion_matrix
import json
import pickle

X_test_if = np.load('data/processed/X_test_if.npy', allow_pickle=True).astype(np.float32)
y_test_if = np.load('data/processed/y_test_if.npy', allow_pickle=True).astype(int)

with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']
    thresh = info['if_threshold']

with open('backend/models/pca_model.pkl', 'rb') as f:
    pca_model = pickle.load(f)

with open('backend/models/isolation_forest_model.pkl', 'rb') as f:
    if_model = pickle.load(f)

X_test_pca = pca_model.transform(X_test_if[:, top_indices])
scores = if_model.decision_function(X_test_pca)
preds = (scores < thresh).astype(int)

print(confusion_matrix(y_test_if, preds))
