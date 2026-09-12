import os
import sys
import json
import sqlite3
from collections import defaultdict

def analyze():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'iot_security.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query genuine PortScans from the dataset (attacker 172.16.0.1)
    cursor.execute('''
        SELECT a.id as alert_id, p.* 
        FROM alerts a 
        JOIN predictions p ON a.prediction_id = p.id 
        WHERE p.source_ip = '172.16.0.1' AND p.threat = 1
    ''')
    
    genuine_alerts = cursor.fetchall()
    print(f"--- GENUINE PORTSCAN ANALYSIS ---")
    print(f"Total genuine PortScan flows: {len(genuine_alerts)}")
    
    if genuine_alerts:
        dest_ips = set()
        dest_ports = set()
        src_ports = set()
        for a in genuine_alerts:
            dest_ips.add(a['dest_ip'])
            
            # extract ports from explanation
            explanation = json.loads(a['explanation']) if a['explanation'] else {}
            sp = explanation.get('src_port')
            dp = explanation.get('dst_port')
            if sp is not None: src_ports.add(sp)
            if dp is not None: dest_ports.add(dp)

        print(f"Source IP: 172.16.0.1")
        print(f"Unique Dest IPs: {len(dest_ips)}")
        print(f"Unique Dest Ports: {len(dest_ports)}")
        print(f"Unique Source Ports: {len(src_ports)}")
        
        # Calculate time windows (approximate based on timestamp range if available, but timestamp is insertion time, not packet time, unless we have PCAP timestamps. Wait, the timestamp in DB for offline PCAP is just insertion time. The PCAP itself has real times, but we didn't save them. Actually, wait! The DB timestamps might be insertion time. 
        # But for unique ports, len(dest_ports) vs len(genuine_alerts) is key.)
        
if __name__ == '__main__':
    analyze()
