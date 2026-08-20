# PART 3: FLASK BACKEND API & REAL-TIME DETECTION
**Assigned to: Person 3**

**Branch:** `part-3-backend-api`

**GitHub Repo:** https://github.com/armanish78/iot_project.git

---

## 📋 Overview

Person 3 is responsible for building the **Flask REST API** that:
- Loads trained ML models from Part 2
- Receives network traffic data in real-time
- Runs threat detection on incoming data
- Logs all predictions and alerts
- Serves data to the React dashboard (Part 4)
- Handles database operations
- Implements authentication and security

---

## 📁 File Structure to Create

In your branch `part-3-backend-api`, create these files:

```
backend/
├── flask_api/
│   ├── __init__.py
│   ├── app.py                     # Flask app initialization
│   ├── config.py                  # Configuration (DB, models, etc)
│   └── routes/
│       ├── __init__.py
│       ├── health_routes.py       # Health check endpoint
│       ├── prediction_routes.py   # Real-time threat detection endpoint
│       ├── alert_routes.py        # Alert management endpoints
│       ├── dashboard_routes.py    # Data for dashboard visualization
│       └── log_routes.py          # Logging and history endpoints
│
├── services/
│   ├── __init__.py
│   ├── threat_detection_service.py  # Core threat detection logic
│   ├── database_service.py          # Database operations
│   ├── logging_service.py           # Logging and monitoring
│   └── data_processor_service.py    # Preprocess incoming data
│
├── models/
│   ├── __init__.py
│   ├── prediction_model.py        # Data model for predictions
│   ├── alert_model.py             # Data model for alerts
│   └── traffic_model.py           # Data model for traffic
│
├── database/
│   ├── __init__.py
│   ├── db_init.py                 # Database initialization
│   ├── db_models.py               # SQLAlchemy models
│   └── db_operations.py           # Database CRUD operations
│
├── logs/
│   ├── .gitkeep                   # Log files (don't commit)
│   └── predictions.log            # Output: Prediction logs
│
└── run.py                         # Flask app runner
```

---

## 🎯 Detailed Tasks

### Task 1: Flask App Initialization (`app.py`)

**What to build:**
- Initialize Flask application
- Set up CORS for React frontend communication
- Configure error handlers
- Register all blueprints (routes)

**Example function signatures:**
```python
from flask import Flask
from flask_cors import CORS

def create_app(config_name: str = 'development') -> Flask:
    """
    Application factory for Flask app
    
    Args:
        config_name: 'development', 'testing', or 'production'
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load config
    if config_name == 'development':
        app.config.from_object('config.DevelopmentConfig')
    elif config_name == 'production':
        app.config.from_object('config.ProductionConfig')
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from routes.health_routes import health_bp
    from routes.prediction_routes import prediction_bp
    from routes.alert_routes import alert_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.log_routes import log_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(log_bp)
    
    return app
```

**Expected Output:**
- Fully configured Flask app ready to handle requests

---

### Task 2: Configuration (`config.py`)

**What to build:**
- Configuration classes for different environments
- Database connection settings
- ML model paths
- API settings

**Example:**
```python
class Config:
    """Base config"""
    SECRET_KEY = 'your-secret-key'
    MODELS_DIR = 'backend/models/'
    RANDOM_FOREST_MODEL = 'backend/models/random_forest_model.pkl'
    ISOLATION_FOREST_MODEL = 'backend/models/isolation_forest_model.pkl'
    FEATURE_SCALER = 'backend/models/scaler.pkl'
    
class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///iot_security.db'
    
class ProductionConfig(Config):
    """Production config"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://...'  # Production DB
```

---

### Task 3: Routes - Health Check (`health_routes.py`)

**What to build:**
- Health check endpoint to verify API is running
- Check ML models are loaded
- Check database is connected

**Example function signatures:**
```python
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/status', methods=['GET'])
def health_status():
    """
    GET /api/health/status
    
    Returns:
        {
            "status": "healthy",
            "models_loaded": true,
            "database_connected": true,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    pass
```

**Expected Output:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "database_connected": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Task 4: Routes - Real-Time Threat Detection (`prediction_routes.py`)

**What to build:**
- Endpoint to receive network traffic data
- Call threat detection service
- Return prediction with explanation

