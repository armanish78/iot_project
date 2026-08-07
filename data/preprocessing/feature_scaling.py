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


def normalize_features(
    df: pd.DataFrame, label_col: str = "label"
) -> pd.DataFrame:
    """
    Normalize numerical features to 0-1 range using MinMaxScaler.

    Args:
        df: Input dataframe
        label_col: The target label column to exclude from scaling

    Returns:
        Scaled dataframe
    """
    df = df.copy()
    numeric_cols = [
        c for c in df.select_dtypes(include="number").columns if c != label_col
    ]

    if not numeric_cols:
        logger.warning("No numeric columns found to scale.")
        return df

    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    logger.info(
        f"Scaled {len(numeric_cols)} numeric features using MinMaxScaler"
    )
    return df
