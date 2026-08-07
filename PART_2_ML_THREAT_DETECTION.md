# PART 2: ML THREAT DETECTION & EXPLAINABILITY
**Assigned to: Person 2**

**Branch:** `part-2-ml-threat-detection`

**GitHub Repo:** https://github.com/armanish78/iot_project.git

---

## 📋 Overview

Person 2 is responsible for building the **ML threat detection system** that:
- Trains Random Forest model (supervised learning for known attacks)
- Trains Isolation Forest model (unsupervised learning for unknown attacks)
- Combines both models in a hybrid pipeline
- Integrates SHAP for explainable AI
- Generates threat explanations for every detection
- Saves trained models for deployment

---

## 📁 File Structure to Create

In your branch `part-2-ml-threat-detection`, create these files:

```
backend/
├── ml_models/
│   ├── __init__.py
│   ├── random_forest_model.py     # Supervised learning (known attacks)
│   ├── isolation_forest_model.py  # Unsupervised learning (unknown attacks)
│   ├── model_trainer.py           # Train both models
│   ├── model_evaluator.py         # Evaluate accuracy, precision, recall, F1
│   ├── shap_explainer.py          # SHAP explanations
│   └── hybrid_pipeline.py         # Combine both models
│
├── models/
│   ├── .gitkeep                   # Placeholder (actual models go here)
│   ├── random_forest_model.pkl    # Output: Trained RF model
│   ├── isolation_forest_model.pkl # Output: Trained IF model
│   ├── scaler.pkl                 # Output: Feature scaler
│   └── feature_names.json         # Output: Feature metadata
│
└── predictions/
    ├── predictions.json           # Output: All predictions with explanations
    └── evaluation_report.json     # Output: Accuracy, precision, recall, F1
```

---

## 🎯 Detailed Tasks

### Task 1: Random Forest Model (`random_forest_model.py`)

**What to build:**
- Train Random Forest classifier on labeled data
- Use supervised learning to classify known attack patterns
- Optimize hyperparameters
- Calculate confidence scores

**Example function signatures:**
```python
def create_random_forest(n_estimators: int = 100, random_state: int = 42) -> RandomForestClassifier:
    """Create Random Forest model"""
    pass

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series, model) -> RandomForestClassifier:
    """Train Random Forest on labeled data"""
    pass

def predict_with_rf(model, X_test: pd.DataFrame) -> tuple:
    """
    Make predictions with confidence scores
    
    Returns:
        (predictions, confidence_scores)
    """
    pass

def get_feature_importance(model, feature_names: list) -> dict:
    """Get which features are most important for decisions"""
    pass
```

**Expected Output:**
- Trained model that can classify normal vs attack traffic
- Confidence scores (0-1 probability)
- Feature importance rankings

**Hyperparameters to tune:**
- `n_estimators`: 100-500 (number of trees)
- `max_depth`: 10-50 (tree depth)
- `min_samples_split`: 2-10
- `random_state`: 42 (for reproducibility)

---

### Task 2: Isolation Forest Model (`isolation_forest_model.py`)

**What to build:**
- Train Isolation Forest for anomaly detection
- Unsupervised learning to detect unknown/zero-day attacks
- No labeled data required
- Identify outliers in network traffic

**Example function signatures:**
```python
def create_isolation_forest(contamination: float = 0.1, random_state: int = 42) -> IsolationForest:
    """Create Isolation Forest for anomaly detection"""
    pass

def train_isolation_forest(X_train: pd.DataFrame, model) -> IsolationForest:
    """Train on data (no labels needed)"""
    pass

def predict_anomalies(model, X_test: pd.DataFrame) -> tuple:
    """
    Detect anomalies
    
    Returns:
        (predictions, anomaly_scores)
        predictions: -1 (anomaly), 1 (normal)
        anomaly_scores: higher = more anomalous
    """
    pass
```

**Expected Output:**
- Model that identifies unusual traffic patterns
- Anomaly scores for each sample
- Detects unseen/zero-day attacks

**Hyperparameters:**
- `contamination`: 0.05-0.2 (expected proportion of attacks)
- `n_estimators`: 100-200
- `random_state`: 42

---

### Task 3: Model Trainer (`model_trainer.py`)

**What to build:**
- Load preprocessed data from Part 1
- Split into train/test sets
- Train Random Forest model
- Train Isolation Forest model
- Save both trained models to disk

**Example function signatures:**
```python
def load_processed_data(train_path: str, test_path: str) -> tuple:
    """Load Part 1 outputs"""
    pass

def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
    """Split into train/test"""
    pass

def train_all_models(X_train, y_train, X_test, y_test):
    """
    Train both RF and IF models
    
    Returns:
        (rf_model, if_model)
    """
    pass

def save_models(rf_model, if_model, output_dir: str):
    """Save trained models as .pkl files"""
    pass
```

**Expected Output:**
- `random_forest_model.pkl` - Trained Random Forest
- `isolation_forest_model.pkl` - Trained Isolation Forest
- `scaler.pkl` - Feature scaler for production
- `feature_names.json` - Feature metadata

