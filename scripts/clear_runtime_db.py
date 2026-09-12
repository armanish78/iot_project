import os
import sys

# Ensure backend directory is in the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.flask_api.app import create_app
from backend.database.db_init import init_db
from backend.database.db_models import db, Alert, Prediction

def clear_db():
    app = create_app('development')
    init_db(app)
    with app.app_context():
        # Alert has a foreign key to Prediction, so delete Alert first
        alerts_deleted = db.session.query(Alert).delete()
        predictions_deleted = db.session.query(Prediction).delete()
        
        db.session.commit()
        
        print(f"Cleanup successful.")
        print(f"Deleted Alerts: {alerts_deleted}")
        print(f"Deleted Predictions: {predictions_deleted}")

if __name__ == '__main__':
    clear_db()
