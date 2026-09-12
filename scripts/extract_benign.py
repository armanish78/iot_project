import dpkt
import sys
import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: extract_benign.py <in_pcap>")
        return

    in_file = sys.argv[1]
    train_file = 'benign_train.pcap'
    test_file = 'benign_test.pcap'
    
    print(f"Extracting benign windows from {in_file} into {train_file} and {test_file}")
    
    # Train: 09:00 to 10:59
    train_start_hour = 9
    train_end_hour = 10
    
    # Test: 11:00 to 11:59
    test_start_hour = 11
    test_end_hour = 11
    
    train_written = 0
    test_written = 0
    total = 0
    
    try:
        with open(in_file, 'rb') as f_in, open(train_file, 'wb') as f_train, open(test_file, 'wb') as f_test:
            reader = dpkt.pcapng.Reader(f_in)
            writer_train = dpkt.pcapng.Writer(f_train)
            writer_test = dpkt.pcapng.Writer(f_test)
            
            for ts, buf in reader:
                total += 1
                if total % 1000000 == 0:
                    print(f"Processed {total} packets. Train: {train_written}, Test: {test_written}")
                
                # ADT is UTC-3
                dt = datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(hours=3)
                
                # We stop processing completely once we pass 12:00 to save time
                if dt.hour >= 12:
                    break
                    
                if train_start_hour <= dt.hour <= train_end_hour:
                    writer_train.writepkt(buf, ts)
                    train_written += 1
                elif test_start_hour <= dt.hour <= test_end_hour:
                    writer_test.writepkt(buf, ts)
                    test_written += 1
                    
    except Exception as e:
        print(f"Extraction error (might be expected at EOF/early break): {e}")

    print(f"Done! Packets Read: {total}")
    print(f"Train Packets (09:00 - 10:59): {train_written}")
    print(f"Test Packets  (11:00 - 11:59): {test_written}")

if __name__ == "__main__":
    main()
