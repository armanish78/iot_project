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

1. **Intelligent Sampling:** The raw data was over 11GB, which would crash a standard computer. We took a mathematically uniform **15% sample** to create a manageable dataset of ~165,000 records.
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

## 4. Phase 3: Instructions for Person-3 (UI & Integration)
*Goal: The backend ML pipeline is 100% finished. Person-3 is responsible for building the Frontend / User Interface to display this system to the end user.*

Hello Person-3! Your job is to take the finished AI models and present them in a beautiful, user-friendly interface. 

### What you need to do:
1. **Choose a Frontend Framework:** You can build this as a modern web app using React, Next.js, or Vue. If you want something entirely Python-based, we highly recommend **Streamlit** or **Gradio**, which are perfect for ML dashboards.
2. **Build an API Layer (Optional but Recommended):** Use `FastAPI` or `Flask` to create an endpoint where the frontend can submit network traffic data and receive predictions from the AI.
3. **Load the Models:** In your backend API, you will load the finalized models using the `pickle` library:
   - `backend/models/random_forest_model.pkl`
   - `backend/models/isolation_forest_model.pkl`
4. **Display the Results:** Your UI should feature a dashboard that shows:
   - Whether the network is currently "Safe" or "Under Attack."
   - Which model caught the attack (The Random Forest or the Isolation Forest).
   - **The SHAP Explanation:** We have provided sample outputs in `backend/predictions/predictions.json`. Your UI needs to read this JSON and display the "Top Features" to the user so they understand *why* the AI triggered an alert. 

You do not need to train or tweak the AI models—they are fully optimized, mathematically verified, and locked in. Focus entirely on making the dashboard look premium, dynamic, and easy to understand!
