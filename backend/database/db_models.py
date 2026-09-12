from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    source_ip = db.Column(db.String(15))
    dest_ip = db.Column(db.String(15))
    threat = db.Column(db.Boolean)
    confidence = db.Column(db.Float)
    threat_type = db.Column(db.String(50))
    explanation = db.Column(db.Text)
    rf_prediction = db.Column(db.Integer)
    if_prediction = db.Column(db.Integer)
    run_id = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    prediction_id = db.Column(db.String(36), db.ForeignKey('predictions.id'))
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
