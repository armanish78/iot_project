import pandas as pd
from sklearn.model_selection import train_test_split
from data.preprocessing.logger import get_logger
from config.preprocessing_config import (
    TRAIN_SIZE,
    VAL_SIZE,
    TEST_SIZE,
    RANDOM_STATE,
)

logger = get_logger(__name__)


def split_data(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Split data into train, validation, and test sets.

    Args:
        X (pd.DataFrame): Feature matrix
        y (pd.Series): Target labels

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    logger.info(
        f"Splitting data into {TRAIN_SIZE*100}% Train, {VAL_SIZE*100}% Val, {TEST_SIZE*100}% Test..."
    )

    # First split: Train vs Temp (Val + Test)
    temp_size = VAL_SIZE + TEST_SIZE
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=temp_size, random_state=RANDOM_STATE, stratify=y
    )

    # Second split: Val vs Test
    test_ratio_of_temp = TEST_SIZE / temp_size
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=test_ratio_of_temp,
        random_state=RANDOM_STATE,
        stratify=y_temp,
    )

    logger.info(f"Train set: {len(X_train)} samples")
    logger.info(f"Validation set: {len(X_val)} samples")
    logger.info(f"Test set: {len(X_test)} samples")

    return X_train, X_val, X_test, y_train, y_val, y_test
