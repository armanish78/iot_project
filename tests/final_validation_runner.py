import requests
import time
import os

base = 'http://127.0.0.1:5000/api/live'

def get_ifaces():
    try:
        ifaces = requests.get(base + '/interfaces').json().get('interfaces', [])
        wifi = next((i['name'] for i in ifaces if 'Wi-Fi' in i['label'] and 'NPF' in i['name']), None)
        loopback = next((i['name'] for i in ifaces if 'Loopback' in i['label'] and 'NPF' in i['name']), None)
        if not wifi: wifi = next((i['name'] for i in ifaces if 'Wi-Fi' in i['name']), "Wi-Fi")
        if not loopback: loopback = next((i['name'] for i in ifaces if 'Loopback' in i['name']), "127.0.0.1")
        return wifi, loopback
    except:
        return "Wi-Fi", "127.0.0.1"

wifi_name, loopback_name = get_ifaces()

results = []

def run_test(test_name, interface, config, wait_time, repeats=1):
    print(f"\n--- Running {test_name} ---")
    for r in range(repeats):
        run_name = test_name if repeats == 1 else f"{test_name} (Run {r+1})"
        try:
            requests.post(base + '/stop')
            res_start = requests.post(base + '/start', json={'interface': interface})
            if res_start.status_code != 200:
                print("Failed to start capture:", res_start.json())
                continue
            
            if config:
                requests.post(base + '/simulate', json=config)
                
            time.sleep(wait_time)
            
            stats = requests.get(base + '/status').json().get('stats', {})
            
            # Stop and drain (will take up to 8 seconds)
            requests.post(base + '/stop')
            time.sleep(1) # just in case
            results.append({
                "Test": run_name,
                "Packets": stats.get('total_packets', 0),
                "Flows": stats.get('flushed_flows', 0),
                "Predictions": stats.get('predictions', 0),
                "Errors": stats.get('inference_errors', 0) + stats.get('capture_errors', 0),
                "Alerts": stats.get('alerts', 0),
                "Notes": "OK" if stats.get('capture_errors', 0) == 0 else stats.get('last_error', 'Error')
            })
            print(f"Finished {run_name}: {stats}")
        except Exception as e:
            print(f"Error in {run_name}: {e}")
            results.append({
                "Test": run_name,
                "Packets": 0, "Flows": 0, "Predictions": 0, "Errors": 1, "Alerts": 0, "Notes": str(e)
            })

# TEST 1
run_test("Test 1: Real Wi-Fi Traffic", wifi_name, None, 15)

# TEST 2
run_test("Test 2: Loopback Normal", loopback_name, {
    "protocol": "TCP", "dest_ip": "127.0.0.1", "dest_port": 12345, 
    "num_connections": 3, "packets_per_connection": 5, "payload_size": 64, 
    "delay_between_packets": 0.1, "delay_between_connections": 0.1
}, 10)

# TEST 3
run_test("Test 3: Burst TCP", loopback_name, {
    "protocol": "TCP", "dest_ip": "127.0.0.1", "dest_port": 12345, 
    "num_connections": 200, "packets_per_connection": 1, "payload_size": 64, 
    "delay_between_packets": 0, "delay_between_connections": 0
}, 15)

# TEST 4 & 5
run_test("Test 4/5: High Rate UDP", loopback_name, {
    "protocol": "UDP", "dest_ip": "127.0.0.1", "dest_port": 12345, 
    "num_connections": 1, "packets_per_connection": 1000, "payload_size": 1024, 
    "delay_between_packets": 0, "delay_between_connections": 0
}, 15, repeats=3)

print("\n\nFINAL REPORT TABLE:")
print(f"{'Test':<30} | {'Packets':<8} | {'Flows':<5} | {'Preds':<5} | {'Err':<3} | {'Alerts':<6} | {'Notes'}")
print("-" * 80)
for r in results:
    print(f"{r['Test']:<30} | {r['Packets']:<8} | {r['Flows']:<5} | {r['Predictions']:<5} | {r['Errors']:<3} | {r['Alerts']:<6} | {r['Notes']}")

# TEST 9 Failure edge conditions
print("\n--- Testing Edge Conditions ---")
requests.post(base + '/stop')
res1 = requests.post(base + '/stop')
print("Stop when stopped:", res1.status_code, res1.json())

requests.post(base + '/start', json={'interface': loopback_name})
res2 = requests.post(base + '/start', json={'interface': loopback_name})
print("Start when started:", res2.status_code, res2.json())
requests.post(base + '/stop')

res3 = requests.post(base + '/simulate', json={})
print("Simulate when stopped:", res3.status_code, res3.json())
