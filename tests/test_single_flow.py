from backend.services.live_inference_service import live_inference_service
from backend.services.database_service import db_service

def test_single_flow():
    # 69 features of zeros for a basic shape test
    features = [0.0] * 69
    
    meta = {
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.1"
    }
    
    print("Testing single flow prediction with 69 features...")
    res = live_inference_service.predict(features, meta)
    
    print("Prediction Result:")
    print(f"Threat: {res['threat']}")
    print(f"Type: {res['threat_type']}")
    print(f"Confidence: {res['confidence']}")

if __name__ == "__main__":
    test_single_flow()
