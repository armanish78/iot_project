import sys
import os
import time
import numpy as np
import joblib
from scapy.all import IP, TCP, UDP

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from live_extractor import LiveFlowExtractor

def main():
    print("--- CONTROLLED MULTI-PACKET VALIDATION ---")
    
    # Load 16-feature Production model
    prod_dir = os.path.join(SCRIPT_DIR, "..", "live")
    prod_clf = joblib.load(os.path.join(prod_dir, "live_rf.pkl"))
    prod_scaler = joblib.load(os.path.join(prod_dir, "live_scaler.pkl"))
    
    # Load 14-feature Candidate model
    cand_dir = os.path.join(SCRIPT_DIR, "rf_14f")
    cand_clf = joblib.load(os.path.join(cand_dir, "model.pkl"))
    cand_scaler = joblib.load(os.path.join(cand_dir, "scaler.pkl"))
    
    def evaluate_traffic(name, ground_truth, packets):
        extractor = LiveFlowExtractor()
        for pkt in packets:
            extractor.process_packet(pkt, current_time=time.time())
        extractor.flush_all_flows()
        
        flows = extractor.expired_flows
        print(f"\nScenario: {name}")
        print(f"Ground Truth: {ground_truth}")
        print(f"Packets Generated: {len(packets)}")
        print(f"Flows Generated: {len(flows)}")
        
        if not flows:
            return
            
        vecs_16 = np.array([f["vector"] for f in flows], dtype=np.float32)
        
        # Production
        vecs_16_scaled_prod = prod_scaler.transform(vecs_16)
        prod_probs = prod_clf.predict_proba(vecs_16_scaled_prod)[:, 1]
        prod_preds = (prod_probs >= 0.50).astype(int)
        
        # Candidate
        # The candidate scaler expects 16 features, then we slice to 14
        vecs_16_scaled_cand = cand_scaler.transform(vecs_16)
        idx_14 = [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        vecs_14_scaled_cand = vecs_16_scaled_cand[:, idx_14]
        cand_probs = cand_clf.predict_proba(vecs_14_scaled_cand)[:, 1]
        cand_preds = (cand_probs >= 0.80).astype(int)
        
        for i, f in enumerate(flows):
            print(f"  Flow {i+1}:")
            print(f"    Prod RF Prob: {prod_probs[i]:.4f} -> Pred: {'THREAT' if prod_preds[i]==1 else 'NORMAL'}")
            print(f"    Cand RF Prob: {cand_probs[i]:.4f} -> Pred: {'THREAT' if cand_preds[i]==1 else 'NORMAL'}")
            
    # 1. NORMAL TCP
    p_benign = []
    for _ in range(10):
        p_benign.append(IP(src="192.168.1.5", dst="8.8.8.8")/TCP(sport=12345, dport=443))
        p_benign.append(IP(src="8.8.8.8", dst="192.168.1.5")/TCP(sport=443, dport=12345))
    evaluate_traffic("NORMAL TCP", "KNOWN BENIGN", p_benign)

    # 2. HIGH-RATE / BURST
    p_udp = []
    for _ in range(500):
        p_udp.append(IP(src="192.168.1.5", dst="10.0.0.5")/UDP(sport=5555, dport=5555))
    evaluate_traffic("HIGH-RATE / BURST", "BEHAVIORAL VALIDATION", p_udp)
    
    # 3. EXISTING SUSPICIOUS (SYN Scan)
    p_scan = []
    for port in range(20, 100):
        p_scan.append(IP(src="192.168.1.5", dst="10.0.0.5")/TCP(sport=12345, dport=port, flags="S"))
    evaluate_traffic("SYN PORT SCAN", "SUSPICIOUS / ATTACK-LIKE", p_scan)
    
    # 4. MULTI-PACKET BIDIRECTIONAL CONNECTION
    p_multi = []
    for _ in range(50):
        p_multi.append(IP(src="192.168.1.10", dst="10.0.0.10")/TCP(sport=54321, dport=8080))
        p_multi.append(IP(src="10.0.0.10", dst="192.168.1.10")/TCP(sport=8080, dport=54321))
    evaluate_traffic("MULTI-PACKET BIDIRECTIONAL CONNECTION", "KNOWN BENIGN", p_multi)

if __name__ == "__main__":
    main()
