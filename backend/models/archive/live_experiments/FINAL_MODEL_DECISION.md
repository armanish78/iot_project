# Sentinel Final Model Decision
**Date:** 2026-09-12
**Component:** Live IDS Inference Engine

## Executive Summary
After discovering that the baseline 16-feature RF model was producing unacceptable false positive rates on real-world traffic, we completely rebuilt the live IDS pipeline. Sentinel has transitioned from an ad-hoc 16-feature Scapy aggregator to an authentic **NFStream-powered CIC-IDS2017 pipeline**. 

The new system successfully integrates an external, pretrained XGBoost model (`maduchs/Network-Intrusion-Detection-using-Machine-Learning-on-CIC-IDS2017`) capable of differentiating normal traffic from 11 distinct attack classes in real-time.

## Architectural Changes

### 1. Feature Extraction Replacement
- **Previous System:** `LiveFlowExtractor` computed 16 basic statistical features (packet counts, simple lengths, and TTLs) by intercepting packets in a busy Scapy `sniff` loop.
- **New System:** Replaced with `NFStreamer`. NFStream natively computes 78+ complex flow properties, including highly precise Inter-Arrival Times (IAT), TCP flag counts, active/idle timeouts, and initial window sizes. 
- **Mapping:** We map the NFStream output strictly to the exactly required **69 features** demanded by the CIC-IDS2017 standard.

### 2. Inference Model Transition
- **Previous System:** Scikit-Learn `RandomForestClassifier` (14 or 16 features) running alongside an `IsolationForest` for hybrid anomaly checking. 
- **New System:** XGBoost (`final_xgboost_model.joblib`) with a standard scaler (`scaler.joblib`) and a Multi-class Label Encoder (`label_encoder.joblib`). 
- **Policy:** The rigid `RF >= 0.80` heuristic has been abandoned. If the model outputs any label other than `BENIGN` (e.g., `Bot`, `DDoS`, `PortScan`), it triggers a threat alert.

## Validation and Compatibility
All requirements of the strict Compatibility Gate (Phase 5) were satisfied:
1. Exact feature names, order, and semantics match the external artifact's training distribution.
2. No data fabrication or zero-filling of missing features is required.
3. The multi-class output natively fulfills Sentinel's alerting contract by mapping `BENIGN` to normal and all other classes to `threat=True`.

## Production Readiness
The final codebase is deployed in `backend/services/packet_capture_service.py` and `backend/services/live_inference_service.py`. The standalone APIs and automated tests run cleanly. 

## Flow Finalization Fix (Windows Loopback)

### Root Cause
During simulation testing, High Rate UDP traffic correctly reached the network stack, but NFStream reported `0 flows aggregated` and `0 predictions`. This occurred because NFStream's live capture generator blocks indefinitely on a silent interface (like Windows loopback after a test burst). Without subsequent packets to wake the C/libpcap loop, the 5-second `idle_timeout` is never evaluated, causing the simulated flow to be permanently trapped in memory.

### Exact Fix
1. **Heartbeat Wake-Up Mechanism**: Added a lightweight background thread in `PacketCaptureService` that emits a dummy UDP packet to `127.0.0.1:55555` once per second while capture is active. This guarantees the C loop wakes up frequently to evaluate and yield expired flows.
2. **Heartbeat Exclusion**: The heartbeat is explicitly intercepted and discarded in Python (`if flow.src_port == 55555...`) *before* any feature extraction, ML inference, or statistics aggregation occurs. It never generates alerts or predictions.
3. **Simulator Pacing**: Enforced a `0.001` second minimum delay for High Rate UDP simulator profiles to prevent Windows Npcap ring buffer overflows, ensuring packets are successfully ingested rather than dropped by the OS.
4. **Shutdown Queue Drain**: The `stop()` method now implements a graceful drain sequence, allowing the capture loop to safely flush and process pending flows for `idle_timeout + 1s` before terminating the NFStream generator.

### Validation Results
- **Real Wi-Fi Traffic**: Continued to work flawlessly (flows > 0, predictions > 0, no inference errors).
- **Loopback Burst TCP**: Successfully flushed and generated predictions natively.
- **High Rate UDP**: The "98 packets / 0 flows" condition is resolved. Packets are fully ingested without dropping, flows successfully aggregate upon simulation end, and predictions generate instantly without hanging.

Sentinel is now complete and production-ready for live real-time IoT Threat Detection.
