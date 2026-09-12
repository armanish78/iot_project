import sys
import os
import time
import json
from scapy.all import sniff

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from live_extractor import LiveFlowExtractor

def main():
    duration = 15 # Capture for 15 seconds
    print(f"Starting real-world benign traffic capture for {duration} seconds...")
    
    extractor = LiveFlowExtractor(idle_timeout=5.0)
    
    def packet_callback(pkt):
        extractor.process_packet(pkt, current_time=time.time())
        
    start_time = time.time()
    
    # Sniff packets
    sniff(
        prn=packet_callback,
        store=False,
        timeout=duration,
        filter="ip"  # Only capture IP packets
    )
    
    extractor.flush_all_flows()
    
    flows = extractor.expired_flows
    print(f"Captured {len(flows)} flows.")
    
    out_file = os.path.join(SCRIPT_DIR, "benchmark_data", "short_benign_flows.json")
    with open(out_file, "w") as f:
        json.dump(flows, f, indent=4)
        
    print(f"Saved benign flows to {out_file}")

if __name__ == "__main__":
    main()
