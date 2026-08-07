import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATASETS_DIR = DATA_DIR / "datasets"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"
MODELS_DIR = PROJECT_ROOT / "models"

# Specific dataset directories/files
NBIOT_DIR = DATASETS_DIR / "nbiot"
UNSW_DIR = DATASETS_DIR / "unsw_raw"
UNSW_FILE = DATASETS_DIR / "unsw_nb15.csv"

# Hyperparameters
SAMPLE_FRACTION = 0.15          # To prevent memory issues with 11GB of N-BaIoT
RANDOM_STATE = 42

# Train/Val/Test Split (70/15/15)
TRAIN_SIZE = 0.70
VAL_SIZE = 0.15
TEST_SIZE = 0.15