---

### Task 4: Model Evaluator (`model_evaluator.py`)

**What to build:**
- Evaluate both models on test data
- Calculate performance metrics
- Generate confusion matrix
- Create evaluation report

**Example function signatures:**
```python
def evaluate_model(y_true: pd.Series, y_pred: np.array) -> dict:
    """
    Calculate metrics
    
    Returns:
        {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.94,
            "f1_score": 0.935,
            "roc_auc": 0.98
        }
    """
    pass

def get_confusion_matrix(y_true, y_pred) -> np.array:
    """Get confusion matrix for visualization"""
    pass

def generate_evaluation_report(rf_metrics: dict, if_metrics: dict, output_path: str):
    """Save evaluation report as JSON"""
    pass
```

**Metrics to calculate:**
- Accuracy: Overall correctness
- Precision: True positives / (True positives + False positives)
- Recall: True positives / (True positives + False negatives)
- F1-Score: Harmonic mean of precision and recall
- ROC-AUC: Area under ROC curve

**Expected Output:**
```json
{
  "random_forest": {
    "accuracy": 0.95,
    "precision": 0.93,
    "recall": 0.94,
    "f1_score": 0.935,
    "roc_auc": 0.98
  },
  "isolation_forest": {
    "accuracy": 0.88,
    "precision": 0.85,
    "recall": 0.90,
    "f1_score": 0.875,
    "roc_auc": 0.92
  }
}
```

---

### Task 5: SHAP Explainer (`shap_explainer.py`)

**What to build:**
- Integrate SHAP (SHapley Additive exPlanations)
- Explain why each connection was flagged as attack
- Identify most important features contributing to prediction
- Generate human-readable explanations

**Example function signatures:**
```python
def create_shap_explainer(model, X_train: pd.DataFrame):
    """Create SHAP explainer for model"""
    pass

def get_feature_importance(explainer, X_sample: pd.DataFrame) -> dict:
    """
    Get SHAP values for a sample
    
    Returns:
        {
            "predicted_class": "attack",
            "confidence": 0.92,
            "top_contributing_features": [
                {"feature": "packet_rate", "contribution": 0.35},
                {"feature": "dest_port", "contribution": 0.28},
                {"feature": "flow_duration", "contribution": 0.22}
            ],
            "explanation": "High packet rate + suspicious destination port + abnormal flow duration indicate attack"
        }
    """
    pass

def generate_explanation(shap_values, feature_names: list, instance: pd.Series) -> str:
    """Generate human-readable explanation"""
    pass
```

**Expected Output:**
- SHAP values for each prediction
- Ranked feature importance
- Natural language explanations like:
  ```
  "Connection flagged as ATTACK with 92% confidence because:
   1. High packet rate (35% contribution)
   2. Suspicious destination port (28% contribution)
   3. Abnormal flow duration (22% contribution)"
  ```

**Libraries:**
```python
import shap
import matplotlib.pyplot as plt
```

---

### Task 6: Hybrid Pipeline (`hybrid_pipeline.py`)

**What to build:**
- Combine Random Forest + Isolation Forest predictions
- Implement voting strategy
- Decision logic for final threat classification
- Generate final prediction with explanation

**Example function signatures:**
```python
def hybrid_predict(rf_model, if_model, shap_explainer, X_sample: pd.DataFrame) -> dict:
    """
    Make prediction using both models
    
    Logic:
    1. Get RF prediction (knows attacks)
    2. Get IF prediction (knows anomalies)
    3. If RF says "attack" -> Threat (high confidence)
    4. If IF says "anomaly" -> Threat (zero-day)
    5. If both agree -> Very high confidence
    6. Get SHAP explanation
    
    Returns:
        {
            "threat": True/False,
            "confidence": 0.92,
            "threat_type": "known_attack" | "zero_day" | "normal",
            "rf_prediction": 1,
            "if_prediction": -1,
            "explanation": "High packet rate indicates..."
        }
    """
    pass

def ensemble_voting(rf_pred: int, if_pred: int) -> tuple:
    """
    Decision logic
    RF: 0 (normal), 1 (attack)
    IF: 1 (normal), -1 (anomaly)
    
    Returns: (final_prediction, confidence, threat_type)
    """
    pass
```

**Decision Matrix:**
| RF Prediction | IF Prediction | Threat Type | Confidence |
|---|---|---|---|
| Attack (1) | Anomaly (-1) | Known Attack | Very High (95%+) |
| Normal (0) | Normal (1) | Normal | Very High (95%+) |
| Attack (1) | Normal (1) | Known Attack | High (80-95%) |
| Normal (0) | Anomaly (-1) | Zero-Day/Unknown | Medium-High (70-85%) |

---

## 📊 Training Data Input

Person 1 provides:
- `data/outputs/processed_train.csv` - Balanced training data
- `data/outputs/processed_test.csv` - Test data
- `data/outputs/feature_info.json` - Feature metadata

**Expected columns:**
```
packet_size_mean, packet_size_std, flow_duration, packet_rate, 
dest_port, source_port, protocol, byte_count, inter_arrival_time, ..., label
```

