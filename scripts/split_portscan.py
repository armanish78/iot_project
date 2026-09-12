import dpkt
import sys
import datetime

def main():
    in_file = 'portscan_only.pcap'
    train_file = 'portscan_train.pcap'
    test_file = 'portscan_test.pcap'
    
    print(f"Splitting {in_file} into {train_file} and {test_file}")
    
    # 13:55 to 14:55 for train
    train_start_hour = 13
    train_start_minute = 55
    train_end_hour = 14
    train_end_minute = 55
    
    train_start_min_of_day = train_start_hour * 60 + train_start_minute
    train_end_min_of_day = train_end_hour * 60 + train_end_minute

    train_written = 0
    test_written = 0
    
    with open(in_file, 'rb') as f_in, open(train_file, 'wb') as f_train, open(test_file, 'wb') as f_test:
        reader = dpkt.pcapng.Reader(f_in)
        writer_train = dpkt.pcapng.Writer(f_train)
        writer_test = dpkt.pcapng.Writer(f_test)
        
        for ts, buf in reader:
            dt = datetime.datetime.utcfromtimestamp(ts) - datetime.timedelta(hours=3)
            min_of_day = dt.hour * 60 + dt.minute
            
            # Since dt includes seconds/microseconds, min_of_day < train_end_min_of_day is strict hour/minute boundary
            # If time is exactly 14:55:00, min_of_day is 14*60+55.
            # We'll say train is < 14:55, test is >= 14:55
            if min_of_day < train_end_min_of_day:
                writer_train.writepkt(buf, ts)
                train_written += 1
            else:
                writer_test.writepkt(buf, ts)
                test_written += 1
                
    print(f"Train Packets (13:55 - 14:54): {train_written}")
    print(f"Test Packets  (14:55 - 15:29): {test_written}")

if __name__ == "__main__":
    main()
