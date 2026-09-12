# Final Model Decision & Architecture

## Statement of Purpose
Sentinel currently provides real-time binary PortScan intrusion detection using an XGBoost model trained on NFStream-generated CIC-IDS2017-compatible flow features.

## Architecture
The final, locked ML architecture is as follows:
- **Packet Capture:** Live packets are captured from the network interface using `NFStreamer` configured with `statistical_analysis=True` and `accounting_mode=1`.
- **Feature Extraction:** Flows are extracted natively via NFStream. As flows expire, `LiveFlowExtractor` extracts a strict 69-feature schema matching the CIC-IDS2017 feature set (e.g., Forward/Backward Packet lengths, IAT statistics, Flags).
- **Preprocessing:** Features are scaled using `StandardScaler` (saved in `scaler.pkl`).
- **Inference Engine:** Scaled features are fed into an XGBoost binary classifier (saved in `xgboost_model.pkl`), utilizing standard `sklearn.preprocessing.LabelEncoder` for seamless pickling and loading.
- **Alert Generation:** If a flow is classified as a PortScan (Attack), the `LiveInferenceService` generates an alert and securely saves both the prediction and the Sentinel alert in the live SQLite database.

## Training Methodology
- **Data Source:** CIC-IDS2017 Friday Working Hours PCAP (Morning: Benign, Afternoon: PortScan).
- **Temporal Split:** The PCAPs were strictly split temporally.
  - Training: 09:00 - 11:00 (Benign) + 13:55 - 14:55 (PortScan)
  - Testing (Holdout): 11:00 - 12:00 (Benign) + 14:55 - 15:29 (PortScan)
- **Label Cleaning:** The PortScan window (13:55-15:29) contained heavy background benign traffic which was initially polluting the dataset. Labels were strictly scrubbed by assigning Attack (`1`) *only* to flows containing the known CIC-IDS2017 attacker IP (`172.16.0.1`). All background traffic was safely labeled Benign (`0`).

## Validation Results
On the completely unseen temporal test set:
- **Accuracy:** 0.9979
- **Recall (PortScan Detection):** 0.9960 (Target: > 0.9000)
- **FPR (False Positive Rate):** 0.0001 (Target: < 0.0100)

### Genuine PortScan PCAP Validation
When replaying the untouched `portscan_test.pcap` directly into the live Sentinel database inference loop (bypassing synthetic scapy tests), the system correctly generated 4,831 SQL Alert rows identifying PortScan attacks involving the attacker IP `172.16.0.1` with ~1.0 confidence, triggering no inference errors.

### Benign Regression Test
When processing 5,000 flows from the `benign_test.pcap` directly through the database path, the system generated exactly 48 alerts, yielding a False Positive Rate of **0.96%**. These alerts are genuine statistical misclassifications by the ML model, well below the target 1% ceiling constraint, proving that the model successfully discriminates PortScans without blanket-flagging background traffic.

## Known Limitations
- The current production detector is specifically validated for **PortScan** attacks only. It is **not** validated for all CIC-IDS2017 attack classes (e.g., DDoS, Web Attacks, Brute Force).
- The system focuses on binary classification (Benign vs. PortScan).
- This model is a research/demonstration proof-of-concept and we do **not** claim 100% detection, zero false positives, or production-grade cybersecurity protection against evasive zero-day intrusion techniques.
