import requests
import json
import time
import numpy as np
import joblib

def run_test():
    print("🚀 Preparing Real Simulation Packets from Dataset...")
    
    try:
        # Load dataset, scaler, and feature names
        X_test = np.load('data/processed/X_test.npy', allow_pickle=True)
        y_test = np.load('data/processed/y_test.npy', allow_pickle=True)
        scaler = joblib.load('data/processed/scaler.pkl')
        
        with open('backend/models/feature_names.json', 'r') as f:
            feature_names = json.load(f)["features"]
    except Exception as e:
        print(f"❌ Error loading dataset files: {e}")
        return
        
    # Pick specific packets from the dataset to demonstrate our system's capabilities:
    # (These indices were pre-calculated to showcase specific edge cases)
    normal1_idx = 0     # A very obvious normal packet
    normal2_idx = 1     # Another normal packet
    attack1_idx = 4     # An obvious known attack
    attack2_idx = 9     # Another known attack
    sneak1_idx = 22754  # SNEAK ATTACK: RF misses this (56% confidence), but IF overrides!
    sneak2_idx = 23286  # SNEAK ATTACK: RF misses this (51% confidence), but IF overrides!
    
    # Extract and scale them back to raw data
    normal1_raw = X_test[normal1_idx]
    normal2_raw = X_test[normal2_idx]
    attack1_raw = X_test[attack1_idx]
    attack2_raw = X_test[attack2_idx]
    sneak1_raw = X_test[sneak1_idx]
    sneak2_raw = X_test[sneak2_idx]
    
    def build_packet(raw_values):
        packet = {}
        for idx, val in enumerate(raw_values):
            packet[feature_names[idx]] = float(val)
        packet["source_ip"] = "192.168.1.100"
        packet["dest_ip"] = "10.0.0.1"
        return packet
        
    test_cases = [
        {
            "description": "Test 1: REAL Normal Traffic",
            "expected": "Normal (Threat: False)",
            "packet": build_packet(normal1_raw)
        },
        {
            "description": "Test 2: REAL Normal Traffic (Alternative pattern)",
            "expected": "Normal (Threat: False)",
            "packet": build_packet(normal2_raw)
        },
        {
            "description": "Test 3: REAL Obvious Attack",
            "expected": "Blocked (RF should catch this easily)",
            "packet": build_packet(attack1_raw)
        },
        {
            "description": "Test 4: REAL Obvious Attack 2",
            "expected": "Blocked (RF should catch this easily)",
            "packet": build_packet(attack2_raw)
        },
        {
            "description": "Test 5: REAL Sneak Attack (Zero-Day Simulation)",
            "expected": "Blocked (RF will miss this, but the Isolation Forest should catch it)",
            "packet": build_packet(sneak1_raw)
        },
        {
            "description": "Test 6: REAL Sneak Attack 2 (Highly evasive)",
            "expected": "Blocked (Testing if the Hybrid System can flag it)",
            "packet": build_packet(sneak2_raw)
        }
    ]
    
    url = "http://localhost:5000/api/predictions/detect"
    
    print("✅ Packets built successfully! Sending to Live API...\n")
    
    for idx, case in enumerate(test_cases, 1):
        print(f"==================================================")
        print(f"{case['description']}")
        print(f"Expected behavior: {case['expected']}")
        print(f"==================================================")
        
        try:
            response = requests.post(url, json=case['packet'])
            response.raise_for_status()
            
            result = response.json()
            threat = result.get('threat', False)
            threat_type = result.get('threat_type', 'none')
            confidence = result.get('confidence', 0.0)
            
            print(f"Status: {'🛑 BLOCKED (Threat)' if threat else '✅ ALLOWED (Normal)'}")
            print(f"Type: {threat_type.upper()}")
            print(f"Confidence: {confidence*100:.1f}%")
            print(f"Explanation: {result.get('explanation', '')}")
            
            print(f"\n[Backend Votes]")
            print(f"Random Forest Vote: {result.get('rf_prediction')} (0=Normal, 1=Attack)")
            print(f"Isolation Forest Vote: {result.get('if_prediction')} (1=Normal, -1=Anomaly)")
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to the API. Is backend/run.py running?")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            
        print("\n")
        time.sleep(1)

if __name__ == "__main__":
    run_test()
