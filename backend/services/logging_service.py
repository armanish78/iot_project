import logging
import os
from pathlib import Path

class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger('iot_security')
        self.logger.setLevel(logging.INFO)
        
        # Resolve log directory relative to this file's location:
        # logging_service.py lives at  backend/services/logging_service.py
        # logs/               lives at  backend/logs/
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / "predictions.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def log_prediction(self, prediction_data: dict):
        """Log prediction event"""
        self.logger.info(f"Prediction made: {prediction_data}")
    
    def log_alert(self, alert_data: dict):
        """Log alert event"""
        self.logger.warning(f"Alert generated: {alert_data}")
    
    def log_error(self, error: Exception, context: dict = None):
        """Log errors"""
        self.logger.error(f"Error occurred: {error}, Context: {context}")

# Create a singleton instance
logger_service = LoggingService()
