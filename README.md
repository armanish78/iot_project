# IoT Threat Detection System

![Status](https://img.shields.io/badge/Status-Phase%201%20%26%202%20Complete-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-orange)

An advanced Artificial Intelligence system designed to protect Internet of Things (IoT) devices from botnet infections (like Mirai) using mathematical network traffic analysis. We have successfully implemented a way to monitor IoT network devices.

This repository contains the complete **Data Preprocessing Pipeline** and **Machine Learning Training Engine**.

---

## 🎯 Current Project Status
We have successfully completed the first two core phases of the project:

### Phase 1: Data Preprocessing (Completed)
- Ingested N-BaIoT and UNSW-NB15 cybersecurity datasets.
- Cleaned, engineered, and scaled 167 distinct network features.
- Applied SMOTE for mathematical class balancing to prevent AI bias.
- **Output Data Location**: All cleaned datasets are located in `data/processed/` as efficient `.npy` binary arrays.

### Phase 2: Machine Learning Engine (Completed)
- Designed a **Hybrid Pipeline** utilizing a Supervised model for known attacks and an Unsupervised model for Zero-Day anomaly detection.
- Performed Hyperparameter tuning (GridSearchCV) and applied Regularization to prevent overfitting.
- **Explainable AI (SHAP)** integration to provide human-readable reasoning for every alert.
- **Final Metrics**: Random Forest (95.5% Accuracy) | Isolation Forest (87.0% Accuracy).

---

## 🤖 The AI Models

### Where are the models located?
The fully trained, optimized, and serialized ML models are saved in the `backend/models/` directory:
- 🌲 **The Expert**: `backend/models/random_forest_model.pkl` (Detects known attacks)
- 🛡️ **The Guard Dog**: `backend/models/isolation_forest_model.pkl` (Detects zero-day anomalies)
- 📝 **Features List**: `backend/models/feature_names.json` (List of the 167 required features)

### How to access and use the models
You do not need to retrain these models. They are fully optimized and ready for inference (Phase 3 Integration).

To use the models in Python, load them using the standard `pickle` library:

```python
import pickle
import numpy as np

# 1. Load the finalized models
with open("backend/models/random_forest_model.pkl", "rb") as f:
    rf_model = pickle.load(f)

with open("backend/models/isolation_forest_model.pkl", "rb") as f:
    if_model = pickle.load(f)

# 2. Provide Network Traffic Data (Example 1D array of 167 features)
# This data must be scaled identically to Phase 1 preprocessing
sample_network_traffic = np.zeros((1, 167)) 

# 3. Make Predictions
rf_prediction = rf_model.predict(sample_network_traffic)

if rf_prediction[0] == 1:
    print("🚨 ALERT: Known Cyber Attack Detected!")
else:
    print("✅ Traffic appears normal.")
```

---

## 📊 SHAP Explainability & Predictions
For frontend UI integration, sample predictions showing exactly *why* the AI flagged an attack can be found in `backend/predictions/predictions.json`. This JSON provides a ready-to-use API payload for building dashboards.

## 📖 Detailed Walkthrough
For an extremely detailed, step-by-step breakdown of the exact algorithms and preprocessing steps used in this repository, please read the `walkthrough.md` file included in this project.
