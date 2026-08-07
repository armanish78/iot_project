# PART 1: DATA PREPROCESSING & FEATURE ENGINEERING
**Assigned to: Person 1**

**Branch:** `part-1-data-preprocessing`

**GitHub Repo:** https://github.com/armanish78/iot_project.git

---

## 📋 Overview

Person 1 is responsible for building the **data pipeline** that:
- Downloads and loads datasets (N-BaIoT, UNSW-NB15)
- Cleans and preprocesses raw data
- Extracts relevant features for threat detection
- Balances imbalanced classes using SMOTE
- Outputs clean, normalized datasets ready for ML models

---

## 📁 File Structure to Create

In your branch `part-1-data-preprocessing`, create these files:

```
data/
├── preprocessing/
│   ├── __init__.py
│   ├── data_loader.py          # Load N-BaIoT and UNSW-NB15
│   ├── data_cleaner.py         # Clean and preprocess data
│   ├── feature_extractor.py    # Extract relevant features
│   ├── feature_scaling.py      # Normalize/scale features
│   ├── class_balancing.py      # SMOTE for imbalanced data
│   └── pipeline.py             # Main preprocessing pipeline
│
├── datasets/
│   ├── README.md               # Instructions to download datasets
│   ├── .gitkeep                # Placeholder (datasets stay local)
│   └── sample_data.csv         # (Optional) Small sample for testing
│
└── outputs/
    ├── processed_train.csv     # Output: Training data (clean)
    ├── processed_test.csv      # Output: Test data (clean)
    └── feature_info.json       # Output: Feature metadata
```

---

## 🎯 Detailed Tasks

### Task 1: Data Loader (`data_loader.py`)

**What to build:**
- Function to download N-BaIoT dataset
- Function to download UNSW-NB15 dataset
- Load both datasets into pandas DataFrames
- Combine datasets with proper labeling

**Example function signatures:**
```python
def load_nbiot_dataset(path: str) -> pd.DataFrame:
    """Load N-BaIoT dataset"""
    pass

def load_unsw_dataset(path: str) -> pd.DataFrame:
    """Load UNSW-NB15 dataset"""
    pass

def combine_datasets(nbiot_df: pd.DataFrame, unsw_df: pd.DataFrame) -> pd.DataFrame:
    """Combine both datasets"""
    pass
```

**Expected Output:**
- DataFrame with all traffic records
- Columns: `source_ip`, `dest_ip`, `protocol`, `packet_size`, `duration`, `label`, etc.
- Label column: 0 = Normal, 1 = Attack

---

### Task 2: Data Cleaner (`data_cleaner.py`)

**What to build:**
- Remove duplicate rows
- Handle missing values (NaN, null)
- Remove irrelevant columns
- Data validation
- Fix data types

**Example function signatures:**
```python
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate records"""
    pass

def handle_missing_values(df: pd.DataFrame, strategy: str = 'drop') -> pd.DataFrame:
    """Handle NaN and null values"""
    pass

def remove_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove columns not useful for ML"""
    pass

def validate_data(df: pd.DataFrame) -> bool:
    """Validate data integrity"""
    pass
```

**Expected Output:**
- Clean DataFrame without duplicates or missing values
- Only relevant columns remain

---

### Task 3: Feature Extractor (`feature_extractor.py`)

**What to build:**
- Extract network traffic features from raw data
- Features to extract (from project docs):
  - Packet size statistics (min, max, mean, std)
  - Protocol type (TCP, UDP, etc.)
  - Byte count
  - Flow duration
  - Source/destination ports
  - Packet rate
  - Inter-arrival time
  - Flow statistics

**Example function signatures:**
```python
def extract_packet_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Extract packet size stats"""
    pass

def extract_flow_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract flow-based features"""
    pass

def extract_protocol_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode protocol types"""
    pass

def extract_timing_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract inter-arrival time and duration"""
    pass
```

**Expected Output:**
- DataFrame with engineered features
- Example: `packet_size_mean`, `packet_size_std`, `flow_duration`, `packet_rate`, etc.

---

### Task 4: Feature Scaling (`feature_scaling.py`)

**What to build:**
- Normalize numerical features (0-1 scale)
- Standardize features (mean=0, std=1)
- Handle categorical features (one-hot encoding if needed)

**Example function signatures:**
```python
def normalize_features(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Normalize to 0-1 range using MinMaxScaler"""
    pass

def standardize_features(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Standardize using StandardScaler (z-score)"""
    pass

def encode_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categorical columns"""
    pass
```

**Expected Output:**
- DataFrame with scaled/normalized features
- All features on same scale for fair ML training

---

### Task 5: Class Balancing (`class_balancing.py`)

**What to build:**
- Check class imbalance (normal vs attack traffic)
- Apply SMOTE (Synthetic Minority Oversampling Technique)
- Balance attack and normal classes

**Example function signatures:**
```python
def check_class_balance(df: pd.DataFrame, label_col: str) -> dict:
    """Check class distribution"""
    pass

def apply_smote(X: pd.DataFrame, y: pd.Series) -> tuple:
    """Apply SMOTE to balance classes"""
    pass

def get_balanced_dataset(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """Return balanced dataset"""
    pass
```

**Expected Output:**
- Balanced dataset with equal attack/normal samples
- Prevents model bias toward majority class

---

