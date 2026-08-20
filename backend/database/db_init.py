from flask import Flask
from backend.database.db_models import db

def init_db(app: Flask):
    """
    Initialize the database with the Flask app context.
    """
    db.init_app(app)
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
