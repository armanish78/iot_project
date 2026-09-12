import time
import json
import logging
from backend.flask_api.app import create_app
from backend.services.packet_capture_service import packet_capture_service

# Reduce scapy logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def run_e2e_pcap_test():
    print("=== LIVE BACKEND E2E PCAP TEST ===")
    
    app = create_app('development')
    client = app.test_client()
    
    from backend.database.db_init import init_db
    init_db(app)
    
    pcap_file = "portscan_test.pcap"
    
    # 2. Start Capture via API using PCAP as interface
    print(f"\nStarting live capture via API on {pcap_file}...")
    res = client.post('/api/live/start', json={"interface": pcap_file})
    print(f"Start Response: {res.status_code} - {res.get_json()}")
    assert res.status_code == 200, "Failed to start capture"
    
    # 3. Wait for processing
    print("\nWaiting for NFStream to process PCAP in background...")
    time.sleep(15.0) # give it some time to process
    
    # 5. Check API Status again
    res = client.get('/api/live/status')
    status = res.get_json()
    print(f"\nPost-processing Status: {json.dumps(status, indent=2)}")
    
    # 6. Stop Capture
    print("\nStopping capture via API...")
    res = client.post('/api/live/stop')
    print(f"Stop Response: {res.status_code} - {res.get_json()}")
    
    # 7. Check DB for predictions
    print("\nChecking database for generated alerts...")
    res = client.get('/api/predictions/?limit=200')
    preds = res.get_json()
    
    if preds is not None:
        print(f"Retrieved {len(preds)} predictions.")
        portscan_count = sum(1 for p in preds if p.get('threat_type') == 'PortScan')
        print(f"Found {portscan_count} PortScan predictions in DB!")
        
        if len(preds) > 0:
            latest = [p for p in preds if p.get('threat')][:5]
            print(f"Latest 5 Threat Predictions:")
            for p in latest:
                print(f"  Threat={p['threat']}, Conf={p['confidence']}, Type={p['threat_type']}, Src={p['source_ip']}, Dst={p['dest_ip']}")
    else:
        print("WARNING: No predictions were generated.")
        
    print("\n=== E2E PCAP TEST FINISHED ===")

if __name__ == "__main__":
    run_e2e_pcap_test()
