import json
import pickle
import numpy as np
from scapy.all import IP, TCP, UDP
from live_extractor import LiveFlowExtractor

def run_validation():
    print("Loading live model artifacts...")
    with open("backend/models/live/live_rf.pkl", "rb") as f:
        rf = pickle.load(f)
    with open("backend/models/live/live_if.pkl", "rb") as f:
        iso = pickle.load(f)
    with open("backend/models/live/live_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open("backend/models/live/live_feature_names.json", "r") as f:
        features = json.load(f)
        
    print(f"Feature count: {len(features)}")
    assert len(features) == 16, "Must be exactly 16 features!"
    print(f"Scaler expected features: {scaler.n_features_in_}")
    assert scaler.n_features_in_ == 16, "Scaler expects exactly 16 features!"
    print(f"RF expected features: {rf.n_features_in_}")
    assert rf.n_features_in_ == 16, "RF expects exactly 16 features!"
    
    # Check ordering
    expected_order = [
        "spkts", "dpkts", "sbytes", "dbytes", "dur", "sttl", "dttl",
        "smean", "dmean", "rate", "sload", "dload",
        "proto_tcp", "proto_udp", "proto_icmp", "proto_other"
    ]
    assert features == expected_order, "Feature ordering mismatch!"
    
    print("\nStarting synthetic flow extraction test...")
    extractor = LiveFlowExtractor(idle_timeout=5.0)
    
    # 1. Synthesize a TCP flow
    # Packet 1: SYN from A to B
    pkt1 = IP(src="192.168.1.10", dst="10.0.0.5", ttl=64) / TCP(sport=12345, dport=80, flags="S") / ("x" * 10)
    extractor.process_packet(pkt1, current_time=1.0)
    
    # Packet 2: SYN-ACK from B to A
    pkt2 = IP(src="10.0.0.5", dst="192.168.1.10", ttl=128) / TCP(sport=80, dport=12345, flags="SA") / ("y" * 10)
    extractor.process_packet(pkt2, current_time=1.5)
    
    # Packet 3: ACK from A to B
    pkt3 = IP(src="192.168.1.10", dst="10.0.0.5", ttl=64) / TCP(sport=12345, dport=80, flags="A") / ("z" * 20)
    extractor.process_packet(pkt3, current_time=2.0)
    
    # 2. Synthesize a UDP flow
    pkt_u1 = IP(src="192.168.1.10", dst="8.8.8.8", ttl=64) / UDP(sport=5353, dport=53) / ("a" * 5)
    extractor.process_packet(pkt_u1, current_time=2.5)
    
    # 3. Trigger flush
    extractor.flush_all_flows()
    
    print(f"\nExtracted {len(extractor.expired_flows)} flows.")
    
    for i, flow_data in enumerate(extractor.expired_flows):
        vector = flow_data["vector"]
        print(f"\nFlow {i+1} Vector:")
        for name, val in zip(features, vector):
            print(f"  {name}: {val}")
            
        assert len(vector) == 16, "Extracted vector must be length 16!"
        assert not np.isnan(vector).any(), "NaN found!"
        assert not np.isinf(vector).any(), "Inf found!"
        
        # Check one-hot
        proto_sum = sum(vector[12:16])
        assert proto_sum == 1, f"Protocol one-hot sum must be exactly 1! Got {proto_sum}"
        
        # Scale and predict
        vector_scaled = scaler.transform([vector])
        rf_pred = rf.predict(vector_scaled)[0]
        iso_pred = iso.predict(vector_scaled)[0]
        
        print(f"  -> RF Prediction: {rf_pred} (0=Benign, 1=Attack)")
        print(f"  -> ISO Prediction: {iso_pred} (1=Normal, -1=Anomaly)")
        
    print("\nSynthetic validation SUCCESSFUL!")

if __name__ == "__main__":
    run_validation()
