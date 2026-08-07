import pandas as pd
from imblearn.over_sampling import SMOTE
from data.preprocessing.logger import get_logger
from config.preprocessing_config import RANDOM_STATE

logger = get_logger(__name__)


def check_class_balance(y: pd.Series) -> dict:
    """Return the class distribution."""
    return y.value_counts().to_dict()


def apply_smote(
    X: pd.DataFrame, y: pd.Series
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Apply SMOTE to balance the dataset.

    Args:
        X (pd.DataFrame): Feature matrix
        y (pd.Series): Labels

    Returns:
        tuple: (Balanced X, Balanced y)
    """
    logger.info(f"Class distribution before SMOTE: {check_class_balance(y)}")

    smote = SMOTE(random_state=RANDOM_STATE)
    X_balanced, y_balanced = smote.fit_resample(X, y)

    # Reconstruct DataFrame to maintain column names
    X_balanced_df = pd.DataFrame(X_balanced, columns=X.columns)

    logger.info(
        f"Class distribution after SMOTE: {check_class_balance(y_balanced)}"
    )
    return X_balanced_df, y_balanced
