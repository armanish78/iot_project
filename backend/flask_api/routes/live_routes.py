from flask import Blueprint, request, jsonify
from scapy.all import get_if_list, conf

from backend.services.packet_capture_service import packet_capture_service
from backend.services.logging_service import logger_service

live_bp = Blueprint('live_bp', __name__, url_prefix='/api/live')


@live_bp.route('/interfaces', methods=['GET'])
def get_interfaces():
    """
    Return network interfaces with a human-friendly display name
    while preserving the real Scapy/Npcap interface internally.
    """
    try:
        interfaces = []

        for pcap_name in get_if_list():
            friendly_name = pcap_name
            description = ""

            try:
                iface = conf.ifaces.get(pcap_name)

                if iface:
                    # On Windows, Scapy's interface object contains
                    # the friendly Windows adapter information.
                    friendly_name = (
                        getattr(iface, "name", None)
                        or getattr(iface, "description", None)
                        or pcap_name
                    )

                    description = (
                        getattr(iface, "description", None)
                        or ""
                    )

            except Exception:
                # If friendly-name lookup fails, keep the real
                # Scapy interface name as a safe fallback.
                pass

            interfaces.append({
                "name": pcap_name,
                "label": friendly_name,
                "description": description
            })

        return jsonify({"interfaces": interfaces}), 200

    except Exception as e:
        logger_service.log_error(
            e,
            {"context": "Get network interfaces"}
        )

        return jsonify({
            "error": str(e)
        }), 500


@live_bp.route('/status', methods=['GET'])
def get_live_status():
    from backend.services.database_service import db_service

    run_id = getattr(
        packet_capture_service,
        'current_run_id',
        None
    )

    devices = []

    if run_id:
        devices = db_service.get_observed_devices(
            run_id=run_id
        )

    status = {
        "running": packet_capture_service.is_running,
        "interface": packet_capture_service.current_interface,
        "run_id": run_id,
        "stats": packet_capture_service.stats,
        "observed_devices": devices
    }

    return jsonify(status), 200


@live_bp.route('/devices', methods=['GET'])
def get_live_devices():
    from backend.services.database_service import db_service

    try:
        run_id = getattr(
            packet_capture_service,
            'current_run_id',
            None
        )

        if run_id:
            devices = db_service.get_observed_devices(
                run_id=run_id
            )
        else:
            devices = []

        return jsonify({
            "devices": devices
        }), 200

    except Exception as e:
        logger_service.log_error(
            e,
            {"context": "Get observed devices"}
        )

        return jsonify({
            "error": str(e)
        }), 500


@live_bp.route('/start', methods=['POST'])
def start_live_capture():
    data = request.get_json() or {}
    interface = data.get("interface")

    if not interface:
        return jsonify({
            "error": "Interface is required to start live capture."
        }), 400

    if packet_capture_service.is_running:
        return jsonify({
            "error": "Capture is already running."
        }), 400

    try:
        from flask import current_app

        app = current_app._get_current_object()

        packet_capture_service.start(
            interface,
            app=app
        )

        return jsonify({
            "message": (
                f"Packet capture started on interface "
                f"'{interface}'."
            )
        }), 200

    except Exception as e:
        logger_service.log_error(
            e,
            {"context": "Start live capture"}
        )

        return jsonify({
            "error": str(e)
        }), 500


@live_bp.route('/stop', methods=['POST'])
def stop_live_capture():
    if not packet_capture_service.is_running:
        return jsonify({
            "message": "Capture is not running."
        }), 200

    try:
        packet_capture_service.stop()

        return jsonify({
            "message": "Packet capture stopped."
        }), 200

    except Exception as e:
        logger_service.log_error(
            e,
            {"context": "Stop live capture"}
        )

        return jsonify({
            "error": str(e)
        }), 500


import threading
import socket
import time


def run_simulation_thread(config, run_id):
    start_time = time.time()
    packets_sent = 0

    protocol = config.get(
        "protocol",
        "UDP"
    ).upper()

    dest_ip = config.get(
        "dest_ip",
        "127.0.0.1"
    )

    dest_port = int(
        config.get(
            "dest_port",
            12345
        )
    )

    num_connections = int(
        config.get(
            "num_connections",
            1
        )
    )

    packets_per_connection = int(
        config.get(
            "packets_per_connection",
            5
        )
    )

    payload_size = int(
        config.get(
            "payload_size",
            64
        )
    )

    delay_packets = float(
        config.get(
            "delay_between_packets",
            0.1
        )
    )
    if delay_packets <= 0:
        delay_packets = 0.001

    delay_connections = float(
        config.get(
            "delay_between_connections",
            0.5
        )
    )

    payload = b"X" * payload_size

    try:
        for _ in range(num_connections):

            sock_type = (
                socket.SOCK_STREAM
                if protocol == "TCP"
                else socket.SOCK_DGRAM
            )

            sock = socket.socket(
                socket.AF_INET,
                sock_type
            )

            if protocol == "TCP":
                sock.settimeout(0.5)

                try:
                    sock.connect(
                        (
                            dest_ip,
                            dest_port
                        )
                    )
                except Exception:
                    # Connection refused is fine.
                    # SYN packets are still generated.
                    pass

            for _ in range(
                packets_per_connection
            ):

                try:
                    if protocol == "UDP":
                        sock.sendto(
                            payload,
                            (
                                dest_ip,
                                dest_port
                            )
                        )
                    else:
                        sock.sendall(payload)

                    packets_sent += 1

                except Exception:
                    # Ignore individual send errors.
                    pass

                if delay_packets > 0:
                    time.sleep(
                        delay_packets
                    )

            sock.close()

            if delay_connections > 0:
                time.sleep(
                    delay_connections
                )

    except Exception as e:
        print(
            f"Simulation error: {e}"
        )

    duration = (
        time.time() - start_time
    )

    print(
        f"Simulation completed: "
        f"{packets_sent} packets sent "
        f"in {duration:.2f}s."
    )

    from backend.services.packet_capture_service import (
        packet_capture_service
    )

    packet_capture_service.mark_traffic_finished(
        run_id
    )


@live_bp.route('/simulate', methods=['POST'])
def run_simulation():
    config = request.get_json() or {}

    if not packet_capture_service.is_running:
        return jsonify({
            "error": (
                "Capture is not running. "
                "Start live capture before "
                "running a traffic simulation."
            )
        }), 400

    run_id = f"SIM-{int(time.time())}"

    dest_ip = config.get(
        "dest_ip",
        "127.0.0.1"
    )

    dest_port = int(
        config.get(
            "dest_port",
            12345
        )
    )

    packet_capture_service.reset_run(
        run_id,
        dest_ip=dest_ip,
        dest_port=dest_port
    )

    thread = threading.Thread(
        target=run_simulation_thread,
        args=(
            config,
            run_id
        ),
        daemon=True
    )

    thread.start()

    return jsonify({
        "message": "Simulation started.",
        "run_id": run_id,
        "config": config
    }), 200