### Task 6: Main Pipeline (`pipeline.py`)

**What to build:**
- Orchestrate all preprocessing steps
- Load → Clean → Extract Features → Scale → Balance
- Save output files
- Log processing steps

**Example function signatures:**
```python
def run_preprocessing_pipeline(nbiot_path: str, unsw_path: str, output_dir: str):
    """
    Main pipeline orchestrator
    1. Load datasets
    2. Clean data
    3. Extract features
    4. Scale features
    5. Balance classes
    6. Save outputs
    """
    pass
```

**Expected Output:**
- `processed_train.csv` (training data, ready for ML)
- `processed_test.csv` (test data, ready for ML)
- `feature_info.json` (metadata about features)

---

## 📊 Input Datasets

### N-BaIoT Dataset
- **Download:** https://archive.ics.uci.edu/ml/datasets/n_BaIoT
- Contains: IoT device traffic infected with Mirai, Bashlite
- Attack types: UDP flood, TCP flood, ACK flood, scanning

### UNSW-NB15 Dataset
- **Download:** https://research.unsw.edu.au/projects/unsw-nb15-dataset
- Contains: Modern network intrusion traffic
- Attack types: DoS, exploits, worms, reconnaissance, backdoors

**Note:** You'll need to download these manually and place in `data/datasets/`

---

## 📤 Expected Output Files

### 1. `processed_train.csv`
```
packet_size_mean,packet_size_std,flow_duration,packet_rate,...,label
0.45,0.12,2.34,15.6,...,0
0.89,0.34,5.67,45.2,...,1
...
```

### 2. `processed_test.csv`
Same format, different records (for testing)

### 3. `feature_info.json`
```json
{
  "total_features": 45,
  "feature_names": ["packet_size_mean", "flow_duration", ...],
  "feature_types": {"numeric": 40, "categorical": 5},
  "class_distribution": {"normal": 50000, "attack": 50000},
  "preprocessing_steps": [
    "removed_duplicates",
    "handled_missing_values",
    "extracted_features",
    "scaled_features",
    "applied_smote"
  ]
}
```

---

## 🛠️ Technologies & Libraries

```python
# Core
import pandas as pd
import numpy as np

# Preprocessing
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from imblearn.over_sampling import SMOTE

# Data handling
import csv
import json
```

---

## 📝 Code Quality Requirements

- ✅ Add docstrings to every function
- ✅ Add type hints (`def func(x: int) -> str:`)
- ✅ Handle errors with try-except
- ✅ Add logging for each preprocessing step
- ✅ Create requirements.txt with dependencies

**Example:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_nbiot_dataset(path: str) -> pd.DataFrame:
    """
    Load N-BaIoT dataset from CSV.
    
    Args:
        path: Path to N-BaIoT CSV file
        
    Returns:
        DataFrame with IoT traffic data
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    try:
        logger.info(f"Loading N-BaIoT dataset from {path}")
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} records")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
```

---

## ✅ Testing & Validation

Before pushing to GitHub, test that:

- ✅ All datasets load without errors
- ✅ No NaN or null values remain
- ✅ Features are properly extracted
- ✅ Data is scaled between 0-1 (or normalized)
- ✅ Classes are balanced (roughly equal attack/normal)
- ✅ Output CSVs can be loaded by Part 2 (ML models)

**Quick test:**
```python
# Load and validate
df_train = pd.read_csv('data/outputs/processed_train.csv')
print(df_train.shape)        # Should have many rows, ~45 columns
print(df_train.describe())   # Check statistics
print(df_train['label'].value_counts())  # Should be roughly equal
```

---

## 📅 Deliverables Checklist

- [ ] `data/preprocessing/data_loader.py` - Load datasets
- [ ] `data/preprocessing/data_cleaner.py` - Clean data
- [ ] `data/preprocessing/feature_extractor.py` - Extract features
- [ ] `data/preprocessing/feature_scaling.py` - Scale features
- [ ] `data/preprocessing/class_balancing.py` - Balance classes
- [ ] `data/preprocessing/pipeline.py` - Main orchestrator
- [ ] `data/outputs/processed_train.csv` - Training data (ready for ML)
- [ ] `data/outputs/processed_test.csv` - Test data (ready for ML)
- [ ] `data/outputs/feature_info.json` - Feature metadata
- [ ] `requirements.txt` - List all dependencies
- [ ] README with instructions to run the pipeline

---

## 🚀 How to Push to GitHub

Once complete:
```bash
git add .
git commit -m "Complete data preprocessing pipeline"
git push origin part-1-data-preprocessing
```

---

## 📞 Integration Notes

**Person 2 (ML Models)** will consume:
- `processed_train.csv` - For training Random Forest & Isolation Forest
- `processed_test.csv` - For testing models
- Feature names from `feature_info.json`

Make sure the output format is exactly what they expect!

---

## Resources & Tips

- 📖 Pandas Documentation: https://pandas.pydata.org/docs/
- 📖 Scikit-learn Preprocessing: https://scikit-learn.org/stable/modules/preprocessing.html
- 📖 SMOTE Documentation: https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html
- 💡 **Tip:** Start with a small sample of data (1000 rows) to test your pipeline before running on full datasets
- 💡 **Tip:** Save intermediate outputs to debug issues

---

Good luck! Your work is critical to the entire project. 🚀
