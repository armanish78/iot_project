import numpy as np
import pandas as pd
import json

X_train_normal = np.load('data/processed/X_train_normal.npy', allow_pickle=True)
with open('backend/models/feature_names.json', 'r') as f:
    info = json.load(f)
    top_indices = info['if_top_indices']
    feature_names = info['features']

selected_features = [feature_names[i] for i in top_indices]
df = pd.DataFrame(X_train_normal[:, top_indices], columns=selected_features)

print("--- Feature Analysis ---")
for col in df.columns:
    col_data = df[col]
    print(f"Feature: {col}")
    print(f"  Min: {col_data.min():.4f}, Max: {col_data.max():.4f}, Mean: {col_data.mean():.4f}, Std: {col_data.std():.4f}")
    if col_data.std() < 0.001:
        print("  WARNING: Near constant!")
