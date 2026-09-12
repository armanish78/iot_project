import sys
import os
import time
import json
import numpy as np
import joblib
from scapy.all import IP, TCP, UDP, ICMP

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from live_extractor import LiveFlowExtractor

def main():
    print("--- SYNTHETIC TRAFFIC VALIDATION ---")
    
    # Load 14-feature RF model
    model_dir = os.path.join(SCRIPT_DIR, "rf_14f")
    try:
        clf = joblib.load(os.path.join(model_dir, "model.pkl"))
        scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
        print(f"Loaded proposed model from {model_dir}")
    except Exception as e:
        print(f"Failed to load proposed model: {e}")
        return

    # To convert 16-feature scaled vectors to 14-feature scaled vectors
    # We must match the extractor logic exactly
    
    def evaluate_traffic(name, packets):
        extractor = LiveFlowExtractor()
        for pkt in packets:
            extractor.process_packet(pkt, current_time=time.time())
        extractor.flush_all_flows()
        
        flows = extractor.expired_flows
        print(f"\nScenario: {name} (Generated {len(packets)} packets -> {len(flows)} flows)")
        
        if not flows:
            return
            
        vecs_16 = np.array([f["vector"] for f in flows], dtype=np.float32)
        vecs_16_scaled = scaler.transform(vecs_16)
        
        # Extract 14 features (remove sttl=5, dttl=6)
        idx_14 = [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        vecs_14_scaled = vecs_16_scaled[:, idx_14]
        
        probs = clf.predict_proba(vecs_14_scaled)[:, 1]
        preds = (probs >= 0.80).astype(int)
        
        threat_count = preds.sum()
        print(f"  Detected Threats: {threat_count} / {len(flows)}")
        for i, f in enumerate(flows):
            print(f"    Flow {i+1}: RF Prob: {probs[i]:.4f} -> {'THREAT' if preds[i]==1 else 'NORMAL'} (spkts={f['vector'][0]}, dbytes={f['vector'][3]})")
            
        return flows, probs, preds

    # 1. Benign Traffic
    p_benign = []
    for _ in range(5):
        p_benign.append(IP(src="192.168.1.5", dst="8.8.8.8")/TCP(sport=12345, dport=443))
        p_benign.append(IP(src="8.8.8.8", dst="192.168.1.5")/TCP(sport=443, dport=12345))
    evaluate_traffic("Normal Web Traffic (Small)", p_benign)

    # 2. High-Rate UDP (often flagged as attack)
    p_udp = []
    for _ in range(500):
        p_udp.append(IP(src="192.168.1.5", dst="10.0.0.5")/UDP(sport=5555, dport=5555))
    evaluate_traffic("High-Rate UDP Burst", p_udp)
    
    # 3. Port Scan (Suspicious)
    p_scan = []
    for port in range(20, 100):
        p_scan.append(IP(src="192.168.1.5", dst="10.0.0.5")/TCP(sport=12345, dport=port, flags="S"))
    evaluate_traffic("SYN Port Scan", p_scan)
    
    # 4. Large Data Exfiltration (Suspicious)
    p_exfil = []
    for _ in range(1000):
        p_exfil.append(IP(src="192.168.1.5", dst="185.15.15.15")/TCP(sport=12345, dport=80, flags="PA")/("X"*1400))
    evaluate_traffic("Data Exfiltration", p_exfil)

if __name__ == "__main__":
    main()
