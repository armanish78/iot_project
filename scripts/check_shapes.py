import numpy as np
import json
import os

p = 'data/processed'
print(f"X_train: {np.load(os.path.join(p, 'X_train.npy'), allow_pickle=True).shape}")
print(f"X_test: {np.load(os.path.join(p, 'X_test.npy'), allow_pickle=True).shape}")
print(f"y_train: {np.load(os.path.join(p, 'y_train.npy'), allow_pickle=True).shape}")
print(f"y_test: {np.load(os.path.join(p, 'y_test.npy'), allow_pickle=True).shape}")
features = json.load(open(os.path.join(p, 'feature_names.json')))
print(f"Final feature count: {len(features)}")
