# IoT Threat Detection System - Project Walkthrough

Welcome to the project! This document is designed for any team member (regardless of their Machine Learning experience) to quickly understand exactly what this project is, what has been completed in Phases 1 and 2, and what needs to happen next in Phase 3.

---

## 1. Project Overview: What are we building?
We are building a highly advanced Artificial Intelligence system to protect Internet of Things (IoT) devices—like smart doorbells, security cameras, and routers—from being hacked and turned into malicious "botnets" (like the infamous Mirai botnet). 

Instead of looking for specific virus signatures (which can easily be bypassed), our AI analyzes the **mathematical behavior** of the network traffic (like packet sizes, flow duration, and data transfer rates) to instantly detect when a device starts acting maliciously.

---

## 2. Phase 1: Data Preprocessing (Completed)
*Goal: Machine Learning models cannot read raw network logs. We had to clean and format the raw data so the AI could understand it.*

We used two massive, industry-standard cybersecurity datasets (**N-BaIoT** and **UNSW-NB15**). Here is how we processed them:

1. **Intelligent Sampling & Data Volume:** The raw data was originally over 11GB. We took a mathematically uniform **15% sample** to create an initial manageable dataset of **~165,000 records**. After applying SMOTE for class balancing, the total data added for training doubled to over **330,000 perfectly balanced records**.
2. **Data Cleaning:** We removed duplicates, deleted useless string columns (like IP addresses), and intelligently filled in millions of missing values.
3. **Feature Engineering & Scaling:** We extracted 167 specific mathematical features (like average packet size) and squashed all the numbers down to a scale between 0.0 and 1.0 (`MinMaxScaler`) so the AI wouldn't get confused by massive numbers.
4. **Class Balancing (SMOTE):** Our data had way more "normal" traffic than "attack" traffic. If we gave this to the AI, it would become biased. We used an advanced technique called **SMOTE** to synthetically generate realistic attack traffic, perfectly balancing the dataset at 50/50.
5. **Final Output:** The clean data was saved as highly efficient Python `.npy` files in the `data/processed/` folder.

---

## 3. Phase 2: Machine Learning Engine (Completed)
*Goal: Train the AI to accurately identify attacks without "memorizing" the answers.*

We built a **Hybrid AI Pipeline** using two completely different types of models working together:

### A. The "Expert" (Random Forest Model)
* **What it does:** This is a supervised model that was explicitly taught what known attacks look like. 
* **Regularization:** Initially, this model was scoring 99.4% accuracy, which is suspiciously high and risks "overfitting" (memorizing the data). We intentionally "dumbed down" the model by restricting its mathematical depth (Regularization). 
* **Final Result:** It now scores a highly realistic and incredibly robust **95.52% Accuracy**. It catches 99.6% of all attacks (Recall) with a few harmless false alarms.

### B. The "Zero-Day Guard Dog" (Isolation Forest Model)
* **What it does:** This is an *unsupervised* anomaly detector. We never taught it what an attack looks like. We only showed it 100% normal, healthy traffic. It mathematically learned the "boundaries of normal behavior" and flags anything outside those boundaries. It is designed to catch brand new viruses that nobody has ever seen before (Zero-Days).
* **Final Result:** Evaluated on a highly realistic dataset, it achieved **87.0% Accuracy**, which is exceptional for an AI operating completely blind.

### C. Explainable AI (SHAP)
AI is often a "black box," meaning it makes a decision, but humans don't know *why*. We integrated a technology called **SHAP**. When the AI flags an attack, SHAP generates a report explaining exactly *which network features* triggered the alarm (e.g., "Packet size suddenly spiked by 400%").

---

## 4. Phase 3: Flask Backend API (Completed)
*Goal: Build a robust backend to serve the Machine Learning models and handle database operations.*

We have successfully built a full Flask REST API that bridges the gap between our raw Machine Learning models and the frontend interface.

### Key Achievements:
1. **API Endpoints:** Created dedicated endpoints for health checks, live network activity, threat history, and real-time predictions.
2. **Database Layer:** Implemented a SQLite database using SQLAlchemy to store every prediction and track high-severity alerts.
3. **ML Integration:** Built a `threat_detection_service` that loads our saved `.pkl` models and securely evaluates incoming JSON data, returning hybrid predictions instantly.
4. **Services Architecture:** Structured the codebase professionally, decoupling routes from business logic (Logging, Database, Preprocessing).

---

## 5. Phase 4: Instructions for Person-4 (React Dashboard)
*Goal: Build a beautiful Frontend UI to display the AI's real-time threat detection to the end-user.*

 The ML models and Flask backend are 100% finished. Your job is purely frontend. 

**Your Quick-Start Checklist:**
1. **Framework:** Spin up a new React or Next.js application. 
2. **Connect:** Fetch data from our local API at `http://localhost:5000` (Key routes: `/api/dashboard/stats`, `/api/dashboard/activity`, and `/api/alerts/`).
3. **Visualize:** Build a premium dashboard that clearly displays the network status ("Safe" vs. "Under Attack") and shows the user exactly *why* an alert triggered using the provided SHAP explanations.

Focus entirely on UX/UI design—make it look dynamic, modern, and easy to read!
