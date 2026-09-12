import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import json
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def main():
    print("Loading datasets...")
    df_train = pd.read_csv('train_features.csv')
    df_test = pd.read_csv('test_features.csv')
    
    # Separate labels
    y_train = df_train['Label'].values
    y_test = df_test['Label'].values
    
    # Drop labels from features
    X_train = df_train.drop(columns=['Label'])
    X_test = df_test.drop(columns=['Label'])
    
    feature_names = list(X_train.columns)
    
    print(f"Train set: {len(X_train)} flows (Benign: {sum(y_train==0)}, Attack: {sum(y_train==1)})")
    print(f"Test set:  {len(X_test)} flows (Benign: {sum(y_test==0)}, Attack: {sum(y_test==1)})")
    
    print("\nFitting StandardScaler strictly on training data...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Calculate scale_pos_weight to handle class imbalance
    num_benign = sum(y_train == 0)
    num_attack = sum(y_train == 1)
    scale_pos_weight = num_benign / max(1, num_attack)
    print(f"Computed scale_pos_weight for XGBoost: {scale_pos_weight:.2f}")

    print("\nTraining XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1
    )
    
    # We will fit on the training data. (Optionally use internal K-Fold or eval set from train if needed, 
    # but for simplicity and robustness we fit directly).
    model.fit(X_train_scaled, y_train)
    
    print("\nEvaluating on UNTOUCHED Test Set...")
    # Predict probabilities to allow threshold tuning if needed
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Default threshold 0.5
    threshold = 0.5
    y_pred = (y_pred_proba >= threshold).astype(int)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}  (TARGET: > 0.9000)")
    print(f"F1 Score:  {f1:.4f}")
    print(f"FPR:       {fpr:.4f}  (TARGET: < 0.0100)")
    print(f"FNR:       {fnr:.4f}")
    print("Confusion Matrix:")
    print(f"          Pred Benign   Pred Attack")
    print(f"True Benign       {tn}           {fp}")
    print(f"True Attack       {fn}           {tp}")

    print("\nSaving production artifacts...")
    out_dir = 'backend/models/live_nfstream'
    os.makedirs(out_dir, exist_ok=True)
    
    joblib.dump(model, os.path.join(out_dir, 'final_xgboost_model.joblib'))
    joblib.dump(scaler, os.path.join(out_dir, 'scaler.joblib'))
    joblib.dump(feature_names, os.path.join(out_dir, 'feature_names.joblib'))
    
    # Label encoder for binary
    # 0 -> BENIGN, 1 -> PortScan
    # To conform with existing API, we need the classes_ array exactly.
    # Sentinel usually looks at the max prob class. 
    # If the model predict_proba returns [prob_benign, prob_attack], the classes_ is just ['BENIGN', 'PortScan']
    label_encoder = LabelEncoder()
    label_encoder.classes_ = np.array(['BENIGN', 'PortScan'])
    joblib.dump(label_encoder, os.path.join(out_dir, 'label_encoder.joblib'))
    
    metadata = {
        "model_type": "xgboost_binary_nfstream",
        "threshold": threshold,
        "classes": ["BENIGN", "PortScan"],
        "metrics": {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "fpr": float(fpr)
        }
    }
    with open(os.path.join(out_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Saved cleanly to {out_dir}/")

if __name__ == "__main__":
    main()
