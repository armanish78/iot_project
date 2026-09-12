import numpy as np
import pandas as pd
import json
import pickle
import os

from data.preprocessing.dataset_loader import load_nbiot_dataset, load_unsw_dataset, combine_datasets
from data.preprocessing.data_cleaner import remove_duplicates, remove_irrelevant_columns, handle_missing_values, fix_data_types
from config.preprocessing_config import NBIOT_DIR, UNSW_FILE, SAMPLE_FRACTION

def run_audit():
    print("=== PIPELINE AUDIT ===")
    
    # 1. Load Data
    print("Loading data for audit...")
    nbiot_df = load_nbiot_dataset(NBIOT_DIR, SAMPLE_FRACTION)
    unsw_df = load_unsw_dataset(UNSW_FILE)
    raw_df = combine_datasets(nbiot_df, unsw_df)
    
    # 2. Check duplicates before removing columns
    raw_dupes = raw_df.duplicated().sum()
    print(f"Duplicates in raw data (with identifiers): {raw_dupes} ({raw_dupes/len(raw_df)*100:.2f}%)")
    
    # 3. Clean
    clean_df = remove_duplicates(raw_df)
    clean_df = remove_irrelevant_columns(clean_df)
    clean_df = handle_missing_values(clean_df, strategy="mean")
    clean_df = fix_data_types(clean_df)
    
    # 4. Check duplicates after removing columns
    cleaned_dupes = clean_df.duplicated().sum()
    print(f"Duplicates in cleaned data (identifiers removed): {cleaned_dupes} ({cleaned_dupes/len(clean_df)*100:.2f}%)")
    
    # 5. Check processed data leakage
    print("\nLoading processed numpy arrays...")
    p = 'data/processed'
    X_train = np.load(os.path.join(p, 'X_train.npy'), allow_pickle=True)
    y_train = np.load(os.path.join(p, 'y_train.npy'), allow_pickle=True)
    X_test = np.load(os.path.join(p, 'X_test.npy'), allow_pickle=True)
    y_test = np.load(os.path.join(p, 'y_test.npy'), allow_pickle=True)
    
    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    
    # 6. Check duplicates within splits
    # Convert numpy to pandas or use unique for fast checking
    train_df = pd.DataFrame(X_train)
    test_df = pd.DataFrame(X_test)
    
    train_dupes = train_df.duplicated().sum()
    test_dupes = test_df.duplicated().sum()
    print(f"Duplicates within X_train: {train_dupes} ({train_dupes/len(X_train)*100:.2f}%)")
    print(f"Duplicates within X_test: {test_dupes} ({test_dupes/len(X_test)*100:.2f}%)")
    
    # 7. Check for train/test leakage
    print("Checking for leakage across train/test splits...")
    # Because numpy arrays could contain floats that slightly differ, merge on exact might be strict, 
    # but they are just split, so exact match is fine.
    # Convert to sets of tuples for fast intersection
    train_set = set(map(tuple, X_train))
    test_set = set(map(tuple, X_test))
    
    intersection = train_set.intersection(test_set)
    print(f"Exact row matches (leakage) between X_train and X_test: {len(intersection)}")
    
    # 8. Feature Names
    features = json.load(open(os.path.join(p, 'feature_names.json')))
    print(f"\nfeature_names.json length: {len(features)}")
    
    # 9. Scaler Check
    with open(os.path.join(p, 'scaler.pkl'), 'rb') as f:
        scaler = pickle.load(f)
    print(f"Scaler type: {type(scaler)}")
    if hasattr(scaler, 'n_features_in_'):
        print(f"Scaler expected features (n_features_in_): {scaler.n_features_in_}")
    
    print("\nAudit Complete.")

if __name__ == "__main__":
    run_audit()
