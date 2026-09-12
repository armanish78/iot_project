import os
import json
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    benchmark_dir = os.path.join(SCRIPT_DIR, "benchmark_data")
    x_train_path = os.path.join(benchmark_dir, "X_train.npy")
    x_test_path = os.path.join(benchmark_dir, "X_test.npy")
    orig_scaler_path = os.path.join(benchmark_dir, "scaler.pkl")
    
    rf_dir = os.path.join(SCRIPT_DIR, "rf_14f")
    model_path = os.path.join(rf_dir, "model.pkl")
    features_path = os.path.join(rf_dir, "feature_names.json")
    
    new_scaler_path = os.path.join(rf_dir, "scaler_14f.pkl")
    metadata_path = os.path.join(rf_dir, "scaler_14f_metadata.json")
    
    # 1. Load the original 16-feature scaler and the scaled training data
    orig_scaler = joblib.load(orig_scaler_path)
    X_train_scaled_16 = np.load(x_train_path)
    X_test_scaled_16 = np.load(x_test_path)
    
    # Inverse transform to get the EXACT original raw training data used
    X_train_raw_16 = orig_scaler.inverse_transform(X_train_scaled_16)
    X_test_raw_16 = orig_scaler.inverse_transform(X_test_scaled_16)
    
    # 2. Extract exactly the 14 columns
    idx_14 = [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    X_train_raw_14 = X_train_raw_16[:, idx_14]
    X_test_raw_14 = X_test_raw_16[:, idx_14]
    
    # 3. Create and fit a NEW MinMaxScaler ON THE 14 COLUMNS ONLY
    new_scaler = MinMaxScaler()
    new_scaler.fit(X_train_raw_14)
    
    # Save the new scaler
    joblib.dump(new_scaler, new_scaler_path)
    print(f"Saved corrected scaler to {new_scaler_path}")
    
    # 4. Validation
    model = joblib.load(model_path)
    with open(features_path, "r") as f:
        feature_names = json.load(f)["features"]
        
    print("\n--- VALIDATION ---")
    print(f"len(feature_names) == {len(feature_names)}")
    print(f"new_scaler.n_features_in_ == {getattr(new_scaler, 'n_features_in_', 'Unknown')}")
    print(f"model.n_features_in_ == {getattr(model, 'n_features_in_', 'Unknown')}")
    
    # 5. Compare Predictions on test data
    # Old pipeline logic used during experiments (Scale 16 -> Slice 14 -> Predict)
    X_test_scaled_old_14 = X_test_scaled_16[:, idx_14]
    probs_old = model.predict_proba(X_test_scaled_old_14)[:, 1]
    
    # New pipeline logic for deployment (Slice 14 -> Scale 14 -> Predict)
    X_test_scaled_new_14 = new_scaler.transform(X_test_raw_14)
    probs_new = model.predict_proba(X_test_scaled_new_14)[:, 1]
    
    diff = np.abs(probs_old - probs_new).max()
    print(f"\nEvaluating on test data...")
    print(f"Maximum absolute difference in probabilities between pipelines: {diff}")
    
    if diff < 1e-5:
        print("SUCCESS: The corrected scaler produces mathematically identical predictions.")
    else:
        print("WARNING: There is a material difference in predictions!")
        
    # Sample Prediction
    sample = X_test_raw_14[0:1] # Just one sample
    scaled_sample = new_scaler.transform(sample)
    pred_prob = model.predict_proba(scaled_sample)[0, 1]
    pred_class = model.predict(scaled_sample)[0]
    print("\nSample Prediction:")
    print(f"Raw Sample (14f): {sample[0]}")
    print(f"Scaled Sample (14f): {scaled_sample[0]}")
    print(f"Prob: {pred_prob}, Pred: {pred_class}")
    
    # 6. Metadata
    metadata = {
        "scaler_feature_count": int(getattr(new_scaler, 'n_features_in_', 0)),
        "feature_order": feature_names,
        "training_data": "benchmark_data/X_train.npy (inversely transformed, sliced to 14 columns, refit)",
        "notes": "Original scaler was incorrectly fitted on 16 features. Corrected scaler was fitted exactly on 14 features of candidate's training data for deployment compatibility."
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Saved metadata to {metadata_path}")

if __name__ == "__main__":
    main()
