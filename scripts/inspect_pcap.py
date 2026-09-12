import dpkt
import sys
import datetime

def main():
    in_file = sys.argv[1]
    
    first_ts = None
    last_ts = None
    count = 0
    
    with open(in_file, 'rb') as f:
        # Try pcapng first, then fallback to pcap
        try:
            reader = dpkt.pcapng.Reader(f)
        except Exception:
            f.seek(0)
            reader = dpkt.pcap.Reader(f)
            
        for ts, buf in reader:
            if first_ts is None:
                first_ts = ts
            last_ts = ts
            count += 1
            if count == 1:
                break
                
        # fast forward to end? Can't easily in dpkt streaming, so just iterate
        for ts, buf in reader:
            last_ts = ts
            count += 1

    print(f"File: {in_file}")
    print(f"Total Packets: {count}")
    
    dt_first_utc = datetime.datetime.utcfromtimestamp(first_ts)
    dt_last_utc = datetime.datetime.utcfromtimestamp(last_ts)
    
    # CIC-IDS2017 was captured in AST/ADT (UTC-3)
    dt_first_local = dt_first_utc - datetime.timedelta(hours=3)
    dt_last_local = dt_last_utc - datetime.timedelta(hours=3)
    
    print(f"First Packet (UTC):   {dt_first_utc}")
    print(f"First Packet (Local): {dt_first_local}")
    print(f"Last Packet (UTC):    {dt_last_utc}")
    print(f"Last Packet (Local):  {dt_last_local}")

if __name__ == "__main__":
    main()
