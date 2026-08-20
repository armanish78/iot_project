from backend.database.db_models import db, Prediction, Alert
from datetime import datetime

# We will implement CRUD operations in the database_service directly or call these helpers
# Let's keep this as a placeholder for low level ops if needed or just empty it out since
# database_service.py usually handles this.

def save_to_db(instance):
    try:
        db.session.add(instance)
        db.session.commit()
        return instance.id
    except Exception as e:
        db.session.rollback()
        raise e
