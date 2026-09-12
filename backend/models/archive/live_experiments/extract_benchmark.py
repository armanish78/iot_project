import pandas as pd
import numpy as np
import os
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import joblib

# Paths
DATA_PATH = os.path.join("..", "..", "..", "data", "datasets", "unsw_nb15.csv")
OUT_DIR = "benchmark_data"

def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    print("Loading raw UNSW-NB15 data...")
    df = pd.read_csv(DATA_PATH)
    
    print("Extracting 16 LiveFlowExtractor features...")
    # Exact 16 features
    features = [
        "spkts", "dpkts", "sbytes", "dbytes", "dur", "sttl", "dttl",
        "smean", "dmean", "rate", "sload", "dload",
        "proto_tcp", "proto_udp", "proto_icmp", "proto_other"
    ]
    
    # Process protocol
    df['proto'] = df['proto'].astype(str).str.lower()
    df['proto_tcp'] = (df['proto'] == 'tcp').astype(int)
    df['proto_udp'] = (df['proto'] == 'udp').astype(int)
    df['proto_icmp'] = (df['proto'] == 'icmp').astype(int)
    df['proto_other'] = (~df['proto'].isin(['tcp', 'udp', 'icmp'])).astype(int)
    
    X = df[features].values.astype(np.float32)
    y = df['label'].values.astype(int)
    
    print(f"Dataset shape: {X.shape}")
    
    # Train/Val/Test Split (60/20/20)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=42, stratify=y_train_val
    ) # 0.25 * 0.8 = 0.2
    
    # Create scaler based on train data ONLY
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Save
    print("Saving to disk...")
    np.save(os.path.join(OUT_DIR, "X_train.npy"), X_train_scaled)
    np.save(os.path.join(OUT_DIR, "X_val.npy"), X_val_scaled)
    np.save(os.path.join(OUT_DIR, "X_test.npy"), X_test_scaled)
    np.save(os.path.join(OUT_DIR, "y_train.npy"), y_train)
    np.save(os.path.join(OUT_DIR, "y_val.npy"), y_val)
    np.save(os.path.join(OUT_DIR, "y_test.npy"), y_test)
    
    joblib.dump(scaler, os.path.join(OUT_DIR, "scaler.pkl"))
    
    with open(os.path.join(OUT_DIR, "feature_names.json"), "w") as f:
        json.dump({"features": features}, f, indent=4)
        
    print("Extraction complete!")

if __name__ == "__main__":
    main()
