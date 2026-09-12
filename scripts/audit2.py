import numpy as np
import pandas as pd
import json
import pickle
import os

from data.preprocessing.dataset_loader import load_nbiot_dataset, load_unsw_dataset, combine_datasets
from data.preprocessing.data_cleaner import remove_duplicates, remove_irrelevant_columns
from config.preprocessing_config import NBIOT_DIR, UNSW_FILE, SAMPLE_FRACTION

def run_audit():
    print("=== FINAL STRICT AUDIT ===")
    
    # 1. Pipeline Stages Check
    print("Loading raw data for stage analysis...")
    nbiot_df = load_nbiot_dataset(NBIOT_DIR, SAMPLE_FRACTION)
    unsw_df = load_unsw_dataset(UNSW_FILE)
    raw_df = combine_datasets(nbiot_df, unsw_df)
    
    rows_before_id_removal = len(raw_df)
    
    # Remove identifiers first (new pipeline order)
    df_no_ids = remove_irrelevant_columns(raw_df.copy())
    rows_after_id_removal = len(df_no_ids)
    
    dupes_before_dedup = df_no_ids.duplicated().sum()
    
    df_deduped = remove_duplicates(df_no_ids)
    rows_after_dedup = len(df_deduped)
    dupes_remaining = df_deduped.duplicated().sum()
    
    print(f"1. Rows before identifier removal: {rows_before_id_removal}")
    print(f"2. Rows after identifier removal: {rows_after_id_removal}")
    print(f"3. Duplicates before deduplication: {dupes_before_dedup}")
    print(f"4. Rows after deduplication: {rows_after_dedup}")
    print(f"5. Duplicates remaining: {dupes_remaining}")
    
    # Conflicting labels check
    # Check if there are exact same features but different labels
    features_only = df_deduped.drop("label", axis=1)
    feature_dupes = features_only.duplicated(keep=False)
    if feature_dupes.any():
        conflicting_rows = df_deduped[feature_dupes]
        # Count how many unique feature sets have >1 unique label
        grouped = conflicting_rows.groupby(list(features_only.columns))['label'].nunique()
        conflicts = grouped[grouped > 1]
        print(f"\nConflicting labels detected: {len(conflicts)} feature vectors have multiple labels.")
        # how it's handled: pandas drop_duplicates kept both because the label column differed
    else:
        print("\nNo conflicting labels detected across identical feature vectors.")
        
    print("\nLoading processed numpy arrays...")
    p = 'data/processed'
    X_train = np.load(os.path.join(p, 'X_train.npy'), allow_pickle=True)
    y_train = np.load(os.path.join(p, 'y_train.npy'), allow_pickle=True)
    X_val = np.load(os.path.join(p, 'X_val.npy'), allow_pickle=True)
    y_val = np.load(os.path.join(p, 'y_val.npy'), allow_pickle=True)
    X_test = np.load(os.path.join(p, 'X_test.npy'), allow_pickle=True)
    y_test = np.load(os.path.join(p, 'y_test.npy'), allow_pickle=True)
    
    print(f"6. Final row counts - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print(f"7. X_train shape: {X_train.shape}")
    print(f"8. X_val shape: {X_val.shape}")
    print(f"9. X_test shape: {X_test.shape}")
    print(f"10. y_train shape: {y_train.shape}, y_val shape: {y_val.shape}, y_test shape: {y_test.shape}")
    
    print(f"\n11. Exact class distributions:")
    print(f"   y_train: 0: {(y_train==0).sum()}, 1: {(y_train==1).sum()}")
    print(f"   y_val:   0: {(y_val==0).sum()}, 1: {(y_val==1).sum()}")
    print(f"   y_test:  0: {(y_test==0).sum()}, 1: {(y_test==1).sum()}")
    
    print("\nChecking for exact feature-vector overlap (Leakage)...")
    train_set = set(map(tuple, X_train))
    val_set = set(map(tuple, X_val))
    test_set = set(map(tuple, X_test))
    
    print(f"16. Overlap counts:")
    print(f"   train intersect validation = {len(train_set.intersection(val_set))}")
    print(f"   train intersect test = {len(train_set.intersection(test_set))}")
    print(f"   validation intersect test = {len(val_set.intersection(test_set))}")
    
    features = json.load(open(os.path.join(p, 'feature_names.json')))
    print(f"\n17. feature_names.json length: {len(features)}")
    
    with open(os.path.join(p, 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    print(f"18. Scaler expected features: {scaler.n_features_in_}")
    
    # Check timestamp of npy files to confirm regeneration
    import time
    mtime = os.path.getmtime(os.path.join(p, 'X_train.npy'))
    print(f"20. X_train.npy generated recently: {time.time() - mtime < 3600} (within last hour)")
    
    print("\nAudit Complete.")

if __name__ == "__main__":
    run_audit()
