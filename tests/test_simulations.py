import requests
import time

base = 'http://127.0.0.1:5000/api/live'

# Fetch valid interfaces
try:
    ifaces = requests.get(base + '/interfaces').json().get('interfaces', [])
    wifi_name = next((i['name'] for i in ifaces if 'Wi-Fi' in i['label'] and 'NPF' in i['name']), None)
    loopback_name = next((i['name'] for i in ifaces if 'Loopback' in i['label'] and 'NPF' in i['name']), None)
    
    if not wifi_name:
        wifi_name = next((i['name'] for i in ifaces if 'Wi-Fi' in i['name']), "Wi-Fi")
    if not loopback_name:
        loopback_name = next((i['name'] for i in ifaces if 'Loopback' in i['name']), "127.0.0.1")
except:
    wifi_name = "Wi-Fi"
    loopback_name = "127.0.0.1"

print(f"Using Wi-Fi ID: {wifi_name}")
print(f"Using Loopback ID: {loopback_name}")

def test_scenario(name, interface, config, wait_time):
    print(f"\n=== TEST: {name} ===")
    requests.post(base + '/stop')
    requests.post(base + '/start', json={'interface': interface})
    
    if config:
        res = requests.post(base + '/simulate', json=config)
        run_id = res.json().get('run_id')
        print(f"Started Run: {run_id}")
    else:
        print("Waiting for background traffic...")
        
    time.sleep(wait_time)
    
    status_before_stop = requests.get(base + '/status').json()
    print("Stats BEFORE stop:", status_before_stop.get('stats'))
    
    requests.post(base + '/stop')
    
    status_after_stop = requests.get(base + '/status').json()
    print("Stats AFTER stop:", status_after_stop.get('stats'))

# A. Real Wi-Fi traffic
test_scenario("Real Wi-Fi traffic", wifi_name, None, 10)

# B. Loopback Connection Burst TCP
test_scenario("Loopback Connection Burst TCP", loopback_name, {
    "protocol": "TCP",
    "dest_ip": "127.0.0.1",
    "dest_port": 12345,
    "num_connections": 20,
    "packets_per_connection": 5,
    "payload_size": 64,
    "delay_between_packets": 0.1,
    "delay_between_connections": 0.5
}, 15)

# C. High Rate UDP
test_scenario("High Rate UDP", loopback_name, {
    "protocol": "UDP",
    "dest_ip": "127.0.0.1",
    "dest_port": 12345,
    "num_connections": 1,
    "packets_per_connection": 1000,
    "payload_size": 1024,
    "delay_between_packets": 0,
    "delay_between_connections": 0
}, 12)
