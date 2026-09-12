import nfstream
import socket
import time
import threading

def generate_udp():
    time.sleep(1)
    print("Generating 1000 UDP packets...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(1000):
        sock.sendto(b"x"*1024, ("127.0.0.1", 12345))
    sock.close()
    print("Generation done.")
    
    # Send a dummy packet later to trigger GC?
    time.sleep(6)
    print("Sending dummy packet to trigger GC...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b"dummy", ("127.0.0.1", 12346))
    sock.close()

def main():
    t = threading.Thread(target=generate_udp)
    t.start()
    
    streamer = nfstream.NFStreamer(
        source="Loopback Pseudo-Interface 1",
        active_timeout=60,
        idle_timeout=5
    )
    
    flows = 0
    packets = 0
    print("Listening on NFStream...")
    for flow in streamer:
        flows += 1
        packets += flow.bidirectional_packets
        print(f"Flow emitted! Packets in flow: {flow.bidirectional_packets}, dst_port: {flow.dst_port}")
        if flows >= 1:
            break

if __name__ == "__main__":
    main()
