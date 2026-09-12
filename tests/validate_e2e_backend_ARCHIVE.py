import time
import json
import socket
import logging
from scapy.all import IP, TCP, UDP, conf, send
from backend.flask_api.app import create_app
from backend.services.packet_capture_service import packet_capture_service

# Reduce scapy logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

def run_e2e_test():
    print("=== LIVE BACKEND E2E TEST ===")
    
    app = create_app('development')
    client = app.test_client()
    
    from backend.database.db_init import init_db
    init_db(app)
    
    # 1. Identify Loopback
    loopback = conf.loopback_name
    print(f"Identified Loopback Interface: {loopback}")
    if not loopback:
        print("ERROR: Could not identify loopback interface.")
        return
        
    # 2. Start Capture via API
    print("\nStarting live capture via API...")
    res = client.post('/api/live/start', json={"interface": loopback})
    print(f"Start Response: {res.status_code} - {res.get_json()}")
    assert res.status_code == 200, "Failed to start capture"
    
    # 3. Verify Status
    res = client.get('/api/live/status')
    status = res.get_json()
    print(f"Status: {status}")
    assert status["running"] is True, "Capture is not running"
    assert status["interface"] == loopback, "Interface mismatch"
    
    # 4. Generate Localhost Traffic
    # Wait a moment for sniff to start
    time.sleep(2)
    print("\nGenerating synthetic localhost traffic...")
    
    # TCP Flow
    pkt1 = IP(src="127.0.0.1", dst="127.0.0.1", ttl=64) / TCP(sport=55555, dport=8080, flags="S") / ("hello")
    pkt2 = IP(src="127.0.0.1", dst="127.0.0.1", ttl=128) / TCP(sport=8080, dport=55555, flags="SA") / ("world")
    pkt3 = IP(src="127.0.0.1", dst="127.0.0.1", ttl=64) / TCP(sport=55555, dport=8080, flags="A") / ("ack")
    
    # Send using sockets or scapy send to localhost loopback
    # Note: On Windows, scapy send() to loopback requires Npcap loopback adapter
    # If Npcap is missing, this might fail or not be captured.
    try:
        send(pkt1, iface=loopback, verbose=False)
        send(pkt2, iface=loopback, verbose=False)
        send(pkt3, iface=loopback, verbose=False)
    except Exception as e:
        print(f"Warning: Failed to send via Scapy, using sockets. Error: {e}")
        # UDP fallback
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b"test udp packet", ("127.0.0.1", 9999))
        sock.close()
        
    print("\nTraffic generated. Waiting for idle timeout (5.0s) + buffer...")
    time.sleep(7.0)
    
    # 5. Check API Status again
    res = client.get('/api/live/status')
    status = res.get_json()
    print(f"\nPost-flush Status: {json.dumps(status, indent=2)}")
    
    # 6. Stop Capture
    print("\nStopping capture via API...")
    res = client.post('/api/live/stop')
    print(f"Stop Response: {res.status_code} - {res.get_json()}")
    assert res.status_code == 200, "Failed to stop capture"
    
    # 7. Check DB for predictions
    print("\nChecking database for generated predictions...")
    res = client.get('/api/predictions/?limit=10')
    preds = res.get_json()
    
    if preds is not None:
        print(f"Retrieved {len(preds)} predictions.")
        if len(preds) > 0:
            latest = preds[0]
            print(f"Latest Prediction: Threat={latest['threat']}, Conf={latest['confidence']}, Type={latest['threat_type']}")
            if "explanation" in latest:
                print(f"Explanation: {latest['explanation']}")
    else:
        print("WARNING: No predictions were generated. Capture may not have intercepted the packets, or Npcap loopback capture is not fully supported in this environment.")
        
    print("\n=== E2E TEST FINISHED ===")

if __name__ == "__main__":
    run_e2e_test()
