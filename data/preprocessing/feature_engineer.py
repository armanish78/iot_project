import pandas as pd
import numpy as np
from data.preprocessing.logger import get_logger

logger = get_logger(__name__)


def extract_packet_statistics(
    df: pd.DataFrame, window: int = 10
) -> pd.DataFrame:
    """Extract packet size stats using a rolling window."""
    if "packet_size" not in df.columns:
        return df

    df = df.copy()
    df["packet_size_min"] = (
        df["packet_size"].rolling(window, min_periods=1).min()
    )
    df["packet_size_max"] = (
        df["packet_size"].rolling(window, min_periods=1).max()
    )
    df["packet_size_mean"] = (
        df["packet_size"].rolling(window, min_periods=1).mean()
    )
    df["packet_size_std"] = (
        df["packet_size"].rolling(window, min_periods=1).std().fillna(0)
    )
    logger.info("Extracted packet size statistics")
    return df


def extract_flow_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract flow-based features."""
    df = df.copy()
    df["byte_count"] = df.get("packet_size", 0).fillna(0)
    df["flow_duration"] = df.get("duration", 1e-6).fillna(0).clip(lower=1e-6)
    df["packet_rate"] = (df["byte_count"] / df["flow_duration"]).replace(
        [np.inf, -np.inf], 0
    )
    logger.info("Extracted flow-based features")
    return df


def extract_protocol_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode protocol types to standard names."""
    df = df.copy()
    known = {"TCP", "UDP", "ICMP"}

    def norm(p):
        if pd.isna(p):
            return "UNKNOWN"
        s = str(p).upper()
        return s if s in known else "OTHER"

    df["protocol"] = df.get("protocol", "UNKNOWN").apply(norm)
    logger.info("Extracted protocol features")
    return df


def extract_timing_features(
    df: pd.DataFrame, timestamp_col: str = "timestamp"
) -> pd.DataFrame:
    """Extract inter-arrival time and duration."""
    df = df.copy()
    if timestamp_col in df.columns and df[timestamp_col].notna().any():
        ts = pd.to_numeric(df[timestamp_col], errors="coerce")
        df["inter_arrival_time"] = ts.diff().abs().fillna(0)
    else:
        df["inter_arrival_time"] = df.get(
            "duration", pd.Series(0, index=df.index)
        ).fillna(0)
    logger.info("Extracted timing features")
    return df


def extract_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Runs all feature extraction steps."""
    logger.info("Starting feature extraction...")
    df = extract_packet_statistics(df)
    df = extract_flow_features(df)
    df = extract_protocol_features(df)
    df = extract_timing_features(df)

    # Drop original granular features that are no longer needed
    to_drop = [c for c in ["packet_size", "duration"] if c in df.columns]
    df = df.drop(columns=to_drop)
    logger.info(f"Feature extraction complete. Total columns: {df.shape[1]}")

    return df
