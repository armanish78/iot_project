import pandas as pd
import numpy as np
from data.preprocessing.logger import get_logger

logger = get_logger(__name__)

DEFAULT_IRRELEVANT_COLUMNS = [
    "source_ip",
    "dest_ip",
    "timestamp",
    "id",
    "attack_cat",
    "attack_type",
]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate records."""
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    logger.info(f"Removed {before - len(df)} duplicate rows")
    return df


def remove_irrelevant_columns(
    df: pd.DataFrame, columns: list = None
) -> pd.DataFrame:
    """Remove columns not useful for ML."""
    columns = columns if columns is not None else DEFAULT_IRRELEVANT_COLUMNS
    to_drop = [c for c in columns if c in df.columns]
    df = df.drop(columns=to_drop)
    logger.info(f"Dropped irrelevant columns: {to_drop}")
    return df


def handle_missing_values(
    df: pd.DataFrame, strategy: str = "mean"
) -> pd.DataFrame:
    """
    Handle NaN and null values.

    Args:
        df: Input dataframe
        strategy: 'drop', 'mean', 'median', or 'zero'
    """
    before_na = df.isna().sum().sum()
    if before_na == 0:
        logger.info("No missing values to handle.")
        return df

    logger.info(f"Handling missing values using strategy: {strategy}")

    if strategy == "drop":
        df = df.dropna().reset_index(drop=True)
    elif strategy in ("mean", "median"):
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns

        for col in numeric_cols:
            if df[col].isna().any():
                fill = (
                    df[col].mean() if strategy == "mean" else df[col].median()
                )
                df[col] = df[col].fillna(fill)

        for col in categorical_cols:
            if df[col].isna().any():
                mode = df[col].mode()
                df[col] = df[col].fillna(
                    mode.iloc[0] if not mode.empty else "unknown"
                )
    elif strategy == "zero":
        df = df.fillna(0)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    logger.info(
        f"Missing values count: {before_na} -> {df.isna().sum().sum()}"
    )
    return df.reset_index(drop=True)


def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure data types are correct."""
    for col in df.columns:
        if col == "label":
            df[col] = (
                pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            )
        elif df[col].dtype == object:
            # Try to convert objects to numeric where possible, ignore if strictly strings
            try:
                df[col] = pd.to_numeric(df[col])
            except ValueError:
                pass
    logger.info("Fixed data types")
    return df


def validate_data(df: pd.DataFrame, label_col: str = "label") -> bool:
    """Validate data integrity."""
    if df.empty:
        logger.error("Validation failed: empty DataFrame")
        return False
    if set(df[label_col].unique()) - {0, 1}:
        logger.error("Validation failed: unexpected label values")
        return False
    if df.isna().sum().sum() > 0:
        logger.error("Validation failed: NaNs remain")
        return False
    if df.duplicated().sum() > 0:
        logger.error("Validation failed: duplicates remain")
        return False

    logger.info("Data validation passed successfully")
    return True
