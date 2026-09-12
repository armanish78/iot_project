import dpkt
import sys
import datetime

def main():
    if len(sys.argv) < 3:
        print("Usage: extract_attack.py <in_pcap> <out_pcap>")
        return

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    
    # 13:55 to 15:29
    start_hour = 13
    start_minute = 55
    end_hour = 15
    end_minute = 29
    
    # Time window converted to minutes of the day for easy comparison
    start_min_of_day = start_hour * 60 + start_minute
    end_min_of_day = end_hour * 60 + end_minute

    written = 0
    total = 0
    
    print(f"Reading {in_file} (pcapng format)...")
    
    try:
        with open(in_file, 'rb') as f_in, open(out_file, 'wb') as f_out:
            reader = dpkt.pcapng.Reader(f_in)
            writer = dpkt.pcapng.Writer(f_out)
            
            for ts, buf in reader:
                total += 1
                if total % 1000000 == 0:
                    print(f"Processed {total} packets. Written: {written}")
                    
                # The UNB CIC-IDS2017 dataset was recorded in AST/ADT (UTC-3 in July)
                # But dpkt might give decimal timestamps.
                dt = datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(hours=3)
                
                # Check if we are in the portscan window
                min_of_day = dt.hour * 60 + dt.minute
                if start_min_of_day <= min_of_day <= end_min_of_day:
                    writer.writepkt(buf, ts)
                    written += 1
                    
    except Exception as e:
        print(f"Extraction error (might be expected at EOF): {e}")

    print(f"Done! Total packets read: {total}. Total written to {out_file}: {written}")

if __name__ == "__main__":
    main()
