# 🛡️ IoT Secure — AI-Powered IoT Threat Detection System

![Status](https://img.shields.io/badge/Status-Working%20MVP-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB)
![Flask](https://img.shields.io/badge/Backend-Flask-black)
![Machine Learning](https://img.shields.io/badge/ML-scikit--learn-orange)
![Explainable AI](https://img.shields.io/badge/XAI-SHAP-purple)
![Database](https://img.shields.io/badge/Database-SQLite-blue)

> An end-to-end AI-powered cybersecurity system for detecting known and zero-day IoT network threats using a hybrid Random Forest + Isolation Forest architecture with SHAP explainability and a real-time security dashboard.

---

## 📌 Overview

**IoT Secure** is a machine-learning-based IoT threat detection system designed to identify malicious network traffic associated with botnets and other network attacks.

The system combines:

- **Random Forest** for known attack detection
- **Isolation Forest** for anomaly and zero-day detection
- **Hybrid ensemble logic** to combine both models
- **SHAP** for explainable AI
- **Flask REST API** for real-time inference
- **SQLite** for prediction and alert storage
- **React + TypeScript** for the cybersecurity dashboard

The project processes network traffic represented by **167 behavioral features**, sends the data through the hybrid ML inference pipeline, stores the resulting security events, and exposes them through a web-based security operations dashboard.

---

# 🎯 Problem

IoT devices are frequently targeted by automated attacks and botnets such as **Mirai**.

Traditional security systems often rely on predefined signatures or rules. This creates two major problems:

1. Known attacks can be detected, but new variants may bypass predefined rules.
2. Aggressive detection rules can produce large numbers of false positives.

IoT Secure addresses this using a **hybrid machine learning architecture**:

```text
Known Attack Detection
        +
Zero-Day Anomaly Detection
        +
Explainable AI
        ↓
Comprehensive IoT Threat Detection
```

## 🧠 Core Architecture
```text
                     IoT Network Traffic
                              │
                              ▼
                     ┌─────────────────┐
                     │   Flask REST    │
                     │      API        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Data Processor  │
                     │                 │
                     │ Validation      │
                     │ Missing Values  │
                     │ Scaling         │
                     └────────┬────────┘
                              │
                       167 Features
                              │
                              ▼
                  ┌────────────────────────┐
                  │    Hybrid ML Engine    │
                  │                        │
                  │ ┌────────────────────┐ │
                  │ │   Random Forest    │ │
                  │ │  Known Attacks     │ │
                  │ └─────────┬──────────┘ │
                  │           │            │
                  │ ┌─────────▼──────────┐ │
                  │ │  Isolation Forest  │ │
                  │ │ Zero-Day Anomalies │ │
                  │ └─────────┬──────────┘ │
                  │           │            │
                  │     Ensemble Logic    │
                  └───────────┬────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │    SHAP     │
                       │ Explainable │
                       │     AI      │
                       └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │   SQLite    │
                       │  Database   │
                       └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Flask JSON  │
                       │  Response   │
                       └──────┬──────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   React Web Dashboard   │
                 │                         │
                 │ Dashboard               │
                 │ Alerts                  │
                 │ Prediction              │
                 └─────────────────────────┘
```

## 🤖 Machine Learning System

### 1. Random Forest — Known Attack Detection

The Random Forest classifier is the supervised component of the system.

**Purpose**

Detect attacks that resemble patterns seen during training.

**Configuration**
- Algorithm:       Random Forest
- Trees:           150
- Maximum Depth:   7
- Training Data:   114,963 samples

The model uses an ensemble of decision trees to classify network traffic as normal or malicious.

**Standalone Performance**
| Metric | Score |
| --- | --- |
| Accuracy | 92.52% |
| Precision | 91.30% |
| Recall | 93.45% |
| F1 Score | 92.36% |

### 🛡️ 2. Isolation Forest — Zero-Day Detection

Isolation Forest is the unsupervised component of the system.

Instead of learning attack signatures, it learns the characteristics of normal traffic and identifies unusual behavior.

**Purpose**

Detect previously unseen or anomalous traffic patterns.

**Configuration**
- Algorithm:       Isolation Forest
- Trees:           200
- Training Data:   Normal traffic only
- Contamination:   0.01

The model works on the most important selected features rather than compressing the original feature space with PCA.

**Standalone Performance**
| Metric | Score |
| --- | --- |
| Accuracy | 87.00% |
| Precision | 84.20% |
| Recall | 89.50% |
| F1 Score | 86.80% |

### 🔀 3. Hybrid Ensemble

The system combines Random Forest and Isolation Forest through an RF Uncertainty Override mechanism.

The basic decision logic is:

```text
RF confidence >= 70%
        ↓
Trust Random Forest

RF confidence <= 50%
        ↓
Trust Random Forest

RF confidence between 50–70%
        ↓
Use Isolation Forest
```

The goal is to use Random Forest when it is confident while allowing the anomaly detector to resolve uncertain cases.

**Hybrid Performance**
| Metric | Performance |
| --- | --- |
| Accuracy | 97.48% |
| Precision | 95.20% |
| Recall | 95.68% |
| F1 Score | 95.44% |
| False Positive Reduction | 69% |

### 🔍 Explainable AI with SHAP

Machine learning predictions are often difficult to interpret.

IoT Secure integrates SHAP (SHapley Additive exPlanations) to provide information about the features contributing to individual predictions.

**Example:**
```json
{
  "is_threat": true,
  "explanation": "Detected anomalous packet behavior",
  "top_contributing_features": [
    {
      "name": "dst_port_count",
      "contribution": 0.45
    },
    {
      "name": "pkt_rate",
      "contribution": 0.38
    },
    {
      "name": "entropy",
      "contribution": 0.32
    }
  ]
}
```
The web dashboard visualizes these feature contributions so users can understand why a traffic sample was classified as a threat.

## 📊 Data Pipeline

The ML system was trained using:

- N-BaIoT
- UNSW-NB15

The combined dataset contains approximately:

- 165,721 network records
- 167 behavioral features

### Preprocessing Pipeline
```text
Raw Datasets
     ↓
Dataset Loading
     ↓
Data Cleaning
     ↓
Duplicate Removal
     ↓
Missing Value Handling
     ↓
Feature Engineering
     ↓
Feature Scaling
     ↓
Train / Validation / Test Split
     ↓
SMOTE Class Balancing
     ↓
Processed NumPy Arrays
```

### Feature Categories

The 167 features represent different aspects of network behavior, including:

- packet rates
- byte rates
- flow duration
- idle time
- packet sizes
- inter-packet timing
- port diversity
- protocol ratios
- TCP flags
- entropy
- skewness
- kurtosis
- retransmission behavior
- connection patterns

### ⚖️ SMOTE Class Balancing

The raw dataset contains an imbalance between normal and attack traffic.

SMOTE (Synthetic Minority Over-sampling Technique) is used to generate synthetic minority-class samples.

The resulting training data is balanced to prevent the models from simply favoring the majority class.

## 🌐 Backend

The backend is implemented using Flask.

It provides:

- REST API endpoints
- ML inference
- preprocessing
- SHAP explanations
- database operations
- alert management
- logging
- health monitoring

### Backend Structure
```text
backend/
├── ml_models/
│   ├── random_forest_model.py
│   ├── isolation_forest_model.py
│   ├── hybrid_pipeline.py
│   ├── shap_explainer.py
│   ├── model_trainer.py
│   └── model_evaluator.py
│
├── services/
│   ├── threat_detection_service.py
│   ├── data_processor_service.py
│   ├── logging_service.py
│   └── database_service.py
│
├── flask_api/
│   ├── app.py
│   ├── config.py
│   └── routes/
│       ├── health_routes.py
│       ├── prediction_routes.py
│       ├── alert_routes.py
│       ├── dashboard_routes.py
│       └── log_routes.py
│
├── database/
│   ├── db_models.py
│   ├── db_init.py
│   └── db_operations.py
│
├── models/
│   ├── random_forest_model.pkl
│   ├── isolation_forest_model.pkl
│   ├── feature_names.json
│   └── scaler.pkl
│
├── logs/
├── predictions/
└── run.py
```

### 🔌 API

The frontend communicates directly with the Flask backend.

The currently integrated frontend routes are:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/health/status` | GET | Backend/system health |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/dashboard/activity` | GET | Recent network activity |
| `/api/alerts/` | GET | Security alerts |
| `/api/predictions/detect` | POST | Run ML threat detection |

The frontend uses the actual API responses and does not rely on mock security data.

## 🖥️ Frontend

The project includes a React-based cybersecurity dashboard.

**Technology**
- React
- TypeScript
- Vite
- Tailwind CSS
- Axios

The interface is designed as a Security Operations Center-style dashboard rather than a conventional IoT device-control application.

### 📱 Frontend Features

#### Dashboard

The dashboard provides an overview of the current security state.

It displays:
- system health
- total scans
- detected threats
- threat rate
- recent network activity
- traffic status

#### Alerts

The Alerts page retrieves real security alerts from the backend.

Information may include:
- timestamp
- threat type
- confidence
- severity
- acknowledgement state

Threats are visually categorized into appropriate security states.

#### Prediction

The Prediction page allows the user to run the existing ML detection pipeline.

The frontend sends a genuine network traffic feature vector to: `POST /api/predictions/detect`

The result is displayed with:
- threat status
- confidence
- threat type
- detection engine
- explanation
- top contributing features

The project includes a genuine test packet generated from the processed test dataset for API testing.

No fabricated prediction results are used for the prediction workflow.

## 🗄️ Database

The backend uses SQLite for lightweight persistent storage.

Database location: `instance/iot_security.db`

### Predictions
Stores prediction results including:
- id
- packet_id
- timestamp
- threat_detected
- confidence
- threat_type
- explanation
- top_features

### Alerts
Security alerts contain information such as:
- id
- prediction_id
- severity
- acknowledged
- response_action
- timestamp

## 📝 Logging

Runtime events are stored under: `backend/logs/`

The system records events such as:
- model initialization
- prediction requests
- threat detections
- API errors
- inference timing

## 📁 Project Structure
```text
iot_project/
│
├── backend/
│   ├── ml_models/
│   ├── services/
│   ├── flask_api/
│   ├── database/
│   ├── models/
│   ├── logs/
│   ├── predictions/
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Alerts.tsx
│   │   │   └── Prediction.tsx
│   │   ├── App.tsx
│   │   └── ...
│   │
│   ├── sample_packet.json
│   ├── package.json
│   └── vite.config.ts
│
├── config/
│   └── preprocessing_config.py
│
├── data/
│   ├── preprocessing/
│   ├── processed/
│   └── logs/
│
├── main_preprocessing.py
├── main_training.py
├── test_api.py
├── requirements.txt
├── README.md
├── doc.md
└── iot_preprocessing_pipeline.ipynb
```

## 🚀 Installation

### Prerequisites
Make sure you have:
- Python 3.11+
- Node.js
- npm

### ⚙️ Backend Setup
Clone the repository:
```bash
git clone https://github.com/armanish78/iot_project.git
cd iot_project
```
Create and activate the Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
Install Python dependencies:
```bash
pip install -r requirements.txt
```
Start the Flask backend:
```bash
python3 backend/run.py
```
The backend runs on: `http://localhost:5000`

### 💻 Frontend Setup
Open another terminal:
```bash
cd frontend
```
Install dependencies:
```bash
npm install
```
Start the development server:
```bash
npm run dev
```
The Vite development server will provide a local URL, typically: `http://localhost:5173`

## 🔗 Running the Complete System

Start the backend:
```bash
source venv/bin/activate
python3 backend/run.py
```
Then start the frontend:
```bash
cd frontend
npm run dev
```
Open the frontend in your browser.

## 🧪 API Testing
The repository includes:
`test_api.py`
which can be used to test the backend prediction system.

The prediction pipeline expects a network traffic representation containing the required 167 features.

## 📈 Performance
The current ML evaluation reports:
- Hybrid Accuracy:              97.48%
- Hybrid Precision:             95.20%
- Hybrid Recall:                95.68%
- Hybrid F1 Score:              95.44%
- False Positive Reduction:     69%
- Average Inference:            ~15 ms
- Approx. Throughput:           ~67 predictions/sec

Model memory footprint is approximately:
- Random Forest:       ~45 MB
- Isolation Forest:    ~22 MB
- Other artifacts:     ~5 KB
- Total:               ~70 MB

## 🧩 Technology Stack
- **Machine Learning**: Python, NumPy, Pandas, scikit-learn, Random Forest, Isolation Forest, GridSearchCV, SMOTE
- **Explainable AI**: SHAP
- **Backend**: Flask, Flask-CORS, Flask-SQLAlchemy
- **Database**: SQLite
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Axios

## ⚠️ Current Limitations
The current system has several limitations:

1. **Fixed Feature Requirement**: The ML pipeline expects the required 167-feature representation.
2. **Dataset Age**: The models were trained using historical cybersecurity datasets.
3. **Model Drift**: The current system does not automatically perform model drift detection.
4. **SQLite Scalability**: A larger production deployment would benefit from PostgreSQL.
5. **Real-Time Network Capture**: A production deployment would require a dedicated network traffic/feature extraction layer.

## 🔮 Future Improvements
**Phase 4 — Production Deployment**
Docker containerization, cloud deployment, API authentication, rate limiting, production database

**Phase 5 — Advanced Detection**
model drift detection, temporal traffic analysis, active learning, human-in-the-loop feedback

**Phase 6 — Advanced ML**
XGBoost, LightGBM, LSTM/sequence models

**Phase 7 — Advanced Dashboard**
real-time streaming updates, advanced threat analytics, historical attack visualization

## 🏆 Key Features
- ✅ Hybrid supervised + unsupervised threat detection
- ✅ Random Forest for known attacks
- ✅ Isolation Forest for anomaly detection
- ✅ Zero-day threat detection capability
- ✅ RF uncertainty override
- ✅ SHAP explainability
- ✅ 167 behavioral network features
- ✅ SMOTE class balancing
- ✅ Flask REST API
- ✅ SQLite persistence
- ✅ Security alert logging
- ✅ React cybersecurity dashboard
- ✅ Real frontend-to-backend integration

## 🔐 Security Note
This project is intended for research, education, experimentation, and controlled cybersecurity environments. The current configuration is designed for local development and demonstration.

## 📚 Documentation
Additional project documentation includes:
- `README.md`
- `doc.md`
- `iot_preprocessing_pipeline.ipynb`
- `test_api.py`

`doc.md` contains the more detailed technical breakdown of the project architecture and implementation.

## 👨‍💻 Project Status
- Phase 1 — Data Preprocessing       ✅ Complete
- Phase 2 — ML Training              ✅ Complete
- Phase 3 — Flask Backend/API        ✅ Complete
- Frontend MVP                       ✅ Complete
- Frontend ↔ Backend Integration     ✅ Working
- Production Deployment              ⏳ Future
- Advanced Real-Time Pipeline        ⏳ Future

## 📌 Summary
IoT Secure combines machine learning, cybersecurity, explainable AI, backend engineering, database persistence, and web development into a single end-to-end system.

## ⭐ Project Highlights
- 97.48%     Hybrid Accuracy
- 95.44%     Hybrid F1 Score
- 95.68%     Threat Recall
- 69%        False Positive Reduction
- 167        Network Features
- 150        Random Forest Trees
- 200        Isolation Forest Trees
- ~15 ms     Average Inference

Built as an end-to-end IoT cybersecurity and machine learning project.
