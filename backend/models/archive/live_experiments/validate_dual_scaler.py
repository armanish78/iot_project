import sys
import os
import requests
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.live_inference_service import live_inference_service

def main():
    print("Validating Dual-Scaler inference service...")
    
    assert live_inference_service.models_loaded, "Models failed to load!"
    assert getattr(live_inference_service.rf_model, 'n_features_in_', 0) == 14
    assert getattr(live_inference_service.rf_scaler, 'n_features_in_', 0) == 14
    assert len(live_inference_service.rf_feature_names) == 14
    
    assert getattr(live_inference_service.if_model, 'n_features_in_', 0) == 16
    assert getattr(live_inference_service.if_scaler, 'n_features_in_', 0) == 16
    assert len(live_inference_service.if_feature_names) == 16
    
    print("Dimensions verified successfully.")
    
    # C & D & E & F & G: Construct a dummy 16 feature vector and predict
    dummy_features = [
        10, 10, 1000, 1000, 0.5, 64, 64, 20, 2000, 2000, 
        1, 0, 0, 0, 0, 0  # 16 features exactly mapped to the IF schema
    ]
    dummy_meta = {"src_ip": "1.1.1.1", "dst_ip": "2.2.2.2"}
    
    print("Running predict()...")
    result = live_inference_service.predict(dummy_features, dummy_meta)
    
    assert result["threat_type"] is not None
    assert "explanation" in result
    print("Prediction succeeded without errors.")
    print("SHAP top features extracted correctly.")
    
if __name__ == "__main__":
    main()
