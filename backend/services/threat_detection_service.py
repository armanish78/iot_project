import pickle
import os
import uuid
from datetime import datetime
from backend.flask_api.config import Config
from backend.services.data_processor_service import processor_service
from backend.services.logging_service import logger_service
from backend.services.database_service import db_service

class ThreatDetectionService:
    def __init__(self):
        """Load models at startup"""
        self.rf_model = None
        self.if_model = None
        self.scaler = None
        
        try:
            if os.path.exists(Config.RANDOM_FOREST_MODEL):
                with open(Config.RANDOM_FOREST_MODEL, 'rb') as f:
                    self.rf_model = pickle.load(f)
            
            if os.path.exists(Config.ISOLATION_FOREST_MODEL):
                with open(Config.ISOLATION_FOREST_MODEL, 'rb') as f:
                    self.if_model = pickle.load(f)
            
            if os.path.exists(Config.FEATURE_SCALER):
                with open(Config.FEATURE_SCALER, 'rb') as f:
                    self.scaler = pickle.load(f)
                    
            logger_service.logger.info("Models loaded successfully")
        except Exception as e:
            logger_service.log_error(e, {"context": "Model loading in ThreatDetectionService"})
            print(f"Warning: Could not load models. {e}")
    
    def predict(self, data: dict) -> dict:
        """
        Make threat prediction on incoming traffic
        """
        try:
            # Preprocess
            scaled_features = processor_service.preprocess_input(data, self.scaler)
            
            rf_prediction = 0
            if_prediction = 1
            is_threat = False
            confidence = 0.0
            explanation = "Normal traffic pattern"
            threat_type = "none"
            
            # Predict
            if self.rf_model:
                rf_prediction = int(self.rf_model.predict(scaled_features)[0])
                if hasattr(self.rf_model, "predict_proba"):
                    probas = self.rf_model.predict_proba(scaled_features)[0]
                    confidence = float(max(probas))
                else:
                    confidence = 0.95
                    
            if self.if_model:
                if_prediction = int(self.if_model.predict(scaled_features)[0])
                
            # Logic: If RF predicts 1 (attack) OR IF predicts -1 (anomaly), it's a threat
            if rf_prediction == 1 or if_prediction == -1:
                is_threat = True
                
            if rf_prediction == 1 and if_prediction == -1:
                threat_type = "known_and_anomaly"
                explanation = "Known attack signature and highly anomalous behavior detected"
            elif rf_prediction == 1:
                threat_type = "known_attack"
                explanation = "Known attack signature detected by Random Forest"
            elif if_prediction == -1:
                threat_type = "zero_day_anomaly"
                explanation = "Unknown anomaly detected by Isolation Forest"
                
            prediction_result = {
                "threat": is_threat,
                "confidence": round(confidence, 2),
                "threat_type": threat_type,
                "explanation": explanation,
                "rf_prediction": rf_prediction,
                "if_prediction": if_prediction,
                "source_ip": data.get("source_ip", "unknown"),
                "dest_ip": data.get("dest_ip", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
            
            # Log
            logger_service.log_prediction(prediction_result)
            
            # Save to DB
            prediction_id = db_service.save_prediction(prediction_result)
            
            # Generate Alert if threat
            if is_threat:
                db_service.save_alert(prediction_id, severity="high")
                logger_service.log_alert({"prediction_id": prediction_id, "threat_type": threat_type})
                
            return prediction_result
            
        except Exception as e:
            logger_service.log_error(e, {"context": "Prediction making"})
            raise e

threat_service = ThreatDetectionService()
