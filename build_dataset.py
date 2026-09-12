import os
import sys
import pandas as pd
from nfstream import NFStreamer
from backend.services.packet_capture_service import LiveFlowExtractor

def extract_features(pcap_path, is_attack_pcap, out_csv, append=False):
    print(f"Extracting features from {pcap_path}...")
    
    # We use NFStreamer to read the pcap offline exactly like the live capture
    streamer = NFStreamer(source=pcap_path, decode_tunnels=True, bpf_filter=None)
    
    # Instantiate the extractor since extract_features_from_nfstream is an instance method
    extractor = LiveFlowExtractor(idle_timeout=5.0)
    
    count = 0
    features_list = []
    chunk_size = 20000
    first_chunk = not append
    
    for flow in streamer:
        count += 1
        
        # Call the exact same extraction logic used by Sentinel live inference
        feat_dict = extractor.extract_features_from_nfstream(flow)
        
        # Extract features vector if necessary (extract_features_from_nfstream returns a dict with 'vector' and 'meta')
        if feat_dict and 'vector' in feat_dict:
            # We want the flat dictionary mapping feature names to values for training
            from live_extractor import FEATURE_COLUMNS
            flat_dict = dict(zip(FEATURE_COLUMNS, feat_dict['vector']))
            
            # Determine actual label based on attacker IP
            flow_label = 0
            if is_attack_pcap:
                src_ip = feat_dict['meta'].get('src_ip')
                dst_ip = feat_dict['meta'].get('dst_ip')
                if src_ip == '172.16.0.1' or dst_ip == '172.16.0.1':
                    flow_label = 1
                    
            # Add the label
            flat_dict['Label'] = flow_label
            features_list.append(flat_dict)
        elif isinstance(feat_dict, dict) and 'Label' not in feat_dict and 'vector' not in feat_dict:
            # Maybe it returns flat dict directly (fallback)
            feat_dict['Label'] = 1 if is_attack_pcap else 0
            features_list.append(feat_dict)

        if count % chunk_size == 0 and features_list:
            df_chunk = pd.DataFrame(features_list)
            df_chunk.to_csv(out_csv, mode='a' if not first_chunk else 'w', header=first_chunk, index=False)
            first_chunk = False
            features_list = []
            print(f"  Processed {count} flows...")
            
    if features_list:
        df_chunk = pd.DataFrame(features_list)
        df_chunk.to_csv(out_csv, mode='a' if not first_chunk else 'w', header=first_chunk, index=False)
        
    print(f"Extracted {count} flows from {pcap_path}.")
    return count

def main():
    benign_train_pcap = 'benign_train.pcap'
    benign_test_pcap = 'benign_test.pcap'
    portscan_train_pcap = 'portscan_train.pcap'
    portscan_test_pcap = 'portscan_test.pcap'
    
    # Check if all files exist
    for f in [benign_train_pcap, benign_test_pcap, portscan_train_pcap, portscan_test_pcap]:
        if not os.path.exists(f):
            print(f"Waiting for {f} to be available...")
            return

    # Extract Train Set
    print("--- BUILDING TRAIN SET ---")
    if os.path.exists('train_features.csv'):
        os.remove('train_features.csv')
    extract_features(benign_train_pcap, is_attack_pcap=False, out_csv='train_features.csv', append=False)
    extract_features(portscan_train_pcap, is_attack_pcap=True, out_csv='train_features.csv', append=True)
    
    # Extract Test Set
    print("\n--- BUILDING TEST SET ---")
    if os.path.exists('test_features.csv'):
        os.remove('test_features.csv')
    extract_features(benign_test_pcap, is_attack_pcap=False, out_csv='test_features.csv', append=False)
    extract_features(portscan_test_pcap, is_attack_pcap=True, out_csv='test_features.csv', append=True)

if __name__ == "__main__":
    main()
