import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from data.preprocessing.logger import get_logger

logger = get_logger(__name__)


def encode_categorical(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    One-hot encode categorical columns.

    Args:
        df: Input dataframe
        columns: List of columns to encode (auto-detects if None)
    """
    df = df.copy()
    if columns is None:
        columns = [
            c
            for c in df.select_dtypes(include=["object", "category"]).columns
            if c != "label"
        ]

    if not columns:
        logger.info("No categorical columns found for encoding.")
        return df

    df = pd.get_dummies(df, columns=columns, prefix=columns)
    logger.info(f"One-hot encoded columns: {columns}")
    return df


def fit_normalize_features(
    df: pd.DataFrame, label_col: str = "label"
) -> tuple:
    """
    Fit scaler on numeric features and normalize to 0-1 range.
    Returns: (Scaled dataframe, fitted MinMaxScaler, list of numeric columns)
    """
    df = df.copy()
    numeric_cols = [
        c for c in df.select_dtypes(include="number").columns if c != label_col
    ]

    if not numeric_cols:
        logger.warning("No numeric columns found to scale.")
        return df, None, []

    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    logger.info(
        f"Scaled {len(numeric_cols)} numeric features using MinMaxScaler"
    )
    return df, scaler, numeric_cols

def transform_features(
    df: pd.DataFrame, scaler: MinMaxScaler, numeric_cols: list
) -> pd.DataFrame:
    """
    Apply fitted scaler to features.
    """
    df = df.copy()
    if scaler and numeric_cols:
        # Only scale columns that actually exist in df
        valid_cols = [c for c in numeric_cols if c in df.columns]
        df[valid_cols] = scaler.transform(df[valid_cols])
    return df
