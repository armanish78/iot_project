import sys
import os
import time
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from backend.flask_api.app import create_app
from backend.database.db_init import init_db
from backend.services.database_service import db_service
from backend.services.live_inference_service import live_inference_service
from backend.database.db_models import db, Prediction, Alert
from live_extractor import LiveFlowExtractor
import nfstream

def main():
    print("=== Sentinel DB Path BENIGN Validation ===")
    
    app = create_app('development')
    init_db(app)
    
    pcap_path = "benign_test.pcap"
    if not os.path.exists(pcap_path):
        print(f"PCAP not found: {pcap_path}")
        return
        
    print(f"Processing {pcap_path} through Sentinel DB path...")
    extractor = LiveFlowExtractor()
    
    with app.app_context():
        # Clear previous test data to ensure clean state
        db.session.query(Alert).delete()
        db.session.query(Prediction).delete()
        db.session.commit()
    
        streamer = nfstream.NFStreamer(
            source=pcap_path,
            statistical_analysis=True,
            accounting_mode=1,
            active_timeout=60,
            idle_timeout=5
        )
        
        run_id = f"VALIDATION-BENIGN-{int(time.time())}"
        processed_flows = 0
        
        # Process 5000 flows
        max_flows = 5000
        
        for flow in streamer:
            flow_data = extractor.extract_features_from_nfstream(flow)
            if flow_data:
                try:
                    # This internally calls db_service.save_prediction and db_service.save_alert
                    live_inference_service.predict(
                        flow_data["vector"],
                        flow_data["meta"],
                        run_id=run_id
                    )
                    processed_flows += 1
                except Exception as e:
                    print(f"Error: {e}")
                    
            if processed_flows >= max_flows:
                break
                
        print(f"Processed {processed_flows} flows through LiveInferenceService.")
        
        # Verify Database
        total_predictions = db.session.query(Prediction).filter_by(run_id=run_id).count()
        portscan_predictions = db.session.query(Prediction).filter_by(run_id=run_id, threat_type="PortScan").count()
        total_alerts = db.session.query(Alert).join(Prediction).filter(Prediction.run_id == run_id).count()
        
        print("\n--- BENIGN VALIDATION REPORT ---")
        print(f"Total flows: {total_predictions}")
        print(f"ML-positive candidates: {portscan_predictions}")
        print(f"Confirmed alerts: {total_alerts}")
        fpr = (total_alerts / total_predictions * 100) if total_predictions > 0 else 0
        print(f"Confirmed FPR: {fpr:.4f}%")
        
        if total_alerts > 0:
            print("\nFAILURE: Alerts were generated for benign traffic!")
            
            # Print a few sample alerts
            print("\nSample Alerts:")
            sample_alerts = db.session.query(Alert, Prediction).join(Prediction).filter(Prediction.run_id == run_id).limit(3).all()
            for alert, pred in sample_alerts:
                print(f"  Alert ID: {alert.id} | Severity: {alert.severity} | Threat: {pred.threat_type} | Conf: {pred.confidence} | Src: {pred.source_ip}")
        else:
            print("\nSUCCESS: No alerts were generated for benign traffic!")

if __name__ == "__main__":
    main()
