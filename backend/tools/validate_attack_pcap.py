import sys
import os
import time
import numpy as np
import joblib
import nfstream

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.packet_capture_service import LiveFlowExtractor

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_attack_pcap.py <path_to_pcap>")
        return

    pcap_path = sys.argv[1]
    if not os.path.exists(pcap_path):
        print(f"File not found: {pcap_path}")
        return

    print(f"--- ATTACK VALIDATION ---")
    print(f"PCAP: {pcap_path}")

    # Load ML artifacts
    model_dir = os.path.join(PROJECT_ROOT, "backend", "models", "live_nfstream")
    try:
        model = joblib.load(os.path.join(model_dir, "final_xgboost_model.joblib"))
        scaler = joblib.load(os.path.join(model_dir, "scaler.joblib"))
        le = joblib.load(os.path.join(model_dir, "label_encoder.joblib"))
    except Exception as e:
        print(f"INFERENCE ERRORS: Failed to load models: {e}")
        return

    extractor = LiveFlowExtractor()

    print("Running NFStream over PCAP...")
    try:
        streamer = nfstream.NFStreamer(
            source=pcap_path,
            statistical_analysis=True,
            accounting_mode=1,
            active_timeout=60,
            idle_timeout=5
        )
    except Exception as e:
        print(f"INFERENCE ERRORS: NFStream failed: {e}")
        return

    flows = []
    total_packets = 0

    for flow in streamer:
        total_packets += flow.bidirectional_packets
        # Same extraction logic as live capture
        flow_data = extractor.extract_features_from_nfstream(flow)
        if flow_data:
            flows.append(flow_data)

    print(f"PACKETS: {total_packets}")
    print(f"FLOWS: {len(flows)}")

    if not flows:
        print("PREDICTIONS: 0")
        print("BENIGN: 0")
        print("ATTACK PREDICTIONS: 0")
        print("PREDICTED CLASSES: []")
        return

    vectors = np.array([f["vector"] for f in flows], dtype=np.float32)
    
    # Same scaling
    try:
        vectors_scaled = scaler.transform(vectors)
    except Exception as e:
        print(f"INFERENCE ERRORS: Scaler failed: {e}")
        return

    # Same inference
    try:
        probs = model.predict_proba(vectors_scaled)
        preds = np.argmax(probs, axis=1)
        pred_labels = le.inverse_transform(preds)
    except Exception as e:
        print(f"INFERENCE ERRORS: Model inference failed: {e}")
        return

    benign_count = sum(1 for p in pred_labels if p == "BENIGN")
    portscan_count = sum(1 for p in pred_labels if p == "PortScan")
    other_count = len(flows) - benign_count - portscan_count
    
    unique_attacks = list(set([p for p in pred_labels if p != "BENIGN"]))

    print(f"PREDICTIONS: {len(flows)}")
    print(f"BENIGN: {benign_count}")
    print(f"PORTSCAN: {portscan_count}")
    print(f"OTHER: {other_count}")
    
    recall = portscan_count / len(flows) if len(flows) > 0 else 0.0
    print(f"INFERENCE ERRORS: 0")
    print(f"PORTSCAN RECALL: {recall:.4f}")
    
    print("\nPROBABILITIES (Top 5 Attack Flows):")
    attack_flows_shown = 0
    for i, label in enumerate(pred_labels):
        if label != "BENIGN":
            max_prob = probs[i][preds[i]]
            print(f"  Flow {i+1} -> {label} (Prob: {max_prob:.4f})")
            attack_flows_shown += 1
            if attack_flows_shown >= 5:
                break
                
    if portscan_count > 0:
        print("\nATTACK TYPE: Validated")
    else:
        print("\nATTACK TYPE: None Detected")

if __name__ == "__main__":
    main()