---

## 📤 Expected Output Files

### 1. `backend/models/random_forest_model.pkl`
Serialized trained Random Forest model

### 2. `backend/models/isolation_forest_model.pkl`
Serialized trained Isolation Forest model

### 3. `backend/models/scaler.pkl`
Feature scaler for normalizing new data

### 4. `backend/models/feature_names.json`
```json
{
  "features": ["packet_size_mean", "packet_size_std", ...],
  "num_features": 45,
  "model_version": "1.0"
}
```

### 5. `backend/predictions/evaluation_report.json`
Model performance metrics

### 6. `backend/predictions/predictions.json`
Sample predictions with explanations:
```json
{
  "predictions": [
    {
      "sample_id": 1,
      "features": {...},
      "threat": true,
      "confidence": 0.92,
      "threat_type": "known_attack",
      "explanation": "High packet rate (35%) + suspicious port (28%) + abnormal duration (22%)",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    ...
  ]
}
```

---

## 🛠️ Technologies & Libraries

```python
# ML Models
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Explainability
import shap

# Utilities
import pickle
import json
import pandas as pd
import numpy as np
```

---

## 📝 Code Quality Requirements

- ✅ Docstrings for every function
- ✅ Type hints
- ✅ Error handling
- ✅ Logging for training steps
- ✅ Model version tracking

**Example:**
```python
import logging
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """
    Train Random Forest classifier on labeled IoT traffic data.
    
    Args:
        X_train: Feature matrix (n_samples, n_features)
        y_train: Labels (0=normal, 1=attack)
        
    Returns:
        Trained RandomForestClassifier model
        
    Raises:
        ValueError: If data dimensions don't match
    """
    try:
        logger.info(f"Training Random Forest with {len(X_train)} samples")
        model = RandomForestClassifier(n_estimators=200, max_depth=30, random_state=42)
        model.fit(X_train, y_train)
        logger.info("Random Forest training complete")
        return model
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
```

---

## ✅ Testing & Validation

Before pushing, verify:

- ✅ Both models train without errors
- ✅ Accuracy >= 85% (on test data)
- ✅ SHAP explanations are generated correctly
- ✅ Trained models can be loaded and used for predictions
- ✅ Hybrid pipeline combines predictions correctly
- ✅ Output JSON files are valid

**Quick test:**
```python
# Load and test
with open('backend/models/random_forest_model.pkl', 'rb') as f:
    rf_model = pickle.load(f)

# Make prediction
sample = X_test.iloc[0:1]
pred = rf_model.predict(sample)
confidence = rf_model.predict_proba(sample)
print(f"Prediction: {pred[0]}, Confidence: {confidence[0]}")
```

---

## 📅 Deliverables Checklist

- [ ] `backend/ml_models/random_forest_model.py` - RF implementation
- [ ] `backend/ml_models/isolation_forest_model.py` - IF implementation
- [ ] `backend/ml_models/model_trainer.py` - Training orchestrator
- [ ] `backend/ml_models/model_evaluator.py` - Evaluation metrics
- [ ] `backend/ml_models/shap_explainer.py` - SHAP integration
- [ ] `backend/ml_models/hybrid_pipeline.py` - Hybrid predictions
- [ ] `backend/models/random_forest_model.pkl` - Trained RF model
- [ ] `backend/models/isolation_forest_model.pkl` - Trained IF model
- [ ] `backend/models/scaler.pkl` - Feature scaler
- [ ] `backend/models/feature_names.json` - Feature metadata
- [ ] `backend/predictions/evaluation_report.json` - Performance metrics
- [ ] `backend/predictions/predictions.json` - Sample predictions
- [ ] `requirements.txt` - All dependencies
- [ ] README with instructions

---

## 🚀 How to Push to GitHub

Once complete:
```bash
git add .
git commit -m "Complete ML threat detection with SHAP explainability"
git push origin part-2-ml-threat-detection
```

---

## 📞 Integration Notes

**Person 3 (Backend API)** will use:
- `backend/models/random_forest_model.pkl`
- `backend/models/isolation_forest_model.pkl`
- `hybrid_pipeline.py` for real-time predictions

**Person 4 (Dashboard)** will use:
- Predictions with explanations from hybrid pipeline
- Confidence scores
- SHAP explanations

Make sure your output format matches what they expect!

---

## 🎯 Performance Targets

Aim for:
- **Accuracy:** >= 90%
- **Precision:** >= 85% (minimize false positives)
- **Recall:** >= 85% (catch most attacks)
- **F1-Score:** >= 0.87
- **ROC-AUC:** >= 0.95

---

## Resources & Tips

- 📖 Scikit-learn RF: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- 📖 Scikit-learn IF: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- 📖 SHAP Documentation: https://shap.readthedocs.io/
- 💡 **Tip:** Use SHAP summary plots to visualize feature importance
- 💡 **Tip:** Test on small dataset first before full training
- 💡 **Tip:** Save model versions (v1.0, v1.1, v2.0) for tracking

---

Good luck! Your models are the brain of the system. 🧠🚀
