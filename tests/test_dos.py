import requests
import time
import socket

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

print("Starting localized 'DoS' test (many GET requests)...")
try:
    # 5000 is the Flask app
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 5000))
    for _ in range(100):
        s.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        time.sleep(0.01)
    s.close()
except Exception as e:
    print("Error:", e)

print("Finished generating traffic. Waiting for flow idle timeout (5s) + buffer...")
time.sleep(8)

stats_before_stop = requests.get(base + '/status').json()
print("Stats BEFORE stop:", stats_before_stop)

requests.post(base + '/stop')
time.sleep(2)
