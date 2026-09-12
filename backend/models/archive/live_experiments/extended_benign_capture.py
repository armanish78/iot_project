import sys
import os
import time
import json
from scapy.all import sniff

# Add project root to sys.path to import live_extractor
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from live_extractor import LiveFlowExtractor

def main():
    duration = 900 # Capture for 15 minutes (900 seconds)
    print(f"Starting EXTENDED real-world benign traffic capture for {duration} seconds...")
    print("This capture will NOT be used for training or threshold tuning.")
    
    extractor = LiveFlowExtractor(idle_timeout=5.0)
    
    start_time = time.time()
    
    def packet_callback(pkt):
        extractor.process_packet(pkt, current_time=time.time())
        # Print progress every minute
        elapsed = time.time() - start_time
        if int(elapsed) % 60 == 0:
            sys.stdout.write(f"\rProgress: {int(elapsed)}/{duration} seconds... Flows tracking: {len(extractor.flows)}")
            sys.stdout.flush()

    # Sniff packets
    print("Sniffing...")
    sniff(
        prn=packet_callback,
        store=False,
        timeout=duration,
        filter="ip"
    )
    
    print("\nCapture complete. Flushing flows...")
    extractor.flush_all_flows()
    
    flows = extractor.expired_flows
    print(f"Captured {len(flows)} extended benign flows.")
    
    out_file = os.path.join(SCRIPT_DIR, "benchmark_data", "extended_benign_flows.json")
    with open(out_file, "w") as f:
        json.dump(flows, f, indent=4)
        
    print(f"Saved extended benign flows to {out_file}")

if __name__ == "__main__":
    main()
