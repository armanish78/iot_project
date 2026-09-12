import requests
import time
import socket
import threading

base = 'http://127.0.0.1:5000/api/live'

def get_ifaces():
    try:
        ifaces = requests.get(base + '/interfaces').json().get('interfaces', [])
        loopback = next((i['name'] for i in ifaces if 'Loopback' in i['name'] or '127.0.0.1' in i['name']), "127.0.0.1")
        return loopback
    except:
        return "127.0.0.1"

loopback_name = get_ifaces()
print(f"Using Loopback ID: {loopback_name}")

requests.post(base + '/stop')
requests.post(base + '/start', json={'interface': loopback_name})
print("Started capture on loopback...")

time.sleep(2)

print("Starting localized 'PortScan' test (attempting TCP connections to closed ports)...")
def scan_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(('127.0.0.1', port))
        s.close()
    except:
        pass

threads = []
for p in range(20000, 20500):
    t = threading.Thread(target=scan_port, args=(p,))
    t.start()
    threads.append(t)
    time.sleep(0.001)

for t in threads:
    t.join()

print("Finished generating traffic. Waiting for flow idle timeout (5s) + buffer...")
time.sleep(8)

stats_before_stop = requests.get(base + '/status').json()
print("Stats BEFORE stop:", stats_before_stop)

requests.post(base + '/stop')
time.sleep(2)
