import pandas as pd
from pathlib import Path
from data.preprocessing.logger import get_logger

logger = get_logger(__name__)

STANDARD_COLUMNS = [
    "source_ip",
    "dest_ip",
    "protocol",
    "src_port",
    "dst_port",
    "packet_size",
    "duration",
    "timestamp",
    "label",
    "dataset_source",
]


def load_nbiot_dataset(path: str, sample_frac: float = 0.15) -> pd.DataFrame:
    """
    Load N-BaIoT dataset, sampling a fraction of each file to fit in memory.

    Args:
        path (str): Path to directory containing N-BaIoT CSVs.
        sample_frac (float): Fraction of data to sample.

    Returns:
        pd.DataFrame: Merged and sampled N-BaIoT data.
    """
    p = Path(path)
    if not p.exists():
        logger.error(f"N-BaIoT path not found: {path}")
        raise FileNotFoundError(f"N-BaIoT path not found: {path}")

    csv_files = sorted(p.glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {path}")
        raise FileNotFoundError(f"No CSV files found in {path}")

    frames = []
    logger.info(
        f"Loading {len(csv_files)} files from N-BaIoT with sampling rate {sample_frac}..."
    )

    for f in csv_files:
        try:
            df_part = pd.read_csv(f)
            if sample_frac < 1.0:
                df_part = df_part.sample(frac=sample_frac, random_state=42)
            if "label" not in df_part.columns:
                df_part["label"] = 0 if "benign" in f.stem.lower() else 1
            df_part["attack_type"] = f.stem
            frames.append(df_part)
        except Exception as e:
            logger.warning(f"Error reading {f}: {e}")

    df = pd.concat(frames, ignore_index=True)
    df["dataset_source"] = "nbiot"
    logger.info(f"Loaded {len(df)} records from N-BaIoT")
    return df


def load_unsw_dataset(path: str) -> pd.DataFrame:
    """
    Load UNSW-NB15 dataset from a single CSV file.

    Args:
        path (str): Path to UNSW-NB15 CSV.

    Returns:
        pd.DataFrame: Loaded UNSW data.
    """
    p = Path(path)
    if not p.exists():
        logger.error(f"UNSW-NB15 file not found: {path}")
        raise FileNotFoundError(f"UNSW-NB15 file not found: {path}")

    logger.info(f"Loading UNSW-NB15 from {path}...")
    df = pd.read_csv(p)

    if "label" not in df.columns:
        if "Label" in df.columns:
            df = df.rename(columns={"Label": "label"})
        else:
            raise ValueError(
                "UNSW-NB15 CSV must contain a 'label' or 'Label' column"
            )

    df["dataset_source"] = "unsw"
    logger.info(f"Loaded {len(df)} records from UNSW-NB15")
    return df


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Internal helper to standardize column names across datasets."""
    rename_map = {
        "srcip": "source_ip",
        "dstip": "dest_ip",
        "sport": "src_port",
        "dsport": "dst_port",
        "proto": "protocol",
        "dur": "duration",
        "sbytes": "packet_size",
        "Stime": "timestamp",
    }
    existing = {k: v for k, v in rename_map.items() if k in df.columns}
    return df.rename(columns=existing)


def combine_datasets(
    nbiot_df: pd.DataFrame, unsw_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine both datasets onto a shared column schema.

    Args:
        nbiot_df (pd.DataFrame): N-BaIoT data
        unsw_df (pd.DataFrame): UNSW-NB15 data

    Returns:
        pd.DataFrame: Combined dataset
    """
    logger.info("Combining datasets...")
    nbiot_df = _standardize_columns(nbiot_df)
    unsw_df = _standardize_columns(unsw_df)

    combined = pd.concat([nbiot_df, unsw_df], ignore_index=True, sort=False)

    for col in STANDARD_COLUMNS:
        if col not in combined.columns:
            combined[col] = 0

    combined["label"] = combined["label"].astype(int)
    logger.info(
        f"Combined dataset: {len(combined)} records ({(combined.label == 0).sum()} normal, {(combined.label == 1).sum()} attack)"
    )
    return combined