**Example function signatures:**
```python
from flask import Blueprint, request, jsonify

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

@prediction_bp.route('/detect', methods=['POST'])
def detect_threat():
    """
    POST /api/predictions/detect
    
    Request body:
    {
        "source_ip": "192.168.1.100",
        "dest_ip": "8.8.8.8",
        "source_port": 45123,
        "dest_port": 53,
        "protocol": "UDP",
        "packet_size": 512,
        "packet_rate": 150,
        "flow_duration": 2.5,
        ... (other features from Part 1)
    }
    
    Returns:
    {
        "threat": true,
        "confidence": 0.92,
        "threat_type": "known_attack",
        "explanation": "High packet rate (35%) + suspicious port (28%)",
        "rf_prediction": 1,
        "if_prediction": -1,
        "timestamp": "2024-01-15T10:30:00Z",
        "request_id": "req-123456"
    }
    """
    data = request.get_json()
    
    # Validate input
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Process and predict
    # Call threat_detection_service.predict(data)
    # Log the prediction
    # Return result
    pass

@prediction_bp.route('/history', methods=['GET'])
def get_prediction_history():
    """
    GET /api/predictions/history?limit=100
    
    Returns recent predictions from database
    """
    pass
```

**Expected Output:**
```json
{
  "threat": true,
  "confidence": 0.92,
  "threat_type": "known_attack",
  "explanation": "High packet rate (35%) + suspicious destination port (28%) + abnormal flow duration (22%)",
  "rf_prediction": 1,
  "if_prediction": -1,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-123456"
}
```

---

### Task 5: Routes - Alert Management (`alert_routes.py`)

**What to build:**
- Endpoint to get active alerts
- Endpoint to acknowledge/resolve alerts
- Filter alerts by severity, time range, etc.

**Example function signatures:**
```python
from flask import Blueprint, request, jsonify

alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alert_bp.route('/', methods=['GET'])
def get_alerts():
    """
    GET /api/alerts?status=active&severity=high
    
    Returns list of alerts
    """
    pass

@alert_bp.route('/<alert_id>/acknowledge', methods=['PUT'])
def acknowledge_alert(alert_id: str):
    """
    PUT /api/alerts/{alert_id}/acknowledge
    
    Mark alert as acknowledged
    """
    pass

@alert_bp.route('/<alert_id>/resolve', methods=['PUT'])
def resolve_alert(alert_id: str):
    """
    PUT /api/alerts/{alert_id}/resolve
    
    Mark alert as resolved
    """
    pass
```

**Expected Output:**
```json
{
  "alerts": [
    {
      "alert_id": "alert-123",
      "threat": true,
      "confidence": 0.92,
      "source_ip": "192.168.1.100",
      "dest_ip": "8.8.8.8",
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "active",
      "severity": "high"
    }
  ]
}
```

---

### Task 6: Routes - Dashboard Data (`dashboard_routes.py`)

**What to build:**
- Endpoint for real-time network activity
- Endpoint for threat statistics
- Endpoint for timeline data

**Example function signatures:**
```python
from flask import Blueprint, request, jsonify

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    GET /api/dashboard/stats
    
    Returns summary statistics
    """
    pass

@dashboard_bp.route('/activity', methods=['GET'])
def get_live_activity():
    """
    GET /api/dashboard/activity?limit=50
    
    Returns recent network activity for live feed
    """
    pass

@dashboard_bp.route('/threat-timeline', methods=['GET'])
def get_threat_timeline():
    """
    GET /api/dashboard/threat-timeline?hours=24
    
    Returns threats over time (for charts)
    """
    pass
```

**Expected Output:**
```json
{
  "stats": {
    "total_connections": 45230,
    "threats_detected": 342,
    "threat_rate": 0.75,
    "top_threat_type": "known_attack",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

### Task 7: Routes - Logging (`log_routes.py`)

**What to build:**
- Endpoint to retrieve system logs
- Filter by date, severity, type
- Export logs

**Example function signatures:**
```python
from flask import Blueprint, request, jsonify

log_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@log_bp.route('/', methods=['GET'])
def get_logs():
    """
    GET /api/logs?severity=error&limit=100
    
    Returns system logs
    """
    pass

