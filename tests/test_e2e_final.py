import time
import json
import socket
import logging
from backend.flask_api.app import create_app
from backend.database.db_init import init_db
from backend.database.db_models import db, Prediction, Alert

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def run_e2e_test():
    print("=== LIVE BACKEND E2E VALIDATION ===")
    
    app = create_app('development')
    client = app.test_client()
    
    with app.app_context():
        init_db(app)
        
    loopback = "Loopback Pseudo-Interface 1"
    
    print("\n1. Verify GET /api/health/status")
    res = client.get('/api/health/status')
    print(f"   Status: {res.status_code}")
    print(f"   Body: {res.get_json()}")

    print("\n2. Start live capture on loopback")
    res = client.post('/api/live/start', json={"interface": loopback})
    print(f"   Status: {res.status_code}")
    print(f"   Body: {res.get_json()}")

    print("\n3. Verify /api/live/status reports running=true")
    res = client.get('/api/live/status')
    status = res.get_json()
    print(f"   Status: {res.status_code}")
    print(f"   Body: {status}")
    
    print("\n4. Generating LOCALHOST TCP and UDP traffic...")
    time.sleep(2)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"E2E UDP TEST", ("127.0.0.1", 12345))
        sock.close()
        print("   Generated UDP packet.")
    except Exception as e:
        print(f"   Failed to generate UDP: {e}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect(("127.0.0.1", 12346))
        except:
            pass
        sock.close()
        print("   Generated TCP packet.")
    except Exception as e:
        print(f"   Failed to generate TCP: {e}")
        
    print("\n5. Waiting for configured idle timeout (5s) + buffer...")
    time.sleep(8)
    
    print("\n6. Verify status again for stats")
    res = client.get('/api/live/status')
    status = res.get_json()
    print(f"   Status: {res.status_code}")
    print(f"   Body: {json.dumps(status, indent=2)}")
    
    print("\n7. Verify API Retrieval")
    res = client.get('/api/predictions/?limit=5')
    print(f"   /api/predictions/ Response: {res.status_code} - {len(res.get_json() or [])} records")
    res = client.get('/api/alerts/')
    print(f"   /api/alerts/ Response: {res.status_code} - {len(res.get_json() or [])} records")
    
    print("\n8. Direct SQLite Database Check")
    with app.app_context():
        preds = Prediction.query.order_by(Prediction.timestamp.desc()).limit(5).all()
        print(f"   Found {len(preds)} predictions in DB:")
        for p in preds:
            print(f"     ID: {p.id}")
            print(f"     Timestamp: {p.timestamp}")
            print(f"     Source IP: {p.source_ip}")
            print(f"     Destination IP: {p.dest_ip}")
            print(f"     Predicted Label: {p.threat_type}")
            print(f"     RF Confidence: {p.confidence}")
            print(f"     RF Prediction: {p.rf_prediction}")
            print(f"     IF Prediction: {p.if_prediction}")
            alert = Alert.query.filter_by(prediction_id=p.id).first()
            print(f"     Associated Alert ID: {alert.id if alert else 'None'}")
            print("     ---")
            
        alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
        print(f"\n   Found {len(alerts)} alerts in DB:")
        for a in alerts:
            print(f"     ID: {a.id}, Severity: {a.severity}, Prediction ID: {a.prediction_id}")
            
    print("\n9. Stop capture")
    res = client.post('/api/live/stop')
    print(f"   Status: {res.status_code}")
    print(f"   Body: {res.get_json()}")
    
    print("\n10. Verify duplicate start handling")
    client.post('/api/live/start', json={"interface": loopback})
    res = client.post('/api/live/start', json={"interface": loopback})
    print(f"   Second Start Status: {res.status_code}")
    print(f"   Second Start Body: {res.get_json()}")
    client.post('/api/live/stop')
    
    print("\n=== E2E TEST COMPLETED ===")

if __name__ == "__main__":
    run_e2e_test()
