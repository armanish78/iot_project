import os

class Config:
    """Base config"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    MODELS_DIR = 'backend/models/'
    RANDOM_FOREST_MODEL = 'backend/models/random_forest_model.pkl'
    ISOLATION_FOREST_MODEL = 'backend/models/isolation_forest_model.pkl'
    FEATURE_SCALER = 'backend/models/scaler.pkl'
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
