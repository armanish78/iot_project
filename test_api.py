import requests
import json

def run_test():
    url = "http://localhost:5000/api/predictions/detect"
    
    print("🚀 Sending a test network packet to the Live API...")
    
    # This is our fake suspicious packet
    test_packet = {
        "source_ip": "192.168.1.5",
        "dest_ip": "10.0.0.1",
        "packet_size_min": 0,
        "sttl": 255
    }
    
    print("\n📦 The Packet:")
    print(json.dumps(test_packet, indent=2))
    
    try:
        response = requests.post(url, json=test_packet)
        response.raise_for_status()  # Check if the request was successful
        
        print("\n✅ API Response received!")
        print("🧠 Threat Analysis Report:")
        print(json.dumps(response.json(), indent=4))
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API.")
        print("Make sure your Flask server is running in another terminal (python backend/run.py)")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    run_test()
