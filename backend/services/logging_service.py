import logging
import os

class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger('iot_security')
        self.logger.setLevel(logging.INFO)
        
        # Ensure logs directory exists
        log_dir = 'backend/logs'
        os.makedirs(log_dir, exist_ok=True)
        
        handler = logging.FileHandler(os.path.join(log_dir, 'predictions.log'))
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
