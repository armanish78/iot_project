from backend.database.db_models import db, Prediction, Alert
from datetime import datetime, timedelta

class DatabaseService:
    
    def save_prediction(self, prediction_data: dict) -> str:
        """Save prediction to database, return prediction_id"""
        new_prediction = Prediction(
            source_ip=prediction_data.get('source_ip', ''),
            dest_ip=prediction_data.get('dest_ip', ''),
            threat=prediction_data.get('threat', False),
            confidence=prediction_data.get('confidence', 0.0),
            threat_type=prediction_data.get('threat_type', 'normal'),
            explanation=prediction_data.get('explanation', ''),
            rf_prediction=prediction_data.get('rf_prediction', 0),
            if_prediction=prediction_data.get('if_prediction', 1)
        )
        db.session.add(new_prediction)
        db.session.commit()
        return new_prediction.id
    
    def save_alert(self, prediction_id: str, severity: str = 'medium') -> str:
        """Save alert to database, return alert_id"""
        new_alert = Alert(
            prediction_id=prediction_id,
            status='active',
            severity=severity
        )
        db.session.add(new_alert)
        db.session.commit()
        return new_alert.id
    
    def get_prediction_history(self, limit: int = 100):
        """Retrieve recent predictions"""
        predictions = Prediction.query.order_by(Prediction.timestamp.desc()).limit(limit).all()
        return [{
            "id": p.id,
            "source_ip": p.source_ip,
            "dest_ip": p.dest_ip,
            "threat": p.threat,
            "confidence": p.confidence,
            "threat_type": p.threat_type,
            "explanation": p.explanation,
            "timestamp": p.timestamp.isoformat()
        } for p in predictions]
    
    def get_active_alerts(self) -> list:
        """Get unresolved alerts"""
        alerts = db.session.query(Alert, Prediction).join(Prediction).filter(Alert.status == 'active').all()
        return [{
            "alert_id": a.Alert.id,
            "prediction_id": p.Prediction.id,
            "threat": p.Prediction.threat,
            "confidence": p.Prediction.confidence,
            "source_ip": p.Prediction.source_ip,
            "dest_ip": p.Prediction.dest_ip,
            "timestamp": a.Alert.timestamp.isoformat(),
            "status": a.Alert.status,
            "severity": a.Alert.severity
        } for a, p in alerts]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        alert = Alert.query.get(alert_id)
        if alert:
            alert.status = 'acknowledged'
            db.session.commit()
            return True
        return False
        
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        alert = Alert.query.get(alert_id)
        if alert:
            alert.status = 'resolved'
            db.session.commit()
            return True
        return False

# Singleton instance
db_service = DatabaseService()
