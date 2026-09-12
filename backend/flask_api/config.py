import os
from pathlib import Path

# Resolve the models directory relative to this file's location:
# config.py lives at  backend/flask_api/config.py
# models/  lives at   backend/models/
_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

class Config:
    """Base config"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    MODELS_DIR = str(_MODELS_DIR)
    RANDOM_FOREST_MODEL = str(_MODELS_DIR / "archive" / "random_forest_model.pkl")
    ISOLATION_FOREST_MODEL = str(_MODELS_DIR / "archive" / "isolation_forest_model.pkl")
    FEATURE_SCALER = str(_MODELS_DIR / "archive" / "scaler.pkl")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///iot_security.db'
    
class ProductionConfig(Config):
    """Production config"""
    DEBUG = False
    # Use postgres or other DB for prod
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///iot_security.db')

config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig
)
