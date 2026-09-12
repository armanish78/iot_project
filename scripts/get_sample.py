import json
import numpy as np
import joblib

try:
    X_test = np.load('data/processed/X_test.npy', allow_pickle=True)
    with open('backend/models/feature_names.json', 'r') as f:
        feature_names = json.load(f)["features"]
        
    attack_raw = X_test[4] # Obvious attack
    
    packet = {}
    for idx, val in enumerate(attack_raw):
        packet[feature_names[idx]] = float(val)
    packet["source_ip"] = "192.168.1.100"
    packet["dest_ip"] = "10.0.0.1"
    
    with open('frontend/src/sample_packet.json', 'w') as f:
        json.dump(packet, f)
    print("Sample packet generated!")
except Exception as e:
    print(f"Error: {e}")
