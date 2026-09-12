from flask import Blueprint, request, jsonify, render_template_string
import socket

device_bp = Blueprint('device_bp', __name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel Phone Telemetry</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #001D39; color: white; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #0A4174; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h1 { color: #7BBDE8; font-size: 24px; margin-top: 0; }
        p { color: #BDD8E9; font-size: 14px; line-height: 1.5; }
        button { background: #4E8EA2; border: none; padding: 15px 20px; color: white; font-weight: bold; border-radius: 8px; width: 100%; margin-bottom: 15px; cursor: pointer; font-size: 16px; }
        button:active { background: #6EA2B3; }
        .log { background: #001D39; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; color: #7BBDE8; min-height: 100px; max-height: 200px; overflow-y: auto; }
        .info { background: rgba(123,189,232,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(123,189,232,0.3); }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sentinel Device Telemetry</h1>
        <div class="info">
            <p><strong>Sentinel PC IP:</strong> {{ pc_ip }}</p>
            <p>This page allows your phone to generate real HTTP/TCP network traffic to the Sentinel PC. Ensure Scapy is capturing on your PC's Wi-Fi interface.</p>
        </div>
        
        <button onclick="sendTelemetry(1)">Send 1 Telemetry Request</button>
        <button onclick="sendTelemetry(10)">Send 10 Rapid Requests</button>
        <button onclick="togglePeriodic()" id="periodicBtn">Start Periodic Telemetry (1/sec)</button>
        
        <div class="log" id="log">Logs will appear here...<br></div>
    </div>

    <script>
        const logEl = document.getElementById('log');
        let periodicInterval = null;

        function log(msg) {
            logEl.innerHTML += msg + '<br>';
            logEl.scrollTop = logEl.scrollHeight;
        }

        async function sendTelemetry(count) {
            log(`Sending ${count} request(s)...`);
            for (let i = 0; i < count; i++) {
                try {
                    const res = await fetch('/device/telemetry', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sensor_id: 'phone-01', value: Math.random() * 100, timestamp: new Date().toISOString() })
                    });
                    if (res.ok) log(`[Success] Request ${i+1}`);
                    else log(`[Error] Request ${i+1} failed`);
                } catch (e) {
                    log(`[Error] Network error: ${e.message}`);
                }
            }
        }

        function togglePeriodic() {
            const btn = document.getElementById('periodicBtn');
            if (periodicInterval) {
                clearInterval(periodicInterval);
                periodicInterval = null;
                btn.innerText = "Start Periodic Telemetry (1/sec)";
                log("Stopped periodic telemetry.");
            } else {
                periodicInterval = setInterval(() => sendTelemetry(1), 1000);
                btn.innerText = "Stop Periodic Telemetry";
                log("Started periodic telemetry.");
            }
        }
    </script>
</body>
</html>
"""

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@device_bp.route('/device', methods=['GET'])
def device_page():
    return render_template_string(HTML_TEMPLATE, pc_ip=get_local_ip())

@device_bp.route('/device/telemetry', methods=['POST'])
def receive_telemetry():
    # We do nothing here except return 200 OK.
    # The traffic is captured at the OS level by Scapy.
    return jsonify({"status": "received"}), 200
