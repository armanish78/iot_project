import threading
import time
import traceback
import nfstream

from live_extractor import LiveFlowExtractor
from backend.services.live_inference_service import live_inference_service
from backend.services.logging_service import logger_service


class PacketCaptureService:
    def __init__(self):
        self._running = False
        self._heartbeat_running = False
        self._thread = None
        self._heartbeat_thread = None
        self._interface = None
        self._app = None
        self._lock = threading.Lock()

        self.current_run_id = None
        self.extractor = None
        self.run_stats = {}

    def _get_empty_stats(self):
        return {
            "total_packets": 0,
            "flushed_flows": 0,
            "predictions": 0,
            "alerts": 0,
            "inference_errors": 0,
            "capture_errors": 0,
            "simulation_state": "IDLE"
        }

    def _get_initial_run_stats(self):
        return {
            "total_packets": 0,
            "flushed_flows": 0,
            "predictions": 0,
            "alerts": 0,
            "inference_errors": 0,
            "capture_errors": 0,
            "simulation_state": "RUNNING"
        }

    @property
    def stats(self):
        with self._lock:
            if (
                self.current_run_id
                and self.current_run_id in self.run_stats
            ):
                return self.run_stats[
                    self.current_run_id
                ].copy()

            return self._get_empty_stats()

    def _clear_run_state(self):
        self.current_run_id = None
        self.extractor = None

    def reset_run(
        self,
        run_id: str,
        dest_ip: str = None,
        dest_port: int = None
    ):
        with self._lock:
            self.current_run_id = run_id
            self.extractor = LiveFlowExtractor(idle_timeout=5.0)
            self.run_stats[run_id] = self._get_initial_run_stats()

            if dest_ip and dest_port:
                self.extractor.set_simulation_target(dest_ip, dest_port)

    def mark_traffic_finished(self, run_id: str):
        with self._lock:
            if (
                run_id in self.run_stats
                and self.run_stats[run_id]["simulation_state"] == "RUNNING"
            ):
                self.run_stats[run_id]["simulation_state"] = "PROCESSING"
                self.run_stats[run_id]["traffic_finished_time"] = time.time()

    @property
    def is_running(self):
        return self._running

    @property
    def current_interface(self):
        return self._interface

    def start(self, interface: str, app=None):
        if self._running:
            raise ValueError("Capture is already running.")
        if not interface:
            raise ValueError("Interface must be explicitly provided.")

        self._app = app

        with self._lock:
            self._interface = interface
            self._running = True
            self._heartbeat_running = True

            live_run_id = f"LIVE-{int(time.time())}"
            self.current_run_id = live_run_id
            self.extractor = LiveFlowExtractor(idle_timeout=5.0)
            live_stats = self._get_empty_stats()
            live_stats["simulation_state"] = "IDLE"
            self.run_stats[live_run_id] = live_stats

        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self._thread.start()

        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()

        logger_service.logger.info(
            f"Packet capture started on interface {interface} with live run {live_run_id}"
        )

    def stop(self):
        if not self._running:
            return

        self._running = False
        
        # Allow up to 8 seconds for the capture thread to gracefully drain
        # pending flows that expire on the 5-second idle_timeout.
        if self._thread:
            self._thread.join(timeout=8.0)

        # Now shut down the heartbeat that was waking the C loop
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)

        with self._lock:
            self._clear_run_state()

        logger_service.logger.info("Packet capture stopped.")

    def _heartbeat_loop(self):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self._heartbeat_running:
            try:
                # Send a tiny dummy packet to an unused port to wake up pcap_next
                # and allow NFStream's internal garbage collection to flush expired flows
                sock.sendto(b"heartbeat", ("127.0.0.1", 55555))
            except Exception:
                pass
            time.sleep(1.0)
        sock.close()

    def _capture_loop(self):
        try:
            streamer = nfstream.NFStreamer(
                source=self._interface,
                statistical_analysis=True,
                accounting_mode=1,
                active_timeout=60,
                idle_timeout=5,
                snapshot_length=65535
            )

            shutdown_start_time = None

            for flow in streamer:
                # Graceful Drain: If stop() was called, wait idle_timeout + 1s to flush pending flows
                if not self._running:
                    if shutdown_start_time is None:
                        shutdown_start_time = time.time()
                    
                    if time.time() - shutdown_start_time >= 6.0:
                        break

                # Exclude heartbeat natively from ALL statistics, ML, and logs
                if flow.src_port == 55555 or flow.dst_port == 55555:
                    continue

                with self._lock:
                    extractor = self.extractor
                    run_id = self.current_run_id
                    stats = self.run_stats.get(run_id) if run_id else None

                if not extractor or not stats:
                    continue

                if stats.get("simulation_state") == "COMPLETED":
                    continue

                stats["total_packets"] += flow.bidirectional_packets

                flow_data = extractor.extract_features_from_nfstream(flow)
                if flow_data:
                    extractor.expired_flows.append(flow_data)

                if self._app:
                    with self._app.app_context():
                        self._process_expired_flows(extractor, run_id, stats)
                else:
                    self._process_expired_flows(extractor, run_id, stats)

                with self._lock:
                    if stats.get("simulation_state") == "PROCESSING":
                        finished_time = stats.get("traffic_finished_time", 0)
                        if time.time() - finished_time >= extractor.idle_timeout:
                            if not extractor.expired_flows:
                                stats["simulation_state"] = "COMPLETED"

        except Exception as e:
            with self._lock:
                run_id = self.current_run_id
                if run_id and run_id in self.run_stats:
                    self.run_stats[run_id]["capture_errors"] += 1
                    self.run_stats[run_id]["last_error"] = str(e)
            self._running = False
            logger_service.logger.error(f"Capture error: {traceback.format_exc()}")

    def _process_expired_flows(self, extractor, run_id, stats):
        while True:
            with self._lock:
                if not extractor.expired_flows:
                    break
                flow_data = extractor.expired_flows.pop(0)

            features = flow_data["vector"]
            meta = flow_data["meta"]

            stats["flushed_flows"] += 1

            try:
                result = live_inference_service.predict(
                    features,
                    meta,
                    run_id=run_id
                )
                stats["predictions"] += 1
                if result.get("alerted"):
                    stats["alerts"] += 1
            except Exception as e:
                stats["inference_errors"] += 1
                logger_service.logger.error(f"Inference error on live flow: {e}")

packet_capture_service = PacketCaptureService()