@log_bp.route('/export', methods=['GET'])
def export_logs():
    """
    GET /api/logs/export?format=csv&start_date=2024-01-01
    
    Export logs as CSV or JSON
    """
    pass
```

---

### Task 8: Threat Detection Service (`threat_detection_service.py`)

**What to build:**
- Load trained models from Part 2
- Preprocess incoming data using scaler from Part 1
- Call hybrid pipeline for prediction
- Format response with explanation

**Example function signatures:**
```python
import pickle
from backend.ml_models.hybrid_pipeline import hybrid_predict

class ThreatDetectionService:
    def __init__(self):
        """Load models at startup"""
        with open('backend/models/random_forest_model.pkl', 'rb') as f:
            self.rf_model = pickle.load(f)
        
        with open('backend/models/isolation_forest_model.pkl', 'rb') as f:
            self.if_model = pickle.load(f)
        
        with open('backend/models/scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)
    
    def predict(self, data: dict) -> dict:
        """
        Make threat prediction on incoming traffic
        
        Args:
            data: Network traffic features
            
        Returns:
            Prediction with explanation
        """
        pass
    
    def preprocess_input(self, data: dict) -> np.array:
        """Normalize incoming data using saved scaler"""
        pass
```

**Expected Output:**
Prediction dictionary with all required fields

---

### Task 9: Database Service (`database_service.py`)

**What to build:**
- Store predictions in database
- Store alerts
- Retrieve history
- CRUD operations

**Example function signatures:**
```python
from database.db_models import Prediction, Alert

class DatabaseService:
    
    def save_prediction(self, prediction_data: dict) -> str:
        """Save prediction to database, return prediction_id"""
        pass
    
    def save_alert(self, alert_data: dict) -> str:
        """Save alert to database, return alert_id"""
        pass
    
    def get_prediction_history(self, limit: int = 100):
        """Retrieve recent predictions"""
        pass
    
    def get_active_alerts(self) -> list:
        """Get unresolved alerts"""
        pass
    
    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        pass
```

---

### Task 10: Logging Service (`logging_service.py`)

**What to build:**
- Log all predictions
- Log errors
- Log API calls
- Structured logging

**Example function signatures:**
```python
import logging

class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger('iot_security')
        handler = logging.FileHandler('backend/logs/predictions.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_prediction(self, prediction_data: dict):
        """Log prediction event"""
        pass
    
    def log_alert(self, alert_data: dict):
        """Log alert event"""
        pass
    
    def log_error(self, error: Exception, context: dict):
        """Log errors"""
        pass
```

---

### Task 11: Database Models (`database/db_models.py`)

**What to build:**
- SQLAlchemy models for Prediction, Alert, Traffic
- Relationships between models
- Indexes for performance

**Example:**
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.String(36), primary_key=True)
    source_ip = db.Column(db.String(15))
    dest_ip = db.Column(db.String(15))
    threat = db.Column(db.Boolean)
    confidence = db.Column(db.Float)
    threat_type = db.Column(db.String(50))
    explanation = db.Column(db.Text)
    rf_prediction = db.Column(db.Integer)
    if_prediction = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.String(36), primary_key=True)
    prediction_id = db.Column(db.String(36), db.ForeignKey('predictions.id'))
    status = db.Column(db.String(20))  # active, acknowledged, resolved
    severity = db.Column(db.String(20))  # low, medium, high, critical
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

---

### Task 12: Main App Runner (`run.py`)

**What to build:**
- Entry point to run Flask app
- Initialize database
- Start server

**Example:**
```python
from backend.flask_api.app import create_app
from backend.database.db_init import init_db

if __name__ == '__main__':
    app = create_app('development')
    init_db(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

## 📊 Expected API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health/status` | Check API health |
| POST | `/api/predictions/detect` | Real-time threat detection |
| GET | `/api/predictions/history` | Prediction history |
| GET | `/api/alerts/` | Get alerts |
| PUT | `/api/alerts/<id>/acknowledge` | Acknowledge alert |
| PUT | `/api/alerts/<id>/resolve` | Resolve alert |
| GET | `/api/dashboard/stats` | Summary statistics |
| GET | `/api/dashboard/activity` | Live network activity |
| GET | `/api/dashboard/threat-timeline` | Threat timeline |
| GET | `/api/logs/` | System logs |
| GET | `/api/logs/export` | Export logs |

---

## 🛠️ Technologies & Libraries

```python
# Web Framework
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

# Database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

# ML Models
import pickle

# Utilities
import logging
import json
from datetime import datetime
from uuid import uuid4
import pandas as pd
import numpy as np
```

---

## 📝 Code Quality Requirements

- ✅ Docstrings for every route
- ✅ Error handling with proper HTTP status codes
- ✅ Input validation for all endpoints
- ✅ Structured logging
- ✅ Type hints

**Example:**
```python
from flask import Blueprint, request, jsonify

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

@prediction_bp.route('/detect', methods=['POST'])
def detect_threat():
    """
    Detect threat in network traffic.
    
    Request body:
        {
            "source_ip": str,
            "dest_ip": str,
            ... (traffic features)
        }
    
    Returns:
        {
            "threat": bool,
            "confidence": float,
            "explanation": str
        }
    
    Status codes:
        200: Success
        400: Bad request
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Process
        prediction = threat_detection_service.predict(data)
        
        return jsonify(prediction), 200
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Internal server error"}), 500
```

---

## ✅ Testing & Validation

Before pushing, verify:

- ✅ Flask app starts without errors
- ✅ All routes are accessible
- ✅ Models load correctly
- ✅ Database operations work
- ✅ Predictions return correct format
- ✅ Logging works properly

**Quick test using curl:**
```bash
# Test health endpoint
curl http://localhost:5000/api/health/status

# Test prediction
curl -X POST http://localhost:5000/api/predictions/detect \
  -H "Content-Type: application/json" \
  -d '{"source_ip":"192.168.1.1","dest_ip":"8.8.8.8",...}'
```

---

## 📅 Deliverables Checklist

- [ ] `backend/flask_api/app.py` - Flask app factory
- [ ] `backend/flask_api/config.py` - Configuration
- [ ] `backend/flask_api/routes/health_routes.py` - Health checks
- [ ] `backend/flask_api/routes/prediction_routes.py` - Threat detection
- [ ] `backend/flask_api/routes/alert_routes.py` - Alert management
- [ ] `backend/flask_api/routes/dashboard_routes.py` - Dashboard data
- [ ] `backend/flask_api/routes/log_routes.py` - Logging endpoints
- [ ] `backend/services/threat_detection_service.py` - Core detection
- [ ] `backend/services/database_service.py` - DB operations
- [ ] `backend/services/logging_service.py` - Structured logging
- [ ] `backend/services/data_processor_service.py` - Data preprocessing
- [ ] `backend/database/db_init.py` - Database initialization
- [ ] `backend/database/db_models.py` - SQLAlchemy models
- [ ] `backend/database/db_operations.py` - CRUD operations
- [ ] `backend/run.py` - App runner
- [ ] `requirements.txt` - Dependencies
- [ ] README with API documentation

---

## 🚀 How to Push to GitHub

Once complete:
```bash
git add .
git commit -m "Complete Flask API with threat detection and database"
git push origin part-3-backend-api
```

---

## 📞 Integration Notes

**Person 4 (React Dashboard)** will:
- Call `/api/dashboard/stats` for statistics
- Call `/api/dashboard/activity` for live feed
- Call `/api/dashboard/threat-timeline` for charts
- Call `/api/alerts/` to display alerts
- Handle WebSocket (optional) for real-time updates

Make sure your API responses match the expected format!

---

## 💾 Database Setup

The app will automatically:
1. Create SQLite database (`iot_security.db`) on first run
2. Create tables from SQLAlchemy models
3. Be ready to store predictions and alerts

For production, switch to PostgreSQL in config.

---

## Resources & Tips

- 📖 Flask Documentation: https://flask.palletsprojects.com/
- 📖 Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- 📖 RESTful API Design: https://restfulapi.net/
- 💡 **Tip:** Test each route individually before integration
- 💡 **Tip:** Use Postman or Insomnia to test API endpoints
- 💡 **Tip:** Enable logging early to debug issues

---

Good luck! Your API is the bridge between ML and frontend. 🌉🚀
