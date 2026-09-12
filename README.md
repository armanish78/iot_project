# 🛡️ Sentinel — AI-Powered IoT Threat Detection System

![Status](https://img.shields.io/badge/Status-Final%20Validation%20Phase-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB)
![Flask](https://img.shields.io/badge/Backend-Flask-black)
![Machine Learning](https://img.shields.io/badge/ML-XGBoost-orange)
![Database](https://img.shields.io/badge/Database-SQLite-blue)

## 📌 1. PROJECT OVERVIEW

**Sentinel** is an end-to-end IoT and network threat detection system. Designed as a final-year academic prototype, it captures real-time network traffic and uses a machine learning pipeline to detect known threats.

In simple terms:
- **Sentinel** acts as a security guard for an IoT network, constantly watching data go by to spot suspicious behavior.
- It solves the problem of IoT devices being insecure by detecting attacks (like a PortScan, where a hacker probes a network to find open doors).
- A **network packet** is a small chunk of data sent over the internet.
- A **flow** is a conversation made up of many packets between a source (like your phone) and a destination (like a smart bulb).
- **NFStream** is a tool that captures these packets and summarizes the flow into statistical features (e.g., how many bytes were sent, the average packet size).
- The **69 features** represent these summarized behavioral statistics.
- **XGBoost** is an advanced AI model that looks at these 69 features and decides whether the flow is **BENIGN** (normal) or a **PORTSCAN** (attack).
- If it's a PortScan, the system generates an alert, saves it to a **SQLite** database, and displays it in real-time on the **React/Vite** dashboard using the **Flask API**.

## 🔄 2. ARCHITECTURE

The current locked data pipeline operates strictly as follows:

```text
Real Network Traffic
        ↓
      Npcap
        ↓
     NFStream
        ↓
69 flow-level features
        ↓
NFStream-native XGBoost model
        ↓
 BENIGN / PORTSCAN
        ↓
   Flask backend
        ↓
      SQLite
        ↓
React/Vite Sentinel Dashboard
```

*Note: The model was trained using NFStream-generated features offline, so the live inference and training environments use the exact same feature-generation pipeline.*

## 🤖 3. PRODUCTION MODEL

The current production machine learning detector is located at:
`backend/models/live_nfstream/`

This directory strictly contains:
- `xgboost_model.pkl` (The finalized XGBoost classifier)
- `scaler.pkl` (The fitted StandardScaler for the 69 features)

## 📊 4. FINAL VALIDATED RESULTS

The model was rigorously validated against unseen datasets.

**PortScan Temporal Test (Offline):**
- **Recall:** 99.60%
- **FPR:** 0.01%
- **Accuracy:** 99.79%

**Benign Regression Test (Live Database Path):**
- **Flows processed:** 5,000 benign flows
- **Alerts generated:** 48
- **FPR:** 0.96%

**Genuine PortScan Validation (Live Database Path):**
- **Alerts generated:** 4,831 Alert rows successfully written to SQLite
- **Attacker IP identified:** `172.16.0.1`
- **Inference errors:** 0

## ⚠️ 5. IMPORTANT HONESTY RULES & LIMITATIONS

- The current production ML detector is specifically trained and validated for **PortScan detection**.
- The broader Sentinel architecture is designed for IoT network traffic monitoring and intrusion detection, but additional attack classes (e.g., DDoS, Web Attacks) require separate training and validation.
- This model is a research prototype. We do **not** claim it detects all cyber attacks, all CIC-IDS2017 attacks, or every IoT threat.
- We do **not** claim 100% detection or zero false positives.
- This is an academic proof-of-concept and does **not** provide production-grade cybersecurity protection against evasive zero-day intrusion techniques.

## 🔌 6. CURRENT API ENDPOINTS

The following API endpoints actively power the dashboard and monitoring system:

**Monitoring & Dashboard:**
- `GET /api/dashboard/stats` - Returns global connection and threat counts.
- `GET /api/dashboard/activity?limit=50` - Returns a timeline of the most recent predictions.
- `GET /api/alerts/` - Returns active threats and alerts.
- `GET /api/predictions/history` - Returns historical predictions.

**Live Control:**
- `GET /api/live/status` - Returns the current status of the capture thread.
- `POST /api/live/start` - Starts the NFStream background thread on a specified interface.
- `POST /api/live/stop` - Safely drains and stops the packet capture thread.

## 🚀 7. RUNNING THE PROJECT

1. **Start Backend:**
   ```bash
   python backend/run.py
   ```
2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
3. **Access Dashboard:** Open `http://localhost:5173`
4. **Live Monitor:** Go to the "Live Monitor" tab, select your physical interface (or Loopback), and click "Start Capture".
