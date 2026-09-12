import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, SCRIPT_DIR)

from backend.flask_api.app import create_app
from backend.database.db_models import db, Alert, Prediction
from backend.services.live_inference_service import live_inference_service
from backend.services.database_service import db_service

app = create_app('development')

with app.app_context():
    print("Clearing state")
    live_inference_service.clear_correlation_state()
    print("State:", live_inference_service.correlation_state)

    run_id = "DEBUG_RUN"
    
    # simulate 15 distinct ports
    for i in range(15):
        flow_data = {
            "vector": [0]*69,
            "meta": {
                "src_ip": "1.1.1.1",
                "dst_ip": "2.2.2.2",
                "src_port": 1234,
                "dst_port": 1000 + i,
                "protocol": 6
            }
        }
        
        # Mock predict
        prediction_result = {
            "source_ip": "1.1.1.1",
            "dest_ip": "2.2.2.2",
            "threat": True
        }
        explanation = {
            "dst_port": 1000 + i
        }
        # call save_prediction first
        prediction_id = db_service.save_prediction(prediction_result)
        
        # call the handler directly to see if it works
        live_inference_service._handle_correlation(prediction_id, prediction_result, explanation)
        print("State after", i, ":", live_inference_service.correlation_state)

    print("Alerts created?")
    # Check if any Alerts were saved (wait, save_alert would fail if pred-id isn't in DB because of foreign key?)
