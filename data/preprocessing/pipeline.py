import os
import json
import numpy as np
import pandas as pd
from config.preprocessing_config import (
    NBIOT_DIR,
    UNSW_FILE,
    SAMPLE_FRACTION,
    PROCESSED_DIR,
)
from data.preprocessing.logger import get_logger
from data.preprocessing.dataset_loader import (
    load_nbiot_dataset,
    load_unsw_dataset,
    combine_datasets,
)
from data.preprocessing.data_cleaner import (
    remove_duplicates,
    remove_irrelevant_columns,
    handle_missing_values,
    fix_data_types,
    validate_data,
)
from data.preprocessing.feature_engineer import extract_all_features
from data.preprocessing.feature_scaling import (
    encode_categorical,
    normalize_features,
)
from data.preprocessing.class_balancer import apply_smote
from data.preprocessing.data_splitter import split_data

logger = get_logger(__name__)


def save_outputs(
    X_train,
    X_val,
    X_test,
    y_train,
    y_val,
    y_test,
    X_train_normal,
    X_test_if,
    y_test_if,
    feature_names,
):
    """Save the numpy arrays and feature names to the processed directory."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    logger.info(f"Saving outputs to {PROCESSED_DIR}...")

    np.save(PROCESSED_DIR / "X_train.npy", X_train.values)
    np.save(PROCESSED_DIR / "X_val.npy", X_val.values)
    np.save(PROCESSED_DIR / "X_test.npy", X_test.values)
    np.save(PROCESSED_DIR / "y_train.npy", y_train.values)
    np.save(PROCESSED_DIR / "y_val.npy", y_val.values)
    np.save(PROCESSED_DIR / "y_test.npy", y_test.values)
    np.save(PROCESSED_DIR / "X_train_normal.npy", X_train_normal.values)
    np.save(PROCESSED_DIR / "X_test_if.npy", X_test_if.values)
    np.save(PROCESSED_DIR / "y_test_if.npy", y_test_if.values)

    with open(PROCESSED_DIR / "feature_names.json", "w") as f:
        json.dump(feature_names.tolist(), f, indent=2)

    logger.info("All files saved successfully.")


def run_pipeline():
    """Execute the full data preprocessing workflow."""
    logger.info("Starting preprocessing pipeline...")

    try:
        # 1. Load Data
        nbiot_df = load_nbiot_dataset(NBIOT_DIR, SAMPLE_FRACTION)
        unsw_df = load_unsw_dataset(UNSW_FILE)
        raw_df = combine_datasets(nbiot_df, unsw_df)

        # 2. Clean Data
        clean_df = remove_duplicates(raw_df)
        clean_df = remove_irrelevant_columns(clean_df)
        clean_df = handle_missing_values(clean_df, strategy="mean")
        clean_df = fix_data_types(clean_df)
        validate_data(clean_df)

        # 3. Feature Engineering
        featured_df = extract_all_features(clean_df)

        # 4. Feature Scaling & Encoding
        encoded_df = encode_categorical(featured_df)
        scaled_df = normalize_features(encoded_df)

        # 5. Data Splitting
        X = scaled_df.drop("label", axis=1)
        y = scaled_df["label"]
        X_train_raw, X_val, X_test, y_train_raw, y_val, y_test = split_data(
            X, y
        )

        # 6. Extract normal traffic for Isolation Forest
        normal_indices = y_train_raw == 0
        X_train_normal = X_train_raw[normal_indices]

        # 6.5 Create IF-specific separate Test Dataset (~5% anomalies)
        X_test_normal = X_test[y_test == 0]
        y_test_normal = y_test[y_test == 0]

        X_test_attack = X_test[y_test == 1]
        y_test_attack = y_test[y_test == 1]

        attack_target_count = int(len(X_test_normal) * 0.05 / 0.95)

        if attack_target_count < len(X_test_attack):
            X_test_attack_sampled = X_test_attack.sample(
                n=attack_target_count, random_state=42
            )
            y_test_attack_sampled = y_test_attack.sample(
                n=attack_target_count, random_state=42
            )
            X_test_if = pd.concat([X_test_normal, X_test_attack_sampled])
            y_test_if = pd.concat([y_test_normal, y_test_attack_sampled])
        else:
            X_test_if = X_test.copy()
            y_test_if = y_test.copy()

        # 7. Class Balancing (Only on Training Data!)
        X_train, y_train = apply_smote(X_train_raw, y_train_raw)

        # 8. Save Outputs
        save_outputs(
            X_train,
            X_val,
            X_test,
            y_train,
            y_val,
            y_test,
            X_train_normal,
            X_test_if,
            y_test_if,
            X.columns,
        )

        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
