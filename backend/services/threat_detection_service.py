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
        import json
        self.rf_model = None
        self.if_model = None
        self.scaler = None
        self.if_top_indices = None
        self.if_threshold = 0.0
        
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
                    
            feature_names_path = os.path.join(os.path.dirname(Config.RANDOM_FOREST_MODEL), "feature_names.json")
            if os.path.exists(feature_names_path):
                with open(feature_names_path, 'r') as f:
                    data = json.load(f)
                    if "if_top_indices" in data and data["if_top_indices"]:
                        self.if_top_indices = data["if_top_indices"]
                    if "if_threshold" in data:
                        self.if_threshold = float(data["if_threshold"])
                        
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
                scaled_features_if = scaled_features
                if self.if_top_indices is not None:
                    scaled_features_if = scaled_features[:, self.if_top_indices]
                
                score = self.if_model.decision_function(scaled_features_if)[0]
                if_prediction = -1 if score < self.if_threshold else 1
                
                # Mathematically derive a legitimate confidence score from the IF anomaly score
                # The further below the threshold, the more confident the anomaly.
                if if_prediction == -1:
                    distance = abs(score - self.if_threshold)
                    # Scale distance into a confidence bump (e.g., distance of 0.015 adds 15%)
                    # Base anomaly confidence starts at 75%
                    if_confidence = min(0.99, 0.75 + (distance * 10))
                else:
                    if_confidence = 0.0
                
            # Logic: RF Uncertainty Override
            rf_conf = confidence
            if rf_conf >= 0.70 or rf_conf <= 0.50:
                is_threat = (rf_prediction == 1)
            else:
                is_threat = (if_prediction == -1)
                if is_threat:
                    # Apply legitimate calculated IF confidence
                    confidence = if_confidence
                
            if rf_prediction == 1 and if_prediction == -1:
                threat_type = "known_and_anomaly"
                explanation = "Known attack signature and highly anomalous behavior detected"
                # Take highest confidence between RF and IF
                confidence = max(rf_conf, if_confidence) 
            elif rf_prediction == 1:
                threat_type = "known_attack"
                explanation = "Known attack signature detected by Random Forest"
            elif if_prediction == -1:
                threat_type = "zero_day_anomaly"
                explanation = "Unknown anomaly detected by Isolation Forest"
                confidence = if_confidence
            else:
                threat_type = "none"
                explanation = "Normal traffic pattern"
                
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
