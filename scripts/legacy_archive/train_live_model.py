import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from imblearn.over_sampling import SMOTE
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
def train_live():
    print("Loading UNSW-NB15...")
    df = pd.read_csv("data/datasets/unsw_nb15.csv")
    
    # 1. Feature Adapter
    print("Adapting features...")
    
    # Label
    if "label" not in df.columns and "Label" in df.columns:
        df = df.rename(columns={"Label": "label"})
    
    # Extract only required columns, drop missing
    core_cols = ["spkts", "dpkts", "sbytes", "dbytes", "dur", "sttl", "dttl", "smean", "dmean", "rate", "sload", "dload", "proto", "label"]
    df = df[core_cols].dropna()
    
    # Build the 16 exact features
    df["proto_tcp"] = (df["proto"].str.lower() == "tcp").astype(int)
    df["proto_udp"] = (df["proto"].str.lower() == "udp").astype(int)
    df["proto_icmp"] = (df["proto"].str.lower() == "icmp").astype(int)
    df["proto_other"] = (~df["proto"].str.lower().isin(["tcp", "udp", "icmp"])).astype(int)
    
    features = [
        "spkts", "dpkts", "sbytes", "dbytes", "dur", "sttl", "dttl", "smean", "dmean", "rate", "sload", "dload",
        "proto_tcp", "proto_udp", "proto_icmp", "proto_other"
    ]
    
    X = df[features]
    y = df["label"].astype(int)
    
    # Split BEFORE SMOTE
    print("Splitting data...")
    X_train_raw, X_test, y_train_raw, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale ONLY on training
    print("Scaling features...")
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame for SMOTE to keep feature names
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=features)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=features)
    
    print(f"Class distribution before SMOTE: 0: {(y_train_raw==0).sum()}, 1: {(y_train_raw==1).sum()}")
    smote = SMOTE(random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train_scaled, y_train_raw)
    print(f"Class distribution after SMOTE: 0: {(y_train_smote==0).sum()}, 1: {(y_train_smote==1).sum()}")
    
    # Train Random Forest
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X_train_smote, y_train_smote)
    
    # Train Isolation Forest
    print("Training Isolation Forest on benign data...")
    # Get only benign (0) from raw un-smoted training data
    benign_idx = y_train_raw.reset_index(drop=True) == 0
    X_train_benign = X_train_scaled[benign_idx]
    
    iso = IsolationForest(n_estimators=50, contamination=0.01, random_state=42, n_jobs=-1)
    iso.fit(X_train_benign)
    
    # Evaluate RF
    print("Evaluating models...")
    rf_preds = rf.predict(X_test_scaled)
    acc = accuracy_score(y_test, rf_preds)
    prec = precision_score(y_test, rf_preds)
    rec = recall_score(y_test, rf_preds)
    f1 = f1_score(y_test, rf_preds)
    cm = confusion_matrix(y_test, rf_preds)
    
    print(f"\nRF Test Metrics:")
    print(f"Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    
    importances = list(zip(features, rf.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    print("\nFeature Importances:")
    for f, imp in importances:
        print(f"  {f}: {imp:.4f}")
    
    metrics = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "test_size": len(y_test)
    }
    
    # Save artifacts
    print("\nSaving live model artifacts...")
    os.makedirs("backend/models/live", exist_ok=True)
    with open("backend/models/live/live_rf.pkl", "wb") as f:
        pickle.dump(rf, f)
    with open("backend/models/live/live_if.pkl", "wb") as f:
        pickle.dump(iso, f)
    with open("backend/models/live/live_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open("backend/models/live/live_feature_names.json", "w") as f:
        json.dump(features, f)
    with open("backend/models/live/live_metadata.json", "w") as f:
        json.dump({"schema_version": "1.0", "type": "live_unsw_only", "features": 16}, f)
    with open("backend/models/live/live_metrics.json", "w") as f:
        json.dump(metrics, f)
        
    print("Live pipeline training complete!")

if __name__ == "__main__":
    train_live